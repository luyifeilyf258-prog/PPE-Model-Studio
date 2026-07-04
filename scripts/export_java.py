from pathlib import Path
from datetime import datetime
import json

from config.config_loader import load_case_config
from config.validators import validate_config
from core.geometry_model import model_case_to_dict
from export.preview_plot import plot_model_case
from export.java_writer import write_model_case_to_java
from pipeline.build_case import build_case_from_config


def _get_project_dir_from_config_path(config_path: Path) -> Path:
    if config_path.parent.name.lower() == "config":
        return config_path.parent.parent
    return config_path.parent


def _get_output_dir_from_config(config_path: Path, cfg: dict) -> Path:
    project_dir = _get_project_dir_from_config_path(config_path)
    output_dir_raw = cfg.get("project", {}).get("output_dir", "./output")
    output_dir = Path(output_dir_raw)

    if not output_dir.is_absolute():
        output_dir = project_dir / output_dir

    return output_dir


def _create_timestamp_run_dir(output_dir: Path) -> Path:
    runs_root = output_dir / "runs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_run_dir = runs_root / f"run_{timestamp}"

    run_dir = base_run_dir
    index = 2
    while run_dir.exists():
        run_dir = Path(f"{base_run_dir}_{index}")
        index += 1

    for sub_dir in ["json", "preview", "java", "logs", "mph", "results"]:
        (run_dir / sub_dir).mkdir(parents=True, exist_ok=True)

    return run_dir


def create_default_run_dir_for_config(config_path: str | Path, cfg: dict | None = None) -> Path:
    config_path = Path(config_path)
    if cfg is None:
        cfg = load_case_config(
            case_yaml_path=config_path,
            defaults_yaml_path=None,
        )

    output_dir = _get_output_dir_from_config(config_path, cfg)
    return _create_timestamp_run_dir(output_dir)


def _is_run_based_java_path(output_java_path: Path) -> bool:
    parts = [part.lower() for part in output_java_path.parts]
    return (
        output_java_path.parent.name.lower() == "java"
        and len(parts) >= 4
        and "runs" in parts
    )


def export_java_from_config(
    config_path: str | Path,
    output_java_path: str | Path,
    *,
    export_json: bool = True,
    export_preview: bool = True,
    json_path: str | Path | None = None,
    preview_path: str | Path | None = None,
    run_study: bool = True,
    export_results: bool = True,
    run_dir: str | Path | None = None,
) -> dict:
\
\
\
\
\
\
\
\
\
\
       
    config_path = Path(config_path)
    output_java_path = Path(output_java_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    cfg = load_case_config(
        case_yaml_path=config_path,
        defaults_yaml_path=None,
    )

    validate_config(cfg)

    if run_dir is not None:
        run_dir = Path(run_dir)
    elif _is_run_based_java_path(output_java_path):
        run_dir = output_java_path.parent.parent
    else:
        run_dir = create_default_run_dir_for_config(config_path, cfg)
        output_java_path = run_dir / "java" / output_java_path.name

    for sub_dir in ["json", "preview", "java", "logs", "mph", "results"]:
        (run_dir / sub_dir).mkdir(parents=True, exist_ok=True)

    case, context = build_case_from_config(cfg)

    output_java_path.parent.mkdir(parents=True, exist_ok=True)
    java_path = write_model_case_to_java(
        case,
        output_java_path,
        run_study=run_study,
        export_results=export_results,
    )

    result = {
        "java_path": str(java_path),
        "json_path": None,
        "preview_path": None,
        "run_dir": str(run_dir),
    }

    if export_json:
        if json_path is None:
            json_path = run_dir / "json" / "case_preview.json"

        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(model_case_to_dict(case), f, indent=2, ensure_ascii=False)

        result["json_path"] = str(json_path)

    if export_preview:
        if preview_path is None:
            preview_path = run_dir / "preview" / "case_preview.png"

        preview_path = Path(preview_path)
        preview_path.parent.mkdir(parents=True, exist_ok=True)

        plot_model_case(
            case,
            preview_path,
            binder_display_scale=3,
            draw_binder_on_top=True,
        )

        result["preview_path"] = str(preview_path)

    return result


def export_preview_from_config(
    config_path: str | Path,
    *,
    run_dir: str | Path | None = None,
    json_path: str | Path | None = None,
    preview_path: str | Path | None = None,
) -> dict:
\
\
\
\
\
       
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    cfg = load_case_config(
        case_yaml_path=config_path,
        defaults_yaml_path=None,
    )

    validate_config(cfg)

    if run_dir is not None:
        run_dir = Path(run_dir)
    else:
        run_dir = create_default_run_dir_for_config(config_path, cfg)

    for sub_dir in ["json", "preview", "java", "logs", "mph", "results"]:
        (run_dir / sub_dir).mkdir(parents=True, exist_ok=True)

    case, context = build_case_from_config(cfg)

    if json_path is None:
        json_path = run_dir / "json" / "case_preview.json"

    if preview_path is None:
        preview_path = run_dir / "preview" / "case_preview.png"

    json_path = Path(json_path)
    preview_path = Path(preview_path)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.parent.mkdir(parents=True, exist_ok=True)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(model_case_to_dict(case), f, indent=2, ensure_ascii=False)

    plot_model_case(
        case,
        preview_path,
        binder_display_scale=3,
        draw_binder_on_top=True,
    )

    return {
        "json_path": str(json_path),
        "preview_path": str(preview_path),
        "run_dir": str(run_dir),
    }


def main():
\
\
\
\
\
\
\
       
    project_dir = Path(__file__).resolve().parent.parent
    config_path = project_dir / "config" / "case_demo.yaml"

    cfg = load_case_config(
        case_yaml_path=config_path,
        defaults_yaml_path=None,
    )

    java_cfg = cfg.get("comsol", {}).get("java", {})
    java_class_name = java_cfg.get("class_name", "GeneratedGeometryLiionTest")

    run_dir = create_default_run_dir_for_config(config_path, cfg)
    output_java_path = run_dir / "java" / f"{java_class_name}.java"

    result = export_java_from_config(
        config_path=config_path,
        output_java_path=output_java_path,
        export_json=True,
        export_preview=True,
        run_dir=run_dir,
    )

    print("ModelCase 组装成功。")
    print(f"本次运行目录: {result['run_dir']}")
    print(f"Java 已保存: {result['java_path']}")

    if result["json_path"]:
        print(f"JSON 已保存: {result['json_path']}")

    if result["preview_path"]:
        print(f"预览图已保存: {result['preview_path']}")


if __name__ == "__main__":
    main()
