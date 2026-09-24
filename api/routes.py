"""FastAPI route handlers for FixFlow troubleshooting service."""
import time
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Request, status

from api.models import (
    ContextDeeplinkResponse,
    MetaBlock,
    TroubleshootRequest,
    TroubleshootResponse,
)
from cache import SemanticCache
from extraction import StructureExtractor
from validation import repair_goal_or_json, validate_goal

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(request: Request) -> Dict[str, Any]:
    """Return service status, cache entry count, and engine readiness."""
    cache: Optional[SemanticCache] = getattr(request.app.state, "cache", None)
    cache_count = cache.count() if cache else 0
    extractor: Optional[StructureExtractor] = getattr(request.app.state, "extractor", None)
    model_ready = extractor is not None

    return {
        "status": "healthy",
        "service": "FixFlow",
        "version": "1.0.0",
        "cache_entries": cache_count,
        "model_readiness": model_ready,
    }


@router.post("/v1/troubleshoot", response_model=TroubleshootResponse, status_code=status.HTTP_200_OK)
def troubleshoot(payload: TroubleshootRequest, request: Request) -> TroubleshootResponse:
    """
    Orchestrate request across Cache -> Extractor -> Resolver -> Validator -> Response.
    - Level 1 & 2 Cache lookup.
    - If hit: return immediately with cost_usd = 0.0.
    - If miss without SIIS: return contexts: [] and fallback = 'no_siis_context'.
    - If miss with SIIS: cold path extraction, validation, repair, cache write, and return.
    """
    start_time = time.perf_counter()
    cache: Optional[SemanticCache] = getattr(request.app.state, "cache", None)
    extractor: Optional[StructureExtractor] = getattr(request.app.state, "extractor", None)
    resolver_fn: Optional[Callable] = getattr(request.app.state, "resolver_fn", None)

    # 1. Cache Fast Path Lookup
    if cache is not None:
        cache_res = cache.get(payload.query)
        if cache_res.hit and cache_res.goal is not None:
            latency = (time.perf_counter() - start_time) * 1000.0
            return TroubleshootResponse(
                query=payload.query,
                response=ContextDeeplinkResponse(contexts=[cache_res.goal]),
                meta=MetaBlock(
                    latency_ms=round(latency, 2),
                    cache_hit=True,
                    model=f"cache-{cache_res.hit_type}-v1",
                    cost_usd=0.0,
                    fallback=None,
                ),
            )

    # 2. Cache Miss: Check SIIS availability
    if payload.siis_response is None:
        latency = (time.perf_counter() - start_time) * 1000.0
        return TroubleshootResponse(
            query=payload.query,
            response=ContextDeeplinkResponse(contexts=[]),
            meta=MetaBlock(
                latency_ms=round(latency, 2),
                cache_hit=False,
                model="fixflow-cache-miss",
                cost_usd=0.0,
                fallback="no_siis_context",
            ),
        )

    # 3. Cold Path: Extract intermediate Goal from SIIS documentation
    if extractor is None:
        extractor = StructureExtractor()

    goal = extractor.extract(
        query=payload.query,
        siis_title=payload.siis_response.title,
        siis_content=payload.siis_response.content,
    )

    if goal is None:
        latency = (time.perf_counter() - start_time) * 1000.0
        return TroubleshootResponse(
            query=payload.query,
            response=ContextDeeplinkResponse(contexts=[]),
            meta=MetaBlock(
                latency_ms=round(latency, 2),
                cache_hit=False,
                model="fixflow-extractor",
                cost_usd=0.001,
                fallback="no_match",
            ),
        )

    # 4. Dev B Hook: Catalog Screen Resolution & Deeplink Binding (if registered)
    if resolver_fn is not None:
        try:
            goal = resolver_fn(goal)
        except Exception:
            pass

    # 5. Validation & Auto-Repair
    report = validate_goal(goal)
    if not report.is_valid:
        repaired_goal, repair_report = repair_goal_or_json(goal)
        if repaired_goal is not None and repair_report.is_valid:
            goal = repaired_goal

    # 6. Update Cache with verified Goal
    if cache is not None:
        cache.put(payload.query, goal)

    latency = (time.perf_counter() - start_time) * 1000.0
    return TroubleshootResponse(
        query=payload.query,
        response=ContextDeeplinkResponse(contexts=[goal]),
        meta=MetaBlock(
            latency_ms=round(latency, 2),
            cache_hit=False,
            model="fixflow-pipeline-v1",
            cost_usd=0.001,
            fallback=None,
        ),
    )
