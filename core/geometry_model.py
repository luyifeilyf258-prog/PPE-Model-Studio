from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
import math
import numpy as np


@dataclass
class Point2D:
    x: float
    y: float


@dataclass
class Segment2D:
    start: Point2D
    end: Point2D

    @property
    def length(self) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return (dx**2 + dy**2) ** 0.5

    @property
    def center(self) -> Point2D:
        return Point2D(
            x=(self.start.x + self.end.x) / 2.0,
            y=(self.start.y + self.end.y) / 2.0,
        )

    @property
    def angle_deg(self) -> float:
\
\
\
           
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.degrees(math.atan2(dx, dy))


@dataclass
class RectangleShape:
    name: str
    x: float
    y: float
    width: float
    height: float
    rotation_deg: float = 0.0
    role: Optional[str] = None


@dataclass
class CircleShape:
    name: str
    center: Point2D
    radius: float
    role: Optional[str] = None


@dataclass
class Particle:
    name: str
    electrode: Literal["negative", "positive"]
    center: Point2D
    radius: float
    diameter: float
    area: float


@dataclass
class ParticleEdge:
    particle1: Particle
    particle2: Particle
    segment: Segment2D


@dataclass
class BinderBridge:
    name: str
    electrode: Literal["negative", "positive"]
    center: Point2D
    width: float
    length: float
    rotation_deg: float
    source: Literal["particle_particle", "particle_collector"]
    owner_particle_name: str | None = None


@dataclass
class RegionBlock:
    name: str
    role: Literal["negative", "separator", "positive"]
    x: float
    y: float
    width: float
    height: float


@dataclass
class PackingStats:
    target_area_fraction: float
    actual_area_fraction: float
    target_particle_area: float
    actual_particle_area: float
    particle_count: int
    placement_attempts: int
    success: bool
    message: str = ""


@dataclass
class BinderStats:
    target_fraction: float
    estimated_mean_width: float
    bridge_count: int
    total_bridge_length: float
    success: bool
    message: str = ""


@dataclass
class SelectionSpec:
    name: str
    entity_level: Literal["domain", "boundary", "curve", "feature"]
    source_feature_names: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ModelCase:
    case_name: str
    unit: str
    battery_params: Dict[str, float]
    electrochem_params: Dict[str, float]

    regions: List[RegionBlock] = field(default_factory=list)

    negative_particles: List[Particle] = field(default_factory=list)
    positive_particles: List[Particle] = field(default_factory=list)

    negative_binders: List[BinderBridge] = field(default_factory=list)
    positive_binders: List[BinderBridge] = field(default_factory=list)

    negative_segments: List[Segment2D] = field(default_factory=list)
    positive_segments: List[Segment2D] = field(default_factory=list)

    selections: List[SelectionSpec] = field(default_factory=list)

    negative_packing_stats: Optional[PackingStats] = None
    positive_packing_stats: Optional[PackingStats] = None
    negative_binder_stats: Optional[BinderStats] = None
    positive_binder_stats: Optional[BinderStats] = None

    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class NameFactory:
    counters: Dict[str, int] = field(default_factory=dict)

    def next(self, prefix: str) -> str:
        value = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = value
        return f"{prefix}{value}"


def _to_jsonable(obj):
\
\
\
       
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]

    if isinstance(obj, tuple):
        return tuple(_to_jsonable(v) for v in obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    return obj


def model_case_to_dict(case: ModelCase) -> dict:
    return _to_jsonable(asdict(case))


def particle_to_circle(p: Particle) -> CircleShape:
    return CircleShape(
        name=p.name,
        center=p.center,
        radius=p.radius,
        role=f"{p.electrode}_particle",
    )