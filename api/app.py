"""FastAPI application factory and server configuration for FixFlow."""
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from cache import CacheStore, GatedSemanticCache, SemanticCache
from extraction import StructureExtractor


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

    # Initialize service components on app state (Defaults to N2 Gated Semantic Cache)
    app.state.cache = cache or GatedSemanticCache(store=CacheStore())
    app.state.extractor = extractor or StructureExtractor()
    app.state.resolver_fn = resolver_fn


    # Register routers
    app.include_router(router)

    return app


# Default singleton app instance
app = create_app()
