from __future__ import annotations

from pathlib import Path
from typing import Callable

from scripts.export_java import export_java_from_config, create_default_run_dir_for_config
from comsol_runner.runner import ComsolRunner, ComsolRunCancelled


def _is_legacy_output_java_path(output_java_path: Path) -> bool:
    return (
        output_java_path.parent.name.lower() == "java"
        and output_java_path.parent.parent.name.lower() == "output"
    )


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
    config_path = Path(config_path)
    output_java_path = Path(output_java_path)
    log_path = Path(log_path)

    if run_dir is not None:
        run_dir = Path(run_dir)
    elif _is_legacy_output_java_path(output_java_path):
        run_dir = create_default_run_dir_for_config(config_path)
        output_java_path = run_dir / "java" / output_java_path.name
        log_path = run_dir / "logs" / log_path.name
        if output_mph_path is not None:
            output_mph_path = run_dir / "mph" / Path(output_mph_path).name
    else:
        run_dir = output_java_path.parent.parent

    log_path.parent.mkdir(parents=True, exist_ok=True)

    def check_stopped():
        if should_stop is not None and should_stop():
            raise ComsolRunCancelled("COMSOL 计算已被用户停止。")

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

    java_path = Path(export_result["java_path"]).resolve()

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

    runner.run_class(
        class_path,
        log_path=log_path,
        output_mph_path=output_mph_path,
    )

    return {
        **export_result,
        "class_path": str(class_path),
        "log_path": str(log_path),
        "output_mph_path": str(output_mph_path) if output_mph_path else None,
        "run_dir": str(run_dir),
    }


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
\
\
\
\
       
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
