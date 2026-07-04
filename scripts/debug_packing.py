from pathlib import Path
import json
import numpy as np

from config.config_loader import load_case_config
from config.validators import validate_config
from core.sampling import make_rng
from core.packing import RegionBox, build_particles_in_region
from core.geometry_model import NameFactory


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    elif isinstance(obj, tuple):
        return [to_jsonable(v) for v in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def main():
    project_dir = Path(__file__).resolve().parent.parent
    case_yaml = project_dir / "config" / "case_demo.yaml"

    cfg = load_case_config(case_yaml_path=case_yaml, defaults_yaml_path=None)
    validate_config(cfg)

    rng = make_rng(cfg["project"]["random_seed"])
    name_factory = NameFactory()

    h = cfg["battery"]["width_h"]
    L_neg = cfg["battery"]["neg_length"]
    L_sep = cfg["battery"]["sep_length"]
    L_pos = cfg["battery"]["pos_length"]

    neg_region = RegionBox(
        x_min=0.0,
        x_max=h,
        y_min=0.0,
        y_max=L_neg,
    )

    pos_region = RegionBox(
        x_min=0.0,
        x_max=h,
        y_min=L_neg + L_sep,
        y_max=L_neg + L_sep + L_pos,
    )

    neg_particles, neg_stats = build_particles_in_region(
        electrode="negative",
        region=neg_region,
        active_fraction=cfg["negative_electrode"]["active_fraction"],
        mean_diameter=cfg["negative_electrode"]["particle"]["mean_diameter"],
        diameter_dispersion=cfg["negative_electrode"]["particle"]["diameter_dispersion"],
        lognormal_std=cfg["negative_electrode"]["particle"]["lognormal_std"],
        rng=rng,
        name_factory=name_factory,
        max_attempts_per_particle=cfg["negative_electrode"]["packing"]["max_attempts_per_particle"],
        target_fill_tolerance=cfg["negative_electrode"]["packing"]["target_fill_tolerance"],
        sort_particles_descending=cfg["negative_electrode"]["packing"]["sort_particles_descending"],
        allow_tangent_contact=cfg["negative_electrode"]["packing"]["allow_tangent_contact"],
    )

    pos_particles, pos_stats = build_particles_in_region(
        electrode="positive",
        region=pos_region,
        active_fraction=cfg["positive_electrode"]["active_fraction"],
        mean_diameter=cfg["positive_electrode"]["particle"]["mean_diameter"],
        diameter_dispersion=cfg["positive_electrode"]["particle"]["diameter_dispersion"],
        lognormal_std=cfg["positive_electrode"]["particle"]["lognormal_std"],
        rng=rng,
        name_factory=name_factory,
        max_attempts_per_particle=cfg["positive_electrode"]["packing"]["max_attempts_per_particle"],
        target_fill_tolerance=cfg["positive_electrode"]["packing"]["target_fill_tolerance"],
        sort_particles_descending=cfg["positive_electrode"]["packing"]["sort_particles_descending"],
        allow_tangent_contact=cfg["positive_electrode"]["packing"]["allow_tangent_contact"],
    )

    print("负极颗粒数:", len(neg_particles))
    print("负极实际面积分数:", neg_stats.actual_area_fraction)
    print("负极放置总尝试次数:", neg_stats.placement_attempts)
    print("负极是否达标:", neg_stats.success)
    print("负极提示:", neg_stats.message)

    print("正极颗粒数:", len(pos_particles))
    print("正极实际面积分数:", pos_stats.actual_area_fraction)
    print("正极放置总尝试次数:", pos_stats.placement_attempts)
    print("正极是否达标:", pos_stats.success)
    print("正极提示:", pos_stats.message)

    output = {
        "negative_particles": [
            {
                "name": p.name,
                "x": p.center.x,
                "y": p.center.y,
                "radius": p.radius,
                "diameter": p.diameter,
                "area": p.area,
            }
            for p in neg_particles
        ],
        "positive_particles": [
            {
                "name": p.name,
                "x": p.center.x,
                "y": p.center.y,
                "radius": p.radius,
                "diameter": p.diameter,
                "area": p.area,
            }
            for p in pos_particles
        ],
        "negative_stats": {
            "target_area_fraction": neg_stats.target_area_fraction,
            "actual_area_fraction": neg_stats.actual_area_fraction,
            "particle_count": neg_stats.particle_count,
            "placement_attempts": neg_stats.placement_attempts,
            "success": neg_stats.success,
            "message": neg_stats.message,
        },
        "positive_stats": {
            "target_area_fraction": pos_stats.target_area_fraction,
            "actual_area_fraction": pos_stats.actual_area_fraction,
            "particle_count": pos_stats.particle_count,
            "placement_attempts": pos_stats.placement_attempts,
            "success": pos_stats.success,
            "message": pos_stats.message,
        },
    }

    out_path = project_dir / "output" / "json" / "packing_test.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(to_jsonable(output), f, indent=2, ensure_ascii=False)

    print(f"颗粒堆积测试结果已保存到: {out_path}")


if __name__ == "__main__":
    main()