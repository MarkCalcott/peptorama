from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from peptorama.processing.validate import process_input
from peptorama.processing.network import build_network

from peptorama.schemas import PeptideInput, SubmitRequest
from peptorama.serialise import serialise
from pathlib import Path
from starlette.exceptions import HTTPException

import re
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist_test"

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# -- Routes --


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/preprocess")
def process_text(body: PeptideInput):
    """Accept raw pasted text."""
    result = process_input(body.known, body.predicted, body.monomers)
    return serialise(result)


@app.post("/api/submit")
def submit_job(request: SubmitRequest):
    """Accept job configuration. Currently echoes input for testing."""
    result = process_input(
        request.input.known, request.input.predicted, request.input.monomers
    )
    result["edges"] = build_network(result, request.config)
    serialised_with_config = serialise(result)
    serialised_with_config["settings"] = request.config.model_dump(by_alias=True)
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
