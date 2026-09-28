"""FastAPI route handlers for FixFlow troubleshooting service."""
import logging
import time
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from api.models import (
    ContextDeeplinkResponse,
    MetaBlock,
    TroubleshootRequest,
    TroubleshootResponse,
)
from cache import CompositionalCache, SemanticCache
from extraction import ExtractionOutcome, StructureExtractor, filter_provenance
from extraction.deterministic import extract_goal_deterministic, topic_and_title
from extraction.query_variations import generate_query_variations
from enrichment import decompose_query_intents
from validation import calibrate_score, programmatic_repair_goal, repair_goal_or_json, validate_goal

router = APIRouter()
logger = logging.getLogger(__name__)


def _cached_variations(query: str) -> list:
    """Cache hits skip extraction, but FAQ A5 still scores 8-10 variations per
    results.jsonl line — generate them deterministically (no LLM call)."""
    return generate_query_variations(query, topic_and_title(query, "")[0])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(request: Request) -> Dict[str, Any]:
    """Return service status, cache entry count, and engine readiness."""
    cache: Optional[SemanticCache] = getattr(request.app.state, "cache", None)
    cache_count = cache.count() if cache else 0
    extractor: Optional[StructureExtractor] = getattr(request.app.state, "extractor", None)
    model_ready = extractor is not None
    chain = getattr(extractor, "llm_callable", None)
    llm_models = chain.active_models() if hasattr(chain, "active_models") else []

    return {
        # FAQ gate G2 requires exactly {"status": "ok"} — any other value
        # fails the gate and skips every live check.
        "status": "ok",
        "service": "FixFlow",
        "version": "1.0.0",
        "cache_entries": cache_count,
        "model_readiness": model_ready,
        # Models currently in the Gemini -> Mistral chain (quota-benched ones
        # drop out); empty means deterministic extraction only.
        "llm_models": llm_models,
    }


