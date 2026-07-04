from core.sampling import make_rng
from core.packing import RegionBox, build_particles_in_region
from core.geometry_model import NameFactory
from core.triangulation import build_particle_edges, resolve_max_edge_length
from core.binder import build_binder_network
from core.case_builder import build_model_case


def build_case_from_config(cfg):
    rng = make_rng(cfg["project"]["random_seed"])
    name_factory = NameFactory()

    h = cfg["battery"]["width_h"]
    d = cfg["battery"]["thickness_d"]
    L_neg = cfg["battery"]["neg_length"]
    L_sep = cfg["battery"]["sep_length"]
    L_pos = cfg["battery"]["pos_length"]

    neg_region = RegionBox(0.0, h, 0.0, L_neg)
    sep_region = RegionBox(0.0, h, L_neg, L_neg + L_sep)
    pos_region = RegionBox(0.0, h, L_neg + L_sep, L_neg + L_sep + L_pos)

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

    battery_params = {
        "h": h,
        "d": d,
        "L_neg": L_neg,
        "L_sep": L_sep,
        "L_pos": L_pos,
    }

    advanced = cfg.get("advanced_settings", {})

    electrochem_params = {
        "ephn": cfg["negative_electrode"]["active_fraction"],
        "ephp": cfg["positive_electrode"]["active_fraction"],
        "cl_init": cfg["electrochemistry"]["electrolyte"]["cl_init"],
        "e_pert": cfg["electrochemistry"]["perturbation"]["e_pert"],
        "omega": cfg["electrochemistry"]["cv"]["scan_rate_mV_per_s"] / 1000.0,
        "v_max": cfg["electrochemistry"]["cv"]["v_max"],
        "v_min": cfg["electrochemistry"]["cv"]["v_min"],
        "c_rate": cfg["electrochemistry"]["cycling"]["c_rate"],
        "soc0_pos": cfg["electrochemistry"]["positive"]["soc0"],
        "k0_pos": cfg["electrochemistry"]["positive"]["k0"],
        "r_film_pos": cfg["electrochemistry"]["positive"]["r_film"],
        "c_dl_pos": cfg["electrochemistry"]["positive"]["c_dl"],
        "soc0_neg": cfg["electrochemistry"]["negative"]["soc0"],
        "k0_neg": cfg["electrochemistry"]["negative"]["k0"],
        "r_film_neg": cfg["electrochemistry"]["negative"]["r_film"],
        "c_dl_neg": cfg["electrochemistry"]["negative"]["c_dl"],
        "Eeq_neg0": 0.1,
        "Eeq_pos0": 4.0,
        "mesh_size": advanced.get("mesh_size", "normal"),
        "mesh_hauto": advanced.get("mesh_hauto", 5),
        "transient_max_iter": advanced.get("transient_max_iter", 100),
        "stationary_max_iter": advanced.get("stationary_max_iter", 100),
        "cutoff_voltage": advanced.get("cutoff_voltage", 3.3),
        "time_step": advanced.get("time_step", 2.0),
    }

    case = build_model_case(
        case_name=cfg["project"]["case_name"],
        unit=cfg["geometry"]["unit"],
        battery_params=battery_params,
        electrochem_params=electrochem_params,
        neg_region=neg_region,
        sep_region=sep_region,
        pos_region=pos_region,
        neg_particles=neg_particles,
        pos_particles=pos_particles,
        neg_binders=neg_binders,
        pos_binders=pos_binders,
        neg_segments=neg_pp_segments,
        pos_segments=pos_pp_segments,
        neg_packing_stats=neg_pack_stats,
        pos_packing_stats=pos_pack_stats,
        neg_binder_stats=neg_binder_stats,
        pos_binder_stats=pos_binder_stats,
    )

    context = {
        "neg_region": neg_region,
        "sep_region": sep_region,
        "pos_region": pos_region,
        "neg_particles": neg_particles,
        "pos_particles": pos_particles,
        "neg_edges": neg_edges,
        "pos_edges": pos_edges,
        "neg_binders": neg_binders,
        "pos_binders": pos_binders,
        "neg_pack_stats": neg_pack_stats,
        "pos_pack_stats": pos_pack_stats,
        "neg_binder_stats": neg_binder_stats,
        "pos_binder_stats": pos_binder_stats,
        "neg_pp_segments": neg_pp_segments,
        "pos_pp_segments": pos_pp_segments,
        "neg_pc_segments": neg_pc_segments,
        "pos_pc_segments": pos_pc_segments,
    }

    return case, context