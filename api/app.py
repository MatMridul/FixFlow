"""FastAPI application factory and server configuration for FixFlow."""
from typing import Callable, Optional

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from cache import CacheStore, CompositionalCache, GatedSemanticCache, SemanticCache
from extraction import StructureExtractor
from extraction.llm_client import LLMChain


def create_app(
    cache: Optional[SemanticCache] = None,
    extractor: Optional[StructureExtractor] = None,
    resolver_fn: Optional[Callable] = None,
) -> FastAPI:
    """Create and configure FixFlow FastAPI application instance."""
    app = FastAPI(
        title="FixFlow — Smart Guided Troubleshooting Engine",
        description="Samsung PRISM GenAI Hackathon (Theme 02) Troubleshooting Service",
        version="1.0.0",
    )

    # Enable CORS for local web interface / frontend dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize service components on app state (Defaults to N1 Compositional Cache)
    app.state.cache = cache or CompositionalCache(store=CacheStore())
    if extractor is None:
        # Gemini -> Mistral chain when GEMINI_API_KEY / MISTRAL_API_KEY are set
        # (env or .env); None -> deterministic extraction only.
        extractor = StructureExtractor(llm_callable=LLMChain.from_env())
    app.state.extractor = extractor
    if resolver_fn is None:
        # Import failure here must be loud, not silently disable deeplinks.
        from resolution import resolve_goal_deeplinks_with_stats
        resolver_fn = resolve_goal_deeplinks_with_stats
    app.state.resolver_fn = resolver_fn


    # Register routers
    app.include_router(router)

    # Demo UI (plain HTML/JS, no build step) served from the same process so
    # there is one thing to keep running during judging.
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="app")

        @app.get("/", include_in_schema=False)
        def _root() -> RedirectResponse:
            return RedirectResponse(url="/app/")

    return app


# Default singleton app instance
app = create_app()
