from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .processing.validate import process_input, CONFIG
from .processing.network import build_network

from .schemas import PeptideInput, SubmitRequest
from .serialise import serialise
from pathlib import Path

import re
import os

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# -- Routes --
@app.get("/api/config")
def get_config():
    return CONFIG


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
