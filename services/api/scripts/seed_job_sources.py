"""Seed job_sources table from YAML/CSV or the deprecated static registry."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

# Ensure `src` imports resolve when running this script directly.
API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from src.domain.jobs.repository import JobSourceRepository
from src.infrastructure.db.session import SessionLocal


def _iter_yaml_rows(file_path: Path) -> list[dict]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError("PyYAML is required for YAML imports. Install with: pip install pyyaml") from exc

    payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if "job_sources" in payload and isinstance(payload["job_sources"], list):
            return payload["job_sources"]
        rows: list[dict] = []
        for source, source_map in payload.items():
            if not isinstance(source_map, dict):
                continue
            for company_key, config in source_map.items():
                if not isinstance(config, dict):
                    continue
                rows.append(
                    {
                        "source": source,
                        "company_key": company_key,
                        "board_token": config.get("board_token"),
                        "display_name": config.get("display_name", company_key),
                        "is_active": config.get("is_active", True),
                    }
                )
        return rows
    if isinstance(payload, list):
        return payload
    raise ValueError("Unsupported YAML structure. Expected list or mapping.")


def _iter_csv_rows(file_path: Path) -> list[dict]:
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "source": row.get("source"),
                    "company_key": row.get("company_key"),
                    "board_token": row.get("board_token"),
                    "display_name": row.get("display_name") or row.get("company_key"),
                    "is_active": str(row.get("is_active", "true")).lower() not in {"false", "0", "no"},
                }
            )
        return rows


def _iter_registry_rows() -> list[dict]:
    from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY

    rows = []
    for source, source_map in JOB_SOURCE_REGISTRY.items():
        for company_key, config in source_map.items():
            rows.append(
                {
                    "source": source,
                    "company_key": company_key,
                    "board_token": config.get("board_token"),
                    "display_name": config.get("display_name", company_key),
                    "is_active": True,
                }
            )
    return rows


def _load_rows(source_file: str | None) -> list[dict]:
    if not source_file:
        return _iter_registry_rows()

    file_path = Path(source_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _iter_yaml_rows(file_path)
    if suffix == ".csv":
        return _iter_csv_rows(file_path)

    raise ValueError("Unsupported source file type. Use .yaml/.yml or .csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed job_sources table")
    parser.add_argument(
        "--source-file",
        default=None,
        help="Optional YAML/CSV source. If omitted, seeds from deprecated source_registry.",
    )
    args = parser.parse_args()

    rows = _load_rows(args.source_file)

    db = SessionLocal()
    try:
        repository = JobSourceRepository(db)
        upserted = 0
        for row in rows:
            source = (row.get("source") or "").strip()
            company_key = (row.get("company_key") or "").strip().lower()
            board_token = (row.get("board_token") or "").strip()
            display_name = (row.get("display_name") or company_key).strip()
            is_active = bool(row.get("is_active", True))

            if not source or not company_key or not board_token:
                continue

            repository.upsert(
                source=source,
                company_key=company_key,
                board_token=board_token,
                display_name=display_name,
                is_active=is_active,
            )
            upserted += 1

        print("PASS seed job sources")
        print(f"upserted={upserted}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
