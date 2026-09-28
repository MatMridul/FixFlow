"""FastAPI application factory and server configuration for FixFlow."""
from typing import Callable, Optional

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

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

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request, exc):
        if exc.status_code == 404:
            if "text/html" in request.headers.get("accept", ""):
                return HTMLResponse(
                    content="""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>404 — Page Not Found | FixFlow</title>
  <meta name="description" content="FixFlow custom 404 recovery page.">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231a1d24'/%3E%3Cpath d='M8 10h16M8 16h10M8 22h14' stroke='%23ffffff' stroke-width='2.5' stroke-linecap='round'/%3E%3C/svg%3E">
  <style>
    body { font-family: -apple-system, system-ui, sans-serif; background: #eef1f5; color: #1a1d24; display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 1.5rem; text-align: center; }
    .card { background: #fff; padding: 2.5rem; border-radius: 12px; border: 1px solid #d6dbe3; max-width: 28rem; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    h1 { font-size: 3rem; margin: 0 0 0.5rem; font-weight: 800; color: #1a1d24; }
    h2 { font-size: 1.25rem; margin: 0 0 0.75rem; color: #2553e0; }
    p { color: #5b6472; margin: 0 0 1.5rem; line-height: 1.6; }
    a { display: inline-block; background: #1a1d24; color: #fff; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-weight: 600; }
    a:hover { background: #000; }
  </style>
</head>
<body>
  <div class="card">
    <h1>404</h1>
    <h2>Troubleshooting Path Not Found</h2>
    <p>The screen or diagnostics resource you requested does not exist or has moved.</p>
    <a href="/app/">Return to FixFlow Engine</a>
  </div>
</body>
</html>""",
                    status_code=404,
                )
            return JSONResponse(status_code=404, content={"detail": exc.detail or "Not Found"})
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return app


# Default singleton app instance
app = create_app()
