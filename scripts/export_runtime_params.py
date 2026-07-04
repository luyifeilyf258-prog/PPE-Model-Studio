from pathlib import Path
import json

from config.config_loader import load_case_config, ensure_output_dirs, flatten_runtime_params
from config.validators import validate_config


def print_nested_params(data, prefix=""):
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            print_nested_params(value, full_key)
        else:
            print(f"{full_key} = {value}")


def main():
    project_dir = Path(__file__).resolve().parent.parent
    case_yaml = project_dir / "config" / "case_demo.yaml"

    cfg = load_case_config(
        case_yaml_path=case_yaml,
        defaults_yaml_path=None,
    )

    validate_config(cfg)
    ensure_output_dirs(cfg)

    runtime_params = flatten_runtime_params(cfg)

    output_dir = project_dir / cfg["project"]["output_dir"] / "json"
    output_dir.mkdir(parents=True, exist_ok=True)

    full_yaml_json = output_dir / f'{cfg["project"]["case_name"]}_full_yaml_config.json'
    runtime_json = output_dir / f'{cfg["project"]["case_name"]}_runtime_params.json'

    with full_yaml_json.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    with runtime_json.open("w", encoding="utf-8") as f:
        json.dump(runtime_params, f, indent=2, ensure_ascii=False)

    print("配置加载成功。")
    print("\n========== 扁平化运行时参数 ==========")
    print_nested_params(runtime_params)

    print(f"\nYAML 全部参数已导出: {full_yaml_json}")
    print(f"运行时参数已导出: {runtime_json}")


if __name__ == "__main__":
    main()