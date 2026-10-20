from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from core.geometry_model import Point2D, Particle, PackingStats, NameFactory
from core.sampling import sample_particle_diameters, SamplingError


class PackingError(Exception):
    pass


@dataclass
class RegionBox:
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height


def circle_area_from_diameter(d: float) -> float:
    r = d / 2.0
    return math.pi * r * r


def estimate_particle_count_for_target_area(
    target_particle_area: float,
    mean_diameter: float,
) -> int:
\
\
\
       
    mean_area = circle_area_from_diameter(mean_diameter)
    if mean_area <= 0:
        raise PackingError("平均颗粒面积必须 > 0")

    n = math.ceil(target_particle_area / mean_area)
    return max(n, 1)


def sample_diameters_until_target_area(
    target_particle_area: float,
    mean_diameter: float,
    diameter_dispersion: float,
    lognormal_std: float,
    rng: np.random.Generator,
    area_tolerance: float = 0.02,
    max_outer_iterations: int = 1000,
) -> np.ndarray:
\
\
\
\
\
\
\
       
    if target_particle_area <= 0:
        raise PackingError("target_particle_area 必须 > 0")

    n = estimate_particle_count_for_target_area(target_particle_area, mean_diameter)

    for _ in range(max_outer_iterations):
        diameters = sample_particle_diameters(
            n=n,
            mean_diameter=mean_diameter,
            diameter_dispersion=diameter_dispersion,
            lognormal_std=lognormal_std,
            rng=rng,
        )
        areas = np.array([circle_area_from_diameter(d) for d in diameters], dtype=float)
        total_area = areas.sum()

        if total_area >= target_particle_area * (1.0 - area_tolerance):
            return diameters

        n += 1

    raise PackingError(
        "无法在限定迭代次数内采样出满足目标面积要求的颗粒集合。"
    )


def is_valid_position(
    x: float,
    y: float,
    r: float,
    placed_particles: List[Particle],
    region: RegionBox,
    allow_tangent_contact: bool = False,
) -> bool:
\
\
\
\
       
    if x - r < region.x_min or x + r > region.x_max:
        return False
    if y - r < region.y_min or y + r > region.y_max:
        return False

    for p in placed_particles:
        dx = x - p.center.x
        dy = y - p.center.y
        dist = math.sqrt(dx * dx + dy * dy)
        min_dist = r + p.radius

        if allow_tangent_contact:
            if dist < min_dist:
                return False
        else:
            if dist <= min_dist:
                return False

    return True


def place_particles_nonoverlap(
    diameters: np.ndarray,
    region: RegionBox,
    electrode: str,
    rng: np.random.Generator,
    name_factory: NameFactory,
    max_attempts_per_particle: int = 5000,
    sort_descending: bool = True,
    allow_tangent_contact: bool = False,
) -> Tuple[List[Particle], int]:
\
\
\
\
\
       
    if sort_descending:
        diameters = np.sort(diameters)[::-1]

    particles: List[Particle] = []
    total_attempts = 0

    prefix = "neg_c" if electrode == "negative" else "pos_c"

    for d in diameters:
        r = d / 2.0
        placed = False

        for _ in range(max_attempts_per_particle):
            total_attempts += 1

            x = rng.uniform(region.x_min + r, region.x_max - r)
            y = rng.uniform(region.y_min + r, region.y_max - r)

            if is_valid_position(
                x=x,
                y=y,
                r=r,
                placed_particles=particles,
                region=region,
                allow_tangent_contact=allow_tangent_contact,
            ):
                particle = Particle(
                    name=name_factory.next(prefix),
                    electrode=electrode,                
                    center=Point2D(x=x, y=y),
                    radius=r,
                    diameter=d,
                    area=math.pi * r * r,
                )
                particles.append(particle)
                placed = True
                break

        if not placed:
                                   
            break

    return particles, total_attempts


def build_particles_in_region(
    *,
    electrode: str,
    region: RegionBox,
    active_fraction: float,
    mean_diameter: float,
    diameter_dispersion: float,
    lognormal_std: float,
    rng: np.random.Generator,
    name_factory: NameFactory,
    max_attempts_per_particle: int,
    target_fill_tolerance: float,
    sort_particles_descending: bool,
    allow_tangent_contact: bool,
) -> Tuple[List[Particle], PackingStats]:
\
\
\
       
    if electrode not in {"negative", "positive"}:
        raise PackingError(f"未知 electrode: {electrode}")

    target_particle_area = region.area * active_fraction

    try:
        diameters = sample_diameters_until_target_area(
            target_particle_area=target_particle_area,
            mean_diameter=mean_diameter,
            diameter_dispersion=diameter_dispersion,
            lognormal_std=lognormal_std,
            rng=rng,
            area_tolerance=target_fill_tolerance,
        )
    except SamplingError as e:
        raise PackingError(f"{electrode} 电极采样失败: {e}") from e

    particles, total_attempts = place_particles_nonoverlap(
        diameters=diameters,
        region=region,
        electrode=electrode,
        rng=rng,
        name_factory=name_factory,
        max_attempts_per_particle=max_attempts_per_particle,
        sort_descending=sort_particles_descending,
        allow_tangent_contact=allow_tangent_contact,
    )

    actual_particle_area = sum(p.area for p in particles)
    actual_area_fraction = actual_particle_area / region.area if region.area > 0 else 0.0

    success = actual_area_fraction >= max(0.0, active_fraction - target_fill_tolerance)

    message = ""
    if not success:
        message = (
            f"{electrode} 电极实际面积分数未达到目标。"
            f" target={active_fraction:.6f}, actual={actual_area_fraction:.6f}"
        )

    stats = PackingStats(
        target_area_fraction=active_fraction,
        actual_area_fraction=actual_area_fraction,
        target_particle_area=target_particle_area,
        actual_particle_area=actual_particle_area,
        particle_count=len(particles),
        placement_attempts=total_attempts,
        success=success,
        message=message,
    )

    return particles, stats