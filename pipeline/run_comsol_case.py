from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Callable

from scripts.export_java import export_java_from_config, create_default_run_dir_for_config
from config.config_loader import load_case_config
from core.geometry_quality import GeometryQualityError
from comsol_runner.runner import (
    ComsolRunner,
    ComsolRunCancelled,
    ComsolRunError,
    csv_has_data,
    extract_comsol_version,
    read_comsol_log,
)


def _is_legacy_output_java_path(output_java_path: Path) -> bool:
    return (
        output_java_path.parent.name.lower() == "java"
        and output_java_path.parent.parent.name.lower() == "output"
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _save_config_snapshot(config_path: Path, run_dir: Path) -> Path:
    snapshot_path = run_dir / "config" / "case_used.yaml"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, snapshot_path)
    return snapshot_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_model_summary(config_path: Path, json_path: str | Path | None) -> dict[str, Any]:
    cfg = load_case_config(case_yaml_path=config_path, defaults_yaml_path=None)
    summary: dict[str, Any] = {
        "case_name": cfg.get("project", {}).get("case_name"),
        "random_seed": cfg.get("project", {}).get("random_seed"),
        "mesh_hauto": cfg.get("advanced_settings", {}).get("mesh_hauto"),
        "time_step": cfg.get("advanced_settings", {}).get("time_step"),
    }
    if json_path and Path(json_path).is_file():
        model = json.loads(Path(json_path).read_text(encoding="utf-8"))
        summary.update({
            "negative_particle_count": len(model.get("negative_particles", [])),
            "positive_particle_count": len(model.get("positive_particles", [])),
            "negative_binder_count": len(model.get("negative_binders", [])),
            "positive_binder_count": len(model.get("positive_binders", [])),
        })
    return summary


