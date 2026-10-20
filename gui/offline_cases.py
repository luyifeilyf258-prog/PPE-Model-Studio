"""Locate and validate the bundled, read-only offline case library."""

import json
import os
from pathlib import Path


def offline_cases_root() -> Path:
    bundle_dir = Path(os.environ.get("PPE_BUNDLE_DIR") or Path(__file__).resolve().parents[1])
    return bundle_dir / "offline_cases"


def load_offline_cases() -> list[dict]:
    root = offline_cases_root()
    records = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if not isinstance(records, list) or [item.get("number") for item in records] != list(range(1, 28)):
        raise ValueError("The offline case catalog must contain cases 1 through 27 in order.")
    for item in records:
        case_dir = root / f"{item['number']:02d}"
        for relative in (
            "config/case_used.yaml",
            "json/case_preview.json",
            "preview/case_preview.png",
            "results/discharge_voltage.csv",
        ):
            if not (case_dir / relative).is_file():
                raise FileNotFoundError(case_dir / relative)
        item["directory"] = case_dir
    return records
