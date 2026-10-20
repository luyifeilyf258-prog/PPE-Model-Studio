from __future__ import annotations

from typing import List, Tuple, Dict

import numpy as np
from scipy.spatial import Delaunay

from core.geometry_model import Particle, Segment2D, ParticleEdge


class TriangulationError(Exception):
    pass


def particle_centers_to_array(particles: List[Particle]) -> np.ndarray:
    if len(particles) == 0:
        raise TriangulationError("颗粒列表为空，无法进行三角剖分。")
    return np.array([[p.center.x, p.center.y] for p in particles], dtype=float)


def unique_edges_from_simplices(simplices: np.ndarray) -> List[Tuple[int, int]]:
    edge_set = set()

    for tri in simplices:
        i, j, k = tri
        edge_set.update({
            tuple(sorted((i, j))),
            tuple(sorted((i, k))),
            tuple(sorted((j, k))),
        })

    return sorted(edge_set)


def build_particle_edges(
    particles: List[Particle],
    max_edge_length: float | None = None,
) -> List[ParticleEdge]:
    if len(particles) < 2:
        return []

    if len(particles) == 2:
        p1, p2 = particles[0], particles[1]
        seg = Segment2D(start=p1.center, end=p2.center)
        if max_edge_length is None or seg.length <= max_edge_length:
            return [ParticleEdge(particle1=p1, particle2=p2, segment=seg)]
        return []

    points = particle_centers_to_array(particles)

    try:
        tri = Delaunay(points)
    except Exception as e:
        raise TriangulationError(f"Delaunay 三角剖分失败: {e}") from e

    index_edges = unique_edges_from_simplices(tri.simplices)

    particle_edges: List[ParticleEdge] = []
    for i, j in index_edges:
        p1 = particles[i]
        p2 = particles[j]
        seg = Segment2D(start=p1.center, end=p2.center)

        if max_edge_length is not None and seg.length > max_edge_length:
            continue

        particle_edges.append(
            ParticleEdge(
                particle1=p1,
                particle2=p2,
                segment=seg,
            )
        )

    return particle_edges


def particle_edges_to_segments(edges: List[ParticleEdge]) -> List[Segment2D]:
    return [e.segment for e in edges]


def summarize_segments(segments: List[Segment2D]) -> Dict[str, float]:
    if not segments:
        return {
            "count": 0.0,
            "total_length": 0.0,
            "mean_length": 0.0,
            "max_length": 0.0,
            "min_length": 0.0,
        }

    lengths = np.array([seg.length for seg in segments], dtype=float)

    return {
        "count": float(len(segments)),
        "total_length": float(lengths.sum()),
        "mean_length": float(lengths.mean()),
        "max_length": float(lengths.max()),
        "min_length": float(lengths.min()),
    }

def resolve_max_edge_length(
    particles: list[Particle],
    configured_max_edge_length: float | None,
    multiplier: float = 3.0,
) -> float | None:
\
\
\
\
       
    if configured_max_edge_length is not None:
        return float(configured_max_edge_length)

    if not particles:
        return None

    actual_mean_diameter = sum(p.diameter for p in particles) / len(particles)
    return float(multiplier * actual_mean_diameter)