def run_comsol_case_from_config(
    *,
    config_path: str | Path,
    output_java_path: str | Path,
    comsolcompile_path: str | Path,
    comsolbatch_path: str | Path,
    log_path: str | Path,
    output_mph_path: str | Path | None = None,
    runner: ComsolRunner | None = None,
    should_stop: Callable[[], bool] | None = None,
    run_study: bool = True,
    export_results: bool = True,
    run_dir: str | Path | None = None,
) -> dict:
    config_path = Path(config_path).resolve()
    output_java_path = Path(output_java_path)
    log_path = Path(log_path)

    if run_dir is not None:
        run_dir = Path(run_dir).resolve()
    elif _is_legacy_output_java_path(output_java_path):
        run_dir = create_default_run_dir_for_config(config_path).resolve()
        output_java_path = run_dir / "java" / output_java_path.name
        log_path = run_dir / "logs" / log_path.name
        if output_mph_path is not None:
            output_mph_path = run_dir / "mph" / Path(output_mph_path).name
    else:
        run_dir = output_java_path.parent.parent.resolve()

    for sub_dir in ("config", "json", "preview", "java", "logs", "mph", "results", "diagnostics"):
        (run_dir / sub_dir).mkdir(parents=True, exist_ok=True)

    config_snapshot_path = _save_config_snapshot(config_path, run_dir)
    manifest_path = run_dir / "logs" / "run_manifest.json"
    manifest: dict[str, Any] = {
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "run_study": run_study,
        "export_results": export_results,
        "source_config_path": str(config_path),
        "config_snapshot_path": str(config_snapshot_path),
        "requested_java_path": str(output_java_path.resolve()),
        "requested_mph_path": str(Path(output_mph_path).resolve()) if output_mph_path else None,
        "actual_mph_path": None,
        "log_path": str(log_path.resolve()),
        "csv_path": None,
        "java_sha256": None,
        "comsol_version": None,
        "model_summary": None,
        "error": None,
    }
    _write_manifest(manifest_path, manifest)

    def check_stopped() -> None:
        if should_stop is not None and should_stop():
            raise ComsolRunCancelled("COMSOL 计算已被用户停止。")

    try:
        check_stopped()
        export_result = export_java_from_config(
            config_path=config_path,
            output_java_path=output_java_path,
            export_json=True,
            export_preview=True,
            run_study=run_study,
            export_results=export_results,
            run_dir=run_dir,
        )
        check_stopped()

        geometry_quality_path = Path(export_result["geometry_quality_report_path"])
        geometry_quality_report = json.loads(geometry_quality_path.read_text(encoding="utf-8"))
        manifest["geometry_quality_report_path"] = str(geometry_quality_path)
        manifest["geometry_quality_status"] = geometry_quality_report["status"]
        manifest["geometry_quality_summary"] = geometry_quality_report["summary"]
        _write_manifest(manifest_path, manifest)
        if run_study and geometry_quality_report["is_blocking"]:
            raise GeometryQualityError(geometry_quality_report)

        java_path = Path(export_result["java_path"]).resolve()
        manifest.update({
            "java_sha256": _sha256(java_path),
            "model_summary": _build_model_summary(config_path, export_result.get("json_path")),
        })
        _write_manifest(manifest_path, manifest)
        if runner is None:
            runner = ComsolRunner(
                comsolcompile_path=comsolcompile_path,
                comsolbatch_path=comsolbatch_path,
                work_dir=java_path.parent,
            )
        else:
            runner.work_dir = java_path.parent

        class_path = runner.compile_java(java_path)
        check_stopped()

        # A reused run directory must not let an old log or CSV masquerade as
        # output from the current COMSOL process.
        log_path.resolve().write_text("", encoding="utf-8")
        expected_csv = run_dir / "results" / "discharge_voltage.csv" if export_results else None
        csv_before = None
        if expected_csv is not None and expected_csv.is_file():
            csv_before = (expected_csv.stat().st_mtime_ns, expected_csv.stat().st_size)

        batch_result = runner.run_class(
            class_path,
            log_path=log_path,
            output_mph_path=output_mph_path,
        )

        csv_path = None
        if export_results:
            csv_path = expected_csv
            csv_after = (
                (csv_path.stat().st_mtime_ns, csv_path.stat().st_size)
                if csv_path is not None and csv_path.is_file()
                else None
            )
            if csv_after == csv_before or not csv_has_data(csv_path):
                raise ComsolRunError(
                    f"COMSOL batch 未生成有效的放电结果 CSV：{csv_path}",
                    output_mph_path=batch_result.output_mph_path,
                    log_path=batch_result.log_path,
                )

        actual_mph = batch_result.output_mph_path
        removed_mph_path = None
        # COMSOL needs an output MPH while running, but it is very large and is
        # not needed once this run has produced a verified voltage CSV.  Keep
        # MPH files on failed/cancelled runs for diagnosis; clean up only a
        # successful full calculation.
        if run_study and export_results and csv_path is not None and actual_mph is not None:
            actual_mph = Path(actual_mph)
            try:
                actual_mph.unlink()
                removed_mph_path = actual_mph
                actual_mph = None
            except OSError:
                # Do not reclassify a valid completed calculation as failed
                # solely because another process has temporarily locked MPH.
                pass
        manifest.update({
            "status": "solved" if run_study else "model_built",
            "finished_at": _now_iso(),
            "actual_mph_path": str(actual_mph) if actual_mph else None,
            "removed_mph_path": str(removed_mph_path) if removed_mph_path else None,
            "csv_path": str(csv_path) if csv_path else None,
            "comsol_version": extract_comsol_version(read_comsol_log(log_path)),
        })
        _write_manifest(manifest_path, manifest)

        return {
            **export_result,
            "class_path": str(class_path),
            "log_path": str(batch_result.log_path or log_path),
            "output_mph_path": str(actual_mph) if actual_mph else None,
            "removed_mph_path": str(removed_mph_path) if removed_mph_path else None,
            "requested_mph_path": str(batch_result.requested_mph_path) if batch_result.requested_mph_path else None,
            "config_snapshot_path": str(config_snapshot_path),
            "manifest_path": str(manifest_path),
            "csv_path": str(csv_path) if csv_path else None,
            "run_status": manifest["status"],
            "run_dir": str(run_dir),
        }
    except ComsolRunCancelled as exc:
        manifest.update({"status": "cancelled", "finished_at": _now_iso(), "error": str(exc)})
        _write_manifest(manifest_path, manifest)
        raise
    except Exception as exc:
        diagnostic_mph = getattr(exc, "output_mph_path", None)
        manifest.update({
            "status": (
                "geometry_blocked" if isinstance(exc, GeometryQualityError)
                else "model_saved_but_solve_failed" if diagnostic_mph else "failed"
            ),
            "finished_at": _now_iso(),
            "actual_mph_path": str(diagnostic_mph) if diagnostic_mph else None,
            "comsol_version": extract_comsol_version(read_comsol_log(log_path)),
            "error": str(exc),
        })
        _write_manifest(manifest_path, manifest)
        raise


def build_model_file_from_config(
    *,
    config_path: str | Path,
    output_java_path: str | Path,
    comsolcompile_path: str | Path,
    comsolbatch_path: str | Path,
    log_path: str | Path,
    output_mph_path: str | Path,
    runner: ComsolRunner | None = None,
    should_stop: Callable[[], bool] | None = None,
    run_dir: str | Path | None = None,
) -> dict:
    return run_comsol_case_from_config(
        config_path=config_path,
        output_java_path=output_java_path,
        comsolcompile_path=comsolcompile_path,
        comsolbatch_path=comsolbatch_path,
        log_path=log_path,
        output_mph_path=output_mph_path,
        runner=runner,
        should_stop=should_stop,
        run_study=False,
        export_results=False,
        run_dir=run_dir,
    )
