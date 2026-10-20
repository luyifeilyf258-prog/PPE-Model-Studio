from __future__ import annotations

from core.geometry_model import (
    ModelCase,
    RegionBlock,
)

def build_model_case(
    *,
    case_name: str,
    unit: str,
    battery_params: dict,
    electrochem_params: dict,
    neg_region,
    sep_region,
    pos_region,
    neg_particles,
    pos_particles,
    neg_binders,
    pos_binders,
    neg_segments,
    pos_segments,
    neg_packing_stats,
    pos_packing_stats,
    neg_binder_stats,
    pos_binder_stats,
) -> ModelCase:
    case = ModelCase(
        case_name=case_name,
        unit=unit,
        battery_params=battery_params,
        electrochem_params=electrochem_params,
    )

    case.regions = [
        RegionBlock(
            name="neg_region",
            role="negative",
            x=neg_region.x_min,
            y=neg_region.y_min,
            width=neg_region.width,
            height=neg_region.height,
        ),
        RegionBlock(
            name="sep_region",
            role="separator",
            x=sep_region.x_min,
            y=sep_region.y_min,
            width=sep_region.width,
            height=sep_region.height,
        ),
        RegionBlock(
            name="pos_region",
            role="positive",
            x=pos_region.x_min,
            y=pos_region.y_min,
            width=pos_region.width,
            height=pos_region.height,
        ),
    ]

    case.negative_particles = neg_particles
    case.positive_particles = pos_particles

    case.negative_binders = neg_binders
    case.positive_binders = pos_binders

    case.negative_segments = neg_segments
    case.positive_segments = pos_segments

    case.negative_packing_stats = neg_packing_stats
    case.positive_packing_stats = pos_packing_stats
    case.negative_binder_stats = neg_binder_stats
    case.positive_binder_stats = pos_binder_stats

    case.metadata = {
        "stage": "geometry_prebuild",
        "description": "Particles and binder network prepared in Python before COMSOL Java export."
    }

    return case