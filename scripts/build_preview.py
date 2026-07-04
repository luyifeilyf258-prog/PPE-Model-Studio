from pathlib import Path
import json

from config.config_loader import load_case_config
from config.validators import validate_config
from core.geometry_model import model_case_to_dict
from export.preview_plot import plot_model_case
from pipeline.build_case import build_case_from_config



def main():
    project_dir = Path(__file__).resolve().parent.parent
    case_yaml = project_dir / "config" / "case_demo.yaml"

    cfg = load_case_config(case_yaml_path=case_yaml, defaults_yaml_path=None)
    validate_config(cfg)

    case, context = build_case_from_config(cfg)

    json_path = project_dir / "output" / "json" / "case_preview.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(model_case_to_dict(case), f, indent=2, ensure_ascii=False)

    png_path = project_dir / "output" / "preview" / "case_preview.png"
    png_path.parent.mkdir(parents=True, exist_ok=True)
    plot_model_case(case, png_path, binder_display_scale=2, draw_binder_on_top=True)

    print("ModelCase 组装成功。")
    print(f"JSON 已保存到: {json_path}")
    print(f"预览图已保存到: {png_path}")


if __name__ == "__main__":
    main()

