from pathlib import Path
import json

from config.config_loader import load_case_config
from config.validators import validate_config
from core.sampling import make_rng
from core.packing import RegionBox, build_particles_in_region
from core.geometry_model import NameFactory
from core.triangulation import build_particle_edges, resolve_max_edge_length
from core.binder import build_binder_network


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

    neg_particles, neg_pack_stats = build_particles_in_region(
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

    pos_particles, pos_pack_stats = build_particles_in_region(
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

    neg_binders, neg_binder_stats, neg_pp_segments, neg_pc_segments = build_binder_network(
        electrode="negative",
        region=neg_region,
        particles=neg_particles,
        particle_edges=neg_edges,
        binder_fraction=cfg["negative_electrode"]["binder_fraction"],
        mean_particle_diameter=cfg["negative_electrode"]["particle"]["mean_diameter"],
        width_dispersion=cfg["negative_electrode"]["binder"]["width_dispersion"],
        lognormal_std=cfg["negative_electrode"]["binder"]["lognormal_std"],
        collector_connection_width_factor=cfg["negative_electrode"]["binder"]["collector_connection_width_factor"],
        enable_collector_connections=cfg["negative_electrode"]["network"]["enable_collector_connections"],
        rng=rng,
        name_factory=name_factory,
    )

    pos_binders, pos_binder_stats, pos_pp_segments, pos_pc_segments = build_binder_network(
        electrode="positive",
        region=pos_region,
        particles=pos_particles,
        particle_edges=pos_edges,
        binder_fraction=cfg["positive_electrode"]["binder_fraction"],
        mean_particle_diameter=cfg["positive_electrode"]["particle"]["mean_diameter"],
        width_dispersion=cfg["positive_electrode"]["binder"]["width_dispersion"],
        lognormal_std=cfg["positive_electrode"]["binder"]["lognormal_std"],
        collector_connection_width_factor=cfg["positive_electrode"]["binder"]["collector_connection_width_factor"],
        enable_collector_connections=cfg["positive_electrode"]["network"]["enable_collector_connections"],
        rng=rng,
        name_factory=name_factory,
    )

    print("负极颗粒数:", len(neg_particles))
    print("负极颗粒-颗粒连接数:", len(neg_pp_segments))
    print("负极颗粒-集流体连接数:", len(neg_pc_segments))
    print("负极粘结剂总数:", len(neg_binders))
    print("负极估算平均粘结剂宽度:", neg_binder_stats.estimated_mean_width)
    print("负极总连接长度:", neg_binder_stats.total_bridge_length)

    print("正极颗粒数:", len(pos_particles))
    print("正极颗粒-颗粒连接数:", len(pos_pp_segments))
    print("正极颗粒-集流体连接数:", len(pos_pc_segments))
    print("正极粘结剂总数:", len(pos_binders))
    print("正极估算平均粘结剂宽度:", pos_binder_stats.estimated_mean_width)
    print("正极总连接长度:", pos_binder_stats.total_bridge_length)

    output = {
        "negative_binders": [
            {
                "name": b.name,
                "x": b.center.x,
                "y": b.center.y,
                "width": b.width,
                "length": b.length,
                "rotation_deg": b.rotation_deg,
                "source": b.source,
            }
            for b in neg_binders
        ],
        "positive_binders": [
            {
                "name": b.name,
                "x": b.center.x,
                "y": b.center.y,
                "width": b.width,
                "length": b.length,
                "rotation_deg": b.rotation_deg,
                "source": b.source,
            }
            for b in pos_binders
        ],
        "negative_binder_stats": {
            "target_fraction": neg_binder_stats.target_fraction,
            "estimated_mean_width": neg_binder_stats.estimated_mean_width,
            "bridge_count": neg_binder_stats.bridge_count,
            "total_bridge_length": neg_binder_stats.total_bridge_length,
            "success": neg_binder_stats.success,
            "message": neg_binder_stats.message,
        },
        "positive_binder_stats": {
            "target_fraction": pos_binder_stats.target_fraction,
            "estimated_mean_width": pos_binder_stats.estimated_mean_width,
            "bridge_count": pos_binder_stats.bridge_count,
            "total_bridge_length": pos_binder_stats.total_bridge_length,
            "success": pos_binder_stats.success,
            "message": pos_binder_stats.message,
        },
    }

    out_path = project_dir / "output" / "json" / "binder_test.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"粘结剂网络测试结果已保存到: {out_path}")
    print("负极自动 max_edge_length:", neg_max_edge_length)
    print("正极自动 max_edge_length:", pos_max_edge_length)


if __name__ == "__main__":
    main()