from pathlib import Path
import json

from config.config_loader import load_case_config
from config.validators import validate_config
from core.sampling import make_rng, sample_particle_diameters, sample_binder_widths


def main():
    project_dir = Path(__file__).resolve().parent.parent
    case_yaml = project_dir / "config" / "case_demo.yaml"
    cfg = load_case_config(case_yaml_path=case_yaml, defaults_yaml_path=None)
    validate_config(cfg)

    rng = make_rng(cfg["project"]["random_seed"])

    neg_particle_d = sample_particle_diameters(
        n=10,
        mean_diameter=cfg["negative_electrode"]["particle"]["mean_diameter"],
        diameter_dispersion=cfg["negative_electrode"]["particle"]["diameter_dispersion"],
        lognormal_std=cfg["negative_electrode"]["particle"]["lognormal_std"],
        rng=rng,
    )

    pos_particle_d = sample_particle_diameters(
        n=10,
        mean_diameter=cfg["positive_electrode"]["particle"]["mean_diameter"],
        diameter_dispersion=cfg["positive_electrode"]["particle"]["diameter_dispersion"],
        lognormal_std=cfg["positive_electrode"]["particle"]["lognormal_std"],
        rng=rng,
    )

    neg_binder_w = sample_binder_widths(
        n=10,
        mean_width=1.0e-6,
        width_dispersion=cfg["negative_electrode"]["binder"]["width_dispersion"],
        lognormal_std=cfg["negative_electrode"]["binder"]["lognormal_std"],
        rng=rng,
    )

    print("负极颗粒直径样本：", neg_particle_d)
    print("正极颗粒直径样本：", pos_particle_d)
    print("负极粘结剂宽度样本：", neg_binder_w)

    output = {
        "neg_particle_diameters": neg_particle_d.tolist(),
        "pos_particle_diameters": pos_particle_d.tolist(),
        "neg_binder_widths": neg_binder_w.tolist(),
    }

    out_path = project_dir / "output" / "json" / "sampling_test.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"采样测试结果已保存到: {out_path}")


if __name__ == "__main__":
    main()