from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from peptorama.processing.validate import process_input
from peptorama.processing.network import build_network

from peptorama.schemas import PeptideInput, SubmitRequest
from peptorama.serialise import serialise
from pathlib import Path
from starlette.exceptions import HTTPException

import logging
import time
from uuid import uuid4
from peptorama.logging_config import setup_logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

setup_logging() 
logger = logging.getLogger("peptorama")

app = FastAPI()

# Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path in ("/health",) or request.url.path.startswith("/static"):
        return await call_next(request)

    request_id = uuid4().hex[:8]
    request.state.request_id = request_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled error", extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        })
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    logger.info("request", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        "client_ip": get_remote_address(request),
    })
    response.headers["X-Request-ID"] = request_id
    return response


# Error messages
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": err["loc"][-1],
            "message": err["msg"].removeprefix("Value error, "),
        }
        for err in exc.errors()
    ]
    logger.info("validation failed", extra={
        "path": request.url.path,
        "fields": [e["field"] for e in errors],
        "messages": [e["message"] for e in errors],
    })
    return JSONResponse(
        status_code=422,
        content={
            "detail": "; ".join(e["message"] for e in errors),
            "errors": errors,
        },
    )

# -- Rate limiting --

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning("rate limited", extra={
        "path": request.url.path,
        "client_ip": get_remote_address(request),
    })
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a minute and try again."},
        headers={"Retry-After": "60"},
    )

# -- CORS --
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://peptorama.netlify.app",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# -- Routes --
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/preprocess")
@limiter.limit("10/minute")
def process_text(request: Request, body: PeptideInput):
    """Accept raw pasted text."""
    result = process_input(body.known, body.predicted, body.monomers)
    return serialise(result)


@app.post("/api/submit")
@limiter.limit("5/minute")
def submit_job(request: Request, body: SubmitRequest):
    """Accept job configuration. Currently echoes input for testing."""
    t0 = time.perf_counter()
    result = process_input(
        body.input.known, body.input.predicted, body.input.monomers
    )
    t1 = time.perf_counter()
    result["edges"] = build_network(result, body.config)
    t2 = time.perf_counter()
    logger.info("job completed", extra={
        "request_id": request.state.request_id,
        "known_input_chars": len(body.input.known),
        "known_predicted_chars": len(body.input.predicted),
        "n_edges": len(result["edges"]),
        "config": body.config.model_dump(by_alias=True),
        "preprocess_ms": round((t1 - t0) * 1000, 1),
        "network_ms": round((t2 - t1) * 1000, 1),
    })
    serialised_with_config = serialise(result)
    serialised_with_config["settings"] = body.config.model_dump(by_alias=True)
    return {"success": True, "result": serialised_with_config}


@app.get("/network")
def network_page():
    return FileResponse("static/network.html")


class SPAStaticFiles(StaticFiles):
    """Serve the React build, falling back to index.html for client-side routes."""

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404 and not path.startswith("api"):
                return await super().get_response("index.html", scope)
            raise


if FRONTEND_DIST.is_dir():
    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
