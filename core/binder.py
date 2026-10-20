from __future__ import annotations

import math
from typing import List, Tuple

from core.geometry_model import (
    Particle,
    ParticleEdge,
    BinderBridge,
    BinderStats,
    NameFactory,
    Point2D,
    Segment2D,
)
from core.packing import RegionBox
from core.sampling import sample_binder_widths, SamplingError


class BinderError(Exception):
    pass


def trimmed_segment_between_particles(
    edge: ParticleEdge,
    embed_ratio: float = 0.25,
) -> Segment2D | None:
    p1 = edge.particle1
    p2 = edge.particle2

    dx = p2.center.x - p1.center.x
    dy = p2.center.y - p1.center.y
    L = math.sqrt(dx * dx + dy * dy)

    if L <= 0:
        return None

    ux = dx / L
    uy = dy / L

                    
    embed1 = max(0.0, min(embed_ratio * p1.radius, 0.45 * p1.radius))
    embed2 = max(0.0, min(embed_ratio * p2.radius, 0.45 * p2.radius))

              
    start = Point2D(
        x=p1.center.x + ux * (p1.radius - embed1),
        y=p1.center.y + uy * (p1.radius - embed1),
    )
    end = Point2D(
        x=p2.center.x - ux * (p2.radius - embed2),
        y=p2.center.y - uy * (p2.radius - embed2),
    )

    seg = Segment2D(start=start, end=end)
    if seg.length <= 0:
        return None

    return seg

def build_particle_particle_trimmed_segments(
    particle_edges: List[ParticleEdge],
) -> List[Segment2D]:
    trimmed_segments: List[Segment2D] = []

    for edge in particle_edges:
        seg = trimmed_segment_between_particles(edge=edge, embed_ratio=0.25)
        if seg is not None and seg.length > 0:
            trimmed_segments.append(seg)

    return trimmed_segments

def build_particle_particle_bridges(
    *,
    electrode: str,
    segments: List[Segment2D],
    widths,
    name_factory: NameFactory,
) -> List[BinderBridge]:
    if len(segments) != len(widths):
        raise BinderError(
            f"segments 数量与 widths 数量不一致: {len(segments)} vs {len(widths)}"
        )

    prefix = "neg_b" if electrode == "negative" else "pos_b"

    bridges: List[BinderBridge] = []
    for seg, width in zip(segments, widths):
        bridges.append(
            BinderBridge(
                name=name_factory.next(prefix),
                electrode=electrode,                
                center=seg.center,
                width=float(width),
                length=float(seg.length),
                rotation_deg=float(seg.angle_deg),
                source="particle_particle",
                owner_particle_name=None,
            )
        )
    return bridges


def select_collector_connection_particles(
    *,
    electrode: str,
    particles: List[Particle],
    region: RegionBox,
    mean_particle_diameter: float,
    collector_connection_width_factor: float,
) -> List[Particle]:
    threshold = collector_connection_width_factor * mean_particle_diameter
    selected: List[Particle] = []

    if electrode == "negative":
        for p in particles:
            dist_to_collector = p.center.y - region.y_min
            if dist_to_collector <= threshold:
                selected.append(p)

    elif electrode == "positive":
        for p in particles:
            dist_to_collector = region.y_max - p.center.y
            if dist_to_collector <= threshold:
                selected.append(p)

    else:
        raise BinderError(f"未知 electrode: {electrode}")

    return selected


def build_particle_collector_segments(
    *,
    electrode: str,
    particles: List[Particle],
    region: RegionBox,
    embed_ratio: float = 0.25,
) -> List[Segment2D]:
\
\
\
       
    segments: List[Segment2D] = []

    if electrode == "negative":
        for p in particles:
            embed = max(0.0, min(embed_ratio * p.radius, 0.45 * p.radius))
            start = Point2D(x=p.center.x, y=region.y_min)
            end = Point2D(x=p.center.x, y=p.center.y - (p.radius - embed))
            seg = Segment2D(start=start, end=end)
            if seg.length > 0:
                segments.append(seg)

    elif electrode == "positive":
        for p in particles:
            embed = max(0.0, min(embed_ratio * p.radius, 0.45 * p.radius))
            start = Point2D(x=p.center.x, y=p.center.y + (p.radius - embed))
            end = Point2D(x=p.center.x, y=region.y_max)
            seg = Segment2D(start=start, end=end)
            if seg.length > 0:
                segments.append(seg)

    else:
        raise BinderError(f"未知 electrode: {electrode}")

    return segments


def build_particle_collector_bridges(
    *,
    electrode: str,
    segments: List[Segment2D],
    widths,
    owner_particles: List[Particle],
    name_factory: NameFactory,
) -> List[BinderBridge]:
    if len(segments) != len(widths):
        raise BinderError(
            f"collector segments 数量与 widths 数量不一致: {len(segments)} vs {len(widths)}"
        )

    if len(segments) != len(owner_particles):
        raise BinderError(
            f"collector segments 数量与 owner_particles 数量不一致: {len(segments)} vs {len(owner_particles)}"
        )

    prefix = "neg_bc" if electrode == "negative" else "pos_bc"

    bridges: List[BinderBridge] = []
    for seg, width, owner in zip(segments, widths, owner_particles):
        bridges.append(
            BinderBridge(
                name=name_factory.next(prefix),
                electrode=electrode,                
                center=seg.center,
                width=float(width),
                length=float(seg.length),
                rotation_deg=float(seg.angle_deg),
                source="particle_collector",
                owner_particle_name=owner.name,
            )
        )
    return bridges