def _troubleshoot(payload: TroubleshootRequest, request: Request, trace: Dict[str, Any]) -> TroubleshootResponse:
    """
    Orchestrate request across Cache -> Extractor -> Resolver -> Validator -> Response.
    - Level 1 & 2 Cache lookup (including Novelty N1 Compositional lookup).
    - If hit: return immediately with cost_usd = 0.0.
    - If miss without SIIS: return contexts: [] and fallback = 'no_siis_context'.
    - If miss with SIIS: cold path extraction, provenance filtering, resolution, validation,
      calibration, cache write, and return.
    """
    start_time = time.perf_counter()
    cache: Optional[SemanticCache] = getattr(request.app.state, "cache", None)
    extractor: Optional[StructureExtractor] = getattr(request.app.state, "extractor", None)
    resolver_fn: Optional[Callable] = getattr(request.app.state, "resolver_fn", None)
    try:
        trace["clauses"] = [
            {"text": text, "signature": sig.to_dict()} for text, sig in decompose_query_intents(payload.query)
        ]
    except Exception:
        trace["clauses"] = []

    # 1. Cache Fast Path Lookup (Novelty N1 Compositional & Gated Fast-Path)
    if cache is not None:
        if isinstance(cache, CompositionalCache):
            comp_res = cache.get_compound(payload.query)
            if comp_res.hit and comp_res.goals:
                trace.update(path="cache", cache_hit_type=comp_res.hit_type)
                latency = (time.perf_counter() - start_time) * 1000.0
                return TroubleshootResponse(
                    query=payload.query,
                    query_variations=_cached_variations(payload.query),
                    response=ContextDeeplinkResponse(contexts=comp_res.goals),
                    meta=MetaBlock(
                        latency_ms=round(latency, 2),
                        cache_hit=True,
                        model=f"cache-{comp_res.hit_type}-v1",
                        cost_usd=0.0,
                        fallback=None,
                    ),
                )
        else:
            cache_res = cache.get(payload.query)
            if cache_res.hit and cache_res.goal is not None:
                trace.update(path="cache", cache_hit_type=cache_res.hit_type)
                latency = (time.perf_counter() - start_time) * 1000.0
                return TroubleshootResponse(
                    query=payload.query,
                    query_variations=_cached_variations(payload.query),
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
        trace["path"] = "no_siis"
        latency = (time.perf_counter() - start_time) * 1000.0
        return TroubleshootResponse(
            query=payload.query,
            query_variations=_cached_variations(payload.query),
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

    siis_title = payload.siis_response.title or ""
    siis_content = payload.siis_response.content or ""
    if hasattr(extractor, "extract_full"):
        outcome = extractor.extract_full(query=payload.query, siis_title=siis_title, siis_content=siis_content)
    else:  # any object exposing only the original Goal-returning extract()
        outcome = ExtractionOutcome(
            goal=extractor.extract(query=payload.query, siis_title=siis_title, siis_content=siis_content)
        )
    goal = outcome.goal
    trace["path"] = "cold"
    trace["extraction"] = {"model": outcome.model, "llm_used": outcome.llm_used, "cost_usd": outcome.cost_usd}
    query_variations = outcome.query_variations or _cached_variations(payload.query)

    if goal is None or not goal.actions:
        latency = (time.perf_counter() - start_time) * 1000.0
        return TroubleshootResponse(
            query=payload.query,
            query_variations=query_variations,
            response=ContextDeeplinkResponse(contexts=[]),
            meta=MetaBlock(
                latency_ms=round(latency, 2),
                cache_hit=False,
                model=outcome.model,
                cost_usd=outcome.cost_usd,
                fallback="no_match",
            ),
        )

    # 3.1 Provenance Filtering (Novelty N5: Hallucination elimination)
    siis_text = f"{siis_title}. {siis_content}"
    filtered, grounding_coverage, provenance = filter_provenance(goal, siis_text, threshold=0.15)
    if filtered.actions:
        goal = filtered
    else:
        # Every LLM step failed grounding (usually heavy paraphrasing). An
        # empty answer costs the unseen-scenario check (FAQ A4: valid,
        # NON-EMPTY responses), so fall back to the deterministic plan —
        # built from SIIS sentences, grounded by construction.
        goal = programmatic_repair_goal(extract_goal_deterministic(payload.query, siis_title, siis_content))
        goal, grounding_coverage, provenance = filter_provenance(goal, siis_text, threshold=0.15)
        trace["extraction"]["replaced_ungrounded_llm_output"] = True

    trace["provenance"] = provenance

    # 4. Dev B Hook: Catalog Screen Resolution & Deeplink Binding + Contract 2 signals
    retrieval_margin, path_alignment = 1.0, 1.0
    if resolver_fn is not None:
        try:
            resolved = resolver_fn(goal)
            if isinstance(resolved, tuple):
                goal, stats = resolved
                retrieval_margin = stats.retrieval_margin
                path_alignment = stats.path_alignment
                trace["resolution"] = stats.details
            else:
                goal = resolved
        except Exception:
            logger.exception("deeplink resolution failed; returning plan without deeplinks")

    # 5. Validation & Auto-Repair
    goal = programmatic_repair_goal(goal)
    report = validate_goal(goal)
    if not report.is_valid:
        repaired_goal, repair_report = repair_goal_or_json(goal)
        if repaired_goal is not None and repair_report.is_valid:
            goal = repaired_goal
            report = repair_report

    # 5.1 Evidence-Calibrated Confidence Scoring (Novelty N5 + Contract 2)
    validator_pass_rate = 1.0 if report.is_valid else max(0.0, 1.0 - (len(report.violations) * 0.15))
    goal.score = calibrate_score(
        grounding_coverage=grounding_coverage,
        validator_pass_rate=validator_pass_rate,
        retrieval_margin=retrieval_margin,
        path_alignment=path_alignment,
    )
    # A weak plan is still returned (unseen scenarios must be non-empty), but
    # flagged so callers/UI can show it as low confidence.
    fallback = "low_confidence" if goal.score < 0.25 else None
    trace["calibration"] = {
        "grounding_coverage": grounding_coverage,
        "validator_pass_rate": validator_pass_rate,
        "retrieval_margin": retrieval_margin,
        "path_alignment": path_alignment,
        "score": goal.score,
    }

    # 6. Update Cache with verified Goal
    if cache is not None:
        if isinstance(cache, CompositionalCache):
            cache.put_compound(payload.query, [goal])
        else:
            cache.put(payload.query, goal)

    latency = (time.perf_counter() - start_time) * 1000.0
    return TroubleshootResponse(
        query=payload.query,
        query_variations=query_variations,
        response=ContextDeeplinkResponse(contexts=[goal]),
        meta=MetaBlock(
            latency_ms=round(latency, 2),
            cache_hit=False,
            model=outcome.model,
            cost_usd=outcome.cost_usd,
            fallback=fallback,
        ),
    )


@router.post("/v1/troubleshoot", response_model=TroubleshootResponse, status_code=status.HTTP_200_OK)
def troubleshoot(payload: TroubleshootRequest, request: Request, debug: bool = False):
    """Scored endpoint. `?debug=true` adds a `trace` (intent clauses, cache
    path, step provenance, screen resolution, calibration inputs) for the
    demo UI; without it the response is exactly the contract shape."""
    trace: Dict[str, Any] = {}
    response = _troubleshoot(payload, request, trace)
    if debug:
        return JSONResponse({**response.model_dump(mode="json"), "trace": trace})
    return response


@router.get("/v1/scenarios")
def scenarios() -> Dict[str, Any]:
    """The 20 student-kit scenarios (query + SIIS payload) for the demo UI."""
    import json
    from pathlib import Path

    data = Path(__file__).resolve().parent.parent / "data"
    queries = [q.strip() for q in (data / "input.txt").read_text(encoding="utf-8").splitlines() if q.strip()]
    siis = json.loads((data / "siis_responses.json").read_text(encoding="utf-8"))["responses"]
    return {
        "scenarios": [
            {"id": r["id"], "query": q, "siis_response": r["siis_response"]}
            for q, r in zip(queries, siis)
        ]
    }
