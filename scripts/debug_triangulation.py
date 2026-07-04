from pathlib import Path
import json

from config.config_loader import load_case_config
from config.validators import validate_config
from core.sampling import make_rng
from core.packing import RegionBox, build_particles_in_region
from core.geometry_model import NameFactory
from core.triangulation import (
    build_particle_edges,
    particle_edges_to_segments,
    summarize_segments,
    resolve_max_edge_length,
)


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

    neg_max_edge_length = resolve_max_edge_length(
        particles=neg_particles,
        configured_max_edge_length=cfg["negative_electrode"]["network"]["max_edge_length"],
        multiplier=3.0,
    )

    pos_max_edge_length = resolve_max_edge_length(
        particles=pos_particles,
        configured_max_edge_length=cfg["positive_electrode"]["network"]["max_edge_length"],
        multiplier=3.0,
    )

    neg_edges = build_particle_edges(
        particles=neg_particles,
        max_edge_length=neg_max_edge_length,
    )

    pos_edges = build_particle_edges(
        particles=pos_particles,
        max_edge_length=pos_max_edge_length,
    )

    neg_segments = particle_edges_to_segments(neg_edges)
    pos_segments = particle_edges_to_segments(pos_edges)

    neg_seg_stats = summarize_segments(neg_segments)
    pos_seg_stats = summarize_segments(pos_segments)

    print("负极颗粒数:", len(neg_particles))
    print("负极边数:", int(neg_seg_stats["count"]))
    print("负极总边长:", neg_seg_stats["total_length"])
    print("负极平均边长:", neg_seg_stats["mean_length"])

    print("正极颗粒数:", len(pos_particles))
    print("正极边数:", int(pos_seg_stats["count"]))
    print("正极总边长:", pos_seg_stats["total_length"])
    print("正极平均边长:", pos_seg_stats["mean_length"])

    output = {
        "negative_particles": [
            {"name": p.name, "x": p.center.x, "y": p.center.y, "r": p.radius}
            for p in neg_particles
        ],
        "positive_particles": [
            {"name": p.name, "x": p.center.x, "y": p.center.y, "r": p.radius}
            for p in pos_particles
        ],
        "negative_segments": [
            {
                "x1": s.start.x,
                "y1": s.start.y,
                "x2": s.end.x,
                "y2": s.end.y,
                "length": s.length,
            }
            for s in neg_segments
        ],
        "positive_segments": [
            {
                "x1": s.start.x,
                "y1": s.start.y,
                "x2": s.end.x,
                "y2": s.end.y,
                "length": s.length,
            }
            for s in pos_segments
        ],
        "negative_segment_stats": neg_seg_stats,
        "positive_segment_stats": pos_seg_stats,
    }

    out_path = project_dir / "output" / "json" / "triangulation_test.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"三角剖分测试结果已保存到: {out_path}")


if __name__ == "__main__":
    main()