def estimate_mean_binder_width(
    *,
    region_area: float,
    binder_fraction: float,
    total_bridge_length: float,
) -> float:
    if total_bridge_length <= 0:
        raise BinderError("total_bridge_length 必须 > 0，无法估算平均粘结剂宽度。")

    target_binder_area = region_area * binder_fraction
    mean_width = target_binder_area / total_bridge_length

    if mean_width <= 0:
        raise BinderError(f"估算得到的 mean_width <= 0: {mean_width}")

    return mean_width


def bridge_x_interval(bridge: BinderBridge) -> Tuple[float, float]:
\
\
       
    x_left = bridge.center.x - bridge.width / 2.0
    x_right = bridge.center.x + bridge.width / 2.0
    return x_left, x_right


def prune_overlapping_collector_bridges(
    bridges: List[BinderBridge],
) -> List[BinderBridge]:
\
\
\
       
    if not bridges:
        return []

    candidates = sorted(bridges, key=lambda b: b.length, reverse=True)

    kept: List[BinderBridge] = []
    occupied_intervals: List[Tuple[float, float]] = []

    for bridge in candidates:
        x_left, x_right = bridge_x_interval(bridge)

        overlap = False
        for a, c in occupied_intervals:
            if not (x_right <= a or x_left >= c):
                overlap = True
                break

        if not overlap:
            kept.append(bridge)
            occupied_intervals.append((x_left, x_right))

    kept.sort(key=lambda b: b.center.x)
    return kept


def collector_bridge_intersects_other_particles(
    bridge: BinderBridge,
    particles: List[Particle],
    owner_particle: Particle,
) -> bool:
\
\
\
       
    x_left = bridge.center.x - bridge.width / 2.0
    x_right = bridge.center.x + bridge.width / 2.0
    y_bottom = bridge.center.y - bridge.length / 2.0
    y_top = bridge.center.y + bridge.length / 2.0

    for p in particles:
        if p.name == owner_particle.name:
            continue

        closest_x = min(max(p.center.x, x_left), x_right)
        closest_y = min(max(p.center.y, y_bottom), y_top)

        dx = p.center.x - closest_x
        dy = p.center.y - closest_y

        if dx * dx + dy * dy < p.radius * p.radius:
            return True

    return False


def prune_collector_bridges_overlapping_particles(
    bridges: List[BinderBridge],
    all_particles: List[Particle],
) -> List[BinderBridge]:
\
\
\
       
    particle_map = {p.name: p for p in all_particles}
    kept: List[BinderBridge] = []

    for bridge in bridges:
        owner_name = bridge.owner_particle_name
        if owner_name is None:
            continue

        owner_particle = particle_map.get(owner_name)
        if owner_particle is None:
            continue

        if not collector_bridge_intersects_other_particles(
            bridge=bridge,
            particles=all_particles,
            owner_particle=owner_particle,
        ):
            kept.append(bridge)

    return kept


def collector_bridges_to_segments(bridges: List[BinderBridge]) -> List[Segment2D]:
\
\
       
    segments: List[Segment2D] = []

    for b in bridges:
        theta = math.radians(b.rotation_deg)
        ux = math.sin(theta)                                  
        uy = math.cos(theta)

        hl = b.length / 2.0
        start = Point2D(
            x=b.center.x - hl * ux,
            y=b.center.y - hl * uy,
        )
        end = Point2D(
            x=b.center.x + hl * ux,
            y=b.center.y + hl * uy,
        )
        segments.append(Segment2D(start=start, end=end))

    return segments


def bridges_to_segments(bridges: List[BinderBridge]) -> List[Segment2D]:
\
\
       
    segments: List[Segment2D] = []

    for b in bridges:
        theta = math.radians(b.rotation_deg)
        ux = math.sin(theta)                                  
        uy = math.cos(theta)

        hl = b.length / 2.0
        start = Point2D(
            x=b.center.x - hl * ux,
            y=b.center.y - hl * uy,
        )
        end = Point2D(
            x=b.center.x + hl * ux,
            y=b.center.y + hl * uy,
        )
        segments.append(Segment2D(start=start, end=end))

    return segments


def particle_particle_bridge_intersects_other_particles(
    bridge: BinderBridge,
    particles: List[Particle],
    endpoint_particles: Tuple[Particle, Particle],
) -> bool:
\
\
\
       
    endpoint_names = {endpoint_particles[0].name, endpoint_particles[1].name}

    x_left = bridge.center.x - bridge.width / 2.0
    x_right = bridge.center.x + bridge.width / 2.0
    y_bottom = bridge.center.y - bridge.length / 2.0
    y_top = bridge.center.y + bridge.length / 2.0

    for p in particles:
        if p.name in endpoint_names:
            continue

        closest_x = min(max(p.center.x, x_left), x_right)
        closest_y = min(max(p.center.y, y_bottom), y_top)

        dx = p.center.x - closest_x
        dy = p.center.y - closest_y

        if dx * dx + dy * dy < p.radius * p.radius:
            return True

    return False


def prune_particle_particle_bridges_overlapping_particles(
    bridges: List[BinderBridge],
    particle_edges: List[ParticleEdge],
    all_particles: List[Particle],
) -> Tuple[List[BinderBridge], List[Segment2D]]:
\
\
\
       
    if len(bridges) != len(particle_edges):
        raise BinderError(
            f"particle-particle bridges 与 particle_edges 数量不一致: {len(bridges)} vs {len(particle_edges)}"
        )

    kept_bridges: List[BinderBridge] = []

    for bridge, edge in zip(bridges, particle_edges):
        intersects = particle_particle_bridge_intersects_other_particles(
            bridge=bridge,
            particles=all_particles,
            endpoint_particles=(edge.particle1, edge.particle2),
        )
        if not intersects:
            kept_bridges.append(bridge)

    kept_segments = bridges_to_segments(kept_bridges)
    return kept_bridges, kept_segments


def build_binder_network(
    *,
    electrode: str,
    region: RegionBox,
    particles: List[Particle],
    particle_edges: List[ParticleEdge],
    binder_fraction: float,
    mean_particle_diameter: float,
    width_dispersion: float,
    lognormal_std: float,
    collector_connection_width_factor: float,
    enable_collector_connections: bool,
    rng,
    name_factory: NameFactory,
) -> Tuple[List[BinderBridge], BinderStats, List[Segment2D], List[Segment2D]]:
    collector_particles: List[Particle] = []
    collector_segments: List[Segment2D] = []

    pp_segments = build_particle_particle_trimmed_segments(particle_edges)

    if enable_collector_connections:
        collector_particles = select_collector_connection_particles(
            electrode=electrode,
            particles=particles,
            region=region,
            mean_particle_diameter=mean_particle_diameter,
            collector_connection_width_factor=collector_connection_width_factor,
        )

        collector_segments = build_particle_collector_segments(
            electrode=electrode,
            particles=collector_particles,
            region=region,
        )

    total_pp_length = sum(seg.length for seg in pp_segments)
    total_pc_length = sum(seg.length for seg in collector_segments)
    total_bridge_length = total_pp_length + total_pc_length

    if total_bridge_length <= 0:
        stats = BinderStats(
            target_fraction=float(binder_fraction),
            estimated_mean_width=0.0,
            bridge_count=0,
            total_bridge_length=0.0,
            success=False,
            message=f"{electrode} 电极未生成任何粘结剂连接。",
        )
        return [], stats, pp_segments, collector_segments

    mean_width = estimate_mean_binder_width(
        region_area=region.area,
        binder_fraction=binder_fraction,
        total_bridge_length=total_bridge_length,
    )

    n_pp = len(pp_segments)
    n_pc = len(collector_segments)

    try:
        pp_widths = sample_binder_widths(
            n=n_pp,
            mean_width=mean_width,
            width_dispersion=width_dispersion,
            lognormal_std=lognormal_std,
            rng=rng,
        ) if n_pp > 0 else []

        pc_widths = sample_binder_widths(
            n=n_pc,
            mean_width=mean_width,
            width_dispersion=width_dispersion,
            lognormal_std=lognormal_std,
            rng=rng,
        ) if n_pc > 0 else []

    except SamplingError as e:
        raise BinderError(f"{electrode} 电极粘结剂宽度采样失败: {e}") from e

    bridges_pp = build_particle_particle_bridges(
        electrode=electrode,
        segments=pp_segments,
        widths=pp_widths,
        name_factory=name_factory,
    ) if n_pp > 0 else []

                                             
    if n_pp > 0:
        bridges_pp, pp_segments = prune_particle_particle_bridges_overlapping_particles(
            bridges=bridges_pp,
            particle_edges=particle_edges,
            all_particles=particles,
        )

    bridges_pc = build_particle_collector_bridges(
        electrode=electrode,
        segments=collector_segments,
        widths=pc_widths,
        owner_particles=collector_particles,
        name_factory=name_factory,
    ) if n_pc > 0 else []

                                     
    bridges_pc = prune_overlapping_collector_bridges(bridges_pc)

                                      
    bridges_pc = prune_collector_bridges_overlapping_particles(
        bridges=bridges_pc,
        all_particles=particles,
    )

                                        
    collector_segments = collector_bridges_to_segments(bridges_pc)

    bridges = bridges_pp + bridges_pc

    stats = BinderStats(
        target_fraction=float(binder_fraction),
        estimated_mean_width=float(mean_width),
        bridge_count=int(len(bridges)),
        total_bridge_length=float(sum(b.length for b in bridges)),
        success=bool(len(bridges) > 0),
        message="",
    )

    return bridges, stats, pp_segments, collector_segments