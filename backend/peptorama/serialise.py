def serialise(raw: dict) -> dict:
    """Make the process_input() output JSON-safe."""
    return {
        "schema": 1,
        "peptides": raw["peptides"],
        "edges": raw.get("edges", []),
        "monomers": dict(sorted(raw["monomers"].items())),
        "warnings": raw["warnings"].to_list(),
        "metadata": {
            **raw["metadata"],
        },
    }