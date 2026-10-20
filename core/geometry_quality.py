from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import math
from statistics import median
from typing import Any, Iterable

from core.geometry_model import BinderBridge, ModelCase, Particle, Point2D, RegionBlock


@dataclass(frozen=True)
class GeometryIssue:
    severity: str
    code: str
    message: str
    objects: tuple[str, ...] = ()


class GeometryQualityError(RuntimeError):
    def __init__(self, report: dict[str, Any]):
        self.report = report
        errors = report.get("errors", [])
        message = "几何质量检查未通过，已阻止 COMSOL 求解。"
        if errors:
            message += "\n\n" + "\n".join(f"- {item['message']}" for item in errors[:8])
        super().__init__(message)


def _segment_endpoints(bridge: BinderBridge) -> tuple[Point2D, Point2D]:
    theta = math.radians(bridge.rotation_deg)
    direction_x = math.sin(theta)
    direction_y = math.cos(theta)
    half_length = bridge.length / 2.0
    return (
        Point2D(
            bridge.center.x - half_length * direction_x,
            bridge.center.y - half_length * direction_y,
        ),
        Point2D(
            bridge.center.x + half_length * direction_x,
            bridge.center.y + half_length * direction_y,
        ),
    )


def _distance_point_to_segment(point: Point2D, start: Point2D, end: Point2D) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return math.hypot(point.x - start.x, point.y - start.y)
    projection = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest_x = start.x + projection * dx
    closest_y = start.y + projection * dy
    return math.hypot(point.x - closest_x, point.y - closest_y)


def _particle_gap(first: Particle, second: Particle) -> float:
    return math.hypot(
        first.center.x - second.center.x,
        first.center.y - second.center.y,
    ) - first.radius - second.radius


def _region_for_electrode(case: ModelCase, electrode: str) -> RegionBlock:
    role = "negative" if electrode == "negative" else "positive"
    for region in case.regions:
        if region.role == role:
            return region
    raise ValueError(f"缺少 {role} 区域")


def _is_particle_inside_region(particle: Particle, region: RegionBlock, tolerance: float) -> bool:
    return (
        particle.center.x - particle.radius >= region.x - tolerance
        and particle.center.x + particle.radius <= region.x + region.width + tolerance
        and particle.center.y - particle.radius >= region.y - tolerance
        and particle.center.y + particle.radius <= region.y + region.height + tolerance
    )


def _make_selection_checks(case: ModelCase) -> tuple[list[dict[str, Any]], list[GeometryIssue]]:
    checks: list[dict[str, Any]] = []
    issues: list[GeometryIssue] = []
    groups = (
        ("negative_particles", case.negative_particles, "geom1_uni_neg_particles_dom", "域"),
        ("positive_particles", case.positive_particles, "geom1_uni_pos_particles_dom", "域"),
        ("negative_binders", case.negative_binders, "geom1_dif_neg_binders_dom", "域"),
        ("positive_binders", case.positive_binders, "geom1_dif_pos_binders_dom", "域"),
        ("negative_particle_electrolyte", case.negative_particles, "geom1_int_neg_particle_electrolyte_bnd", "边界"),
        ("positive_particle_electrolyte", case.positive_particles, "geom1_int_pos_particle_electrolyte_bnd", "边界"),
    )
    for name, source, java_tag, entity_level in groups:
        count = len(source)
        is_valid = count > 0
        checks.append({
            "name": name,
            "java_selection": java_tag,
            "entity_level": entity_level,
            "source_count": count,
            "status": "ready" if is_valid else "missing_source",
        })
        if not is_valid:
            issues.append(GeometryIssue(
                "error",
                "required_selection_source_empty",
                f"关键 COMSOL {entity_level} selection '{java_tag}' 没有可用的 {name} 源对象。",
            ))

    for name, region in (("negative_collector", _region_for_electrode(case, "negative")), ("positive_collector", _region_for_electrode(case, "positive"))):
        is_valid = region.width > 0 and region.height > 0
        checks.append({
            "name": name,
            "java_selection": f"geom1_gboxsel_{'neg' if name.startswith('negative') else 'pos'}_collector",
            "entity_level": "边界",
            "source_count": 1 if is_valid else 0,
            "status": "ready" if is_valid else "missing_source",
        })
        if not is_valid:
            issues.append(GeometryIssue(
                "error",
                "collector_region_invalid",
                f"{name} 的区域尺寸无效，无法生成集流体边界 selection。",
            ))
    return checks, issues


def _append_particle_shape_issues(
    particles: Iterable[Particle],
    region: RegionBlock,
    tolerance: float,
    issues: list[GeometryIssue],
) -> None:
    particle_list = list(particles)
    for particle in particle_list:
        if particle.radius <= tolerance:
            issues.append(GeometryIssue(
                "error", "particle_radius_nonpositive", f"颗粒 {particle.name} 的半径无效。", (particle.name,)
            ))
        elif not _is_particle_inside_region(particle, region, tolerance):
            issues.append(GeometryIssue(
                "error", "particle_outside_region", f"颗粒 {particle.name} 超出所属电极区域。", (particle.name,)
            ))

    for index, first in enumerate(particle_list):
        for second in particle_list[index + 1:]:
            gap = _particle_gap(first, second)
            if gap < -tolerance:
                issues.append(GeometryIssue(
                    "error", "particle_overlap", f"颗粒 {first.name} 与 {second.name} 发生重叠。", (first.name, second.name)
                ))
            elif gap <= tolerance:
                issues.append(GeometryIssue(
                    "error", "particle_tangent", f"颗粒 {first.name} 与 {second.name} 相切或间隙过小。", (first.name, second.name)
                ))


def _binder_contacts(
    bridge: BinderBridge,
    particles: Iterable[Particle],
    tolerance: float,
) -> list[str]:
    start, end = _segment_endpoints(bridge)
    contacts = []
    for particle in particles:
        distance = _distance_point_to_segment(particle.center, start, end)
        if distance <= particle.radius + bridge.width / 2.0 + tolerance:
            contacts.append(particle.name)
    return contacts


def _connectivity_report(
    particles: list[Particle],
    bridges: list[BinderBridge],
    median_diameter: float,
    issues: list[GeometryIssue],
) -> dict[str, Any]:
    tolerance = max(1.0e-15, median_diameter * 1.0e-8)
    graph: dict[str, set[str]] = {particle.name: set() for particle in particles}
    graph["collector"] = set()
    contacts_by_bridge: dict[str, list[str]] = {}

    for bridge in bridges:
        contacts = _binder_contacts(bridge, particles, tolerance)
        contacts_by_bridge[bridge.name] = contacts
        if bridge.width <= tolerance or bridge.length <= tolerance:
            issues.append(GeometryIssue(
                "error", "binder_dimension_invalid", f"binder {bridge.name} 的宽度或长度无效。", (bridge.name,)
            ))
            continue

        if bridge.source == "particle_particle" and len(contacts) < 2:
            issues.append(GeometryIssue(
                "error", "binder_missing_particle_contact", f"颗粒连接 binder {bridge.name} 未连接两个颗粒。", (bridge.name, *contacts)
            ))
        if bridge.source == "particle_collector" and len(contacts) < 1:
            issues.append(GeometryIssue(
                "error", "collector_binder_missing_particle_contact", f"集流体 binder {bridge.name} 未连接任何颗粒。", (bridge.name,)
            ))
        if len(contacts) > 2:
            issues.append(GeometryIssue(
                "warning", "binder_contacts_extra_particles", f"binder {bridge.name} 接触了超过两个颗粒，布尔几何可能较复杂。", (bridge.name, *contacts)
            ))

        for first_index, first in enumerate(contacts):
            for second in contacts[first_index + 1:]:
                graph[first].add(second)
                graph[second].add(first)
        if bridge.source == "particle_collector":
            for particle_name in contacts:
                graph["collector"].add(particle_name)
                graph[particle_name].add("collector")

        if bridge.width < 0.01 * median_diameter:
            issues.append(GeometryIssue(
                "warning", "binder_narrow_relative_to_particle", f"binder {bridge.name} 宽度低于颗粒中位直径的 1%，可能难以网格化。", (bridge.name,)
            ))
        if bridge.length / bridge.width > 150:
            issues.append(GeometryIssue(
                "warning", "binder_high_aspect_ratio", f"binder {bridge.name} 长宽比超过 150，可能产生细长网格单元。", (bridge.name,)
            ))

    reachable = {"collector"}
    queue: deque[str] = deque(["collector"])
    while queue:
        current = queue.popleft()
        for neighbour in graph.get(current, set()):
            if neighbour not in reachable:
                reachable.add(neighbour)
                queue.append(neighbour)
    disconnected = sorted(name for name in graph if name != "collector" and name not in reachable)
    if not graph["collector"]:
        issues.append(GeometryIssue(
            "error", "collector_not_connected", "没有 binder 将任何颗粒连接到集流体。"
        ))
    elif disconnected:
        issues.append(GeometryIssue(
            "warning",
            "particles_not_connected_to_collector",
            f"有 {len(disconnected)} 个颗粒未通过 binder 网络连接到集流体。",
            tuple(disconnected),
        ))

    return {
        "particle_count": len(particles),
        "binder_count": len(bridges),
        "collector_connected_particle_count": len(reachable) - 1,
        "disconnected_particles": disconnected,
        "bridge_contacts": contacts_by_bridge,
    }


def _append_small_gap_warnings(
    particles: list[Particle],
    bridges: list[BinderBridge],
    median_diameter: float,
    issues: list[GeometryIssue],
) -> dict[str, Any]:
    tolerance = max(1.0e-15, median_diameter * 1.0e-8)
    bridge_pairs = {
        frozenset(_binder_contacts(bridge, particles, tolerance))
        for bridge in bridges
        if bridge.source == "particle_particle"
    }
    minimum_gap = math.inf
    for index, first in enumerate(particles):
        for second in particles[index + 1:]:
            gap = _particle_gap(first, second)
            minimum_gap = min(minimum_gap, gap)
            if 0 < gap < 0.02 * median_diameter and frozenset((first.name, second.name)) not in bridge_pairs:
                issues.append(GeometryIssue(
                    "warning",
                    "unbridged_narrow_particle_gap",
                    f"颗粒 {first.name} 与 {second.name} 间存在未由 binder 填充的狭小间隙。",
                    (first.name, second.name),
                ))
    return {"minimum_particle_gap": None if minimum_gap == math.inf else minimum_gap}


def assess_geometry_quality(case: ModelCase) -> dict[str, Any]:
    """Build a conservative, Python-side preflight report for COMSOL export.

    The report validates only structures known before COMSOL performs its Boolean
    operations. It does not claim to replace COMSOL's final geometry checks.
    """
    issues: list[GeometryIssue] = []
    all_particles = case.negative_particles + case.positive_particles
    diameters = [particle.diameter for particle in all_particles if particle.diameter > 0]
    median_diameter = median(diameters) if diameters else 0.0
    tolerance = max(1.0e-15, median_diameter * 1.0e-8)

    _append_particle_shape_issues(
        case.negative_particles, _region_for_electrode(case, "negative"), tolerance, issues
    )
    _append_particle_shape_issues(
        case.positive_particles, _region_for_electrode(case, "positive"), tolerance, issues
    )
    selection_checks, selection_issues = _make_selection_checks(case)
    issues.extend(selection_issues)

    negative = _connectivity_report(
        case.negative_particles, case.negative_binders,
        median([p.diameter for p in case.negative_particles]) if case.negative_particles else 0.0,
        issues,
    )
    positive = _connectivity_report(
        case.positive_particles, case.positive_binders,
        median([p.diameter for p in case.positive_particles]) if case.positive_particles else 0.0,
        issues,
    )
    gap_summary = {
        "negative": _append_small_gap_warnings(
            case.negative_particles, case.negative_binders,
            median([p.diameter for p in case.negative_particles]) if case.negative_particles else 0.0,
            issues,
        ),
        "positive": _append_small_gap_warnings(
            case.positive_particles, case.positive_binders,
            median([p.diameter for p in case.positive_particles]) if case.positive_particles else 0.0,
            issues,
        ),
    }

    cell_area = sum(region.width * region.height for region in case.regions)
    estimated_solid_area = sum(particle.area for particle in all_particles) + sum(
        bridge.width * bridge.length for bridge in case.negative_binders + case.positive_binders
    )
    if cell_area <= 0:
        issues.append(GeometryIssue("error", "cell_area_invalid", "电池总区域面积无效。"))
    elif estimated_solid_area >= cell_area:
        issues.append(GeometryIssue(
            "warning",
            "solid_area_proxy_high",
            "颗粒和 binder 的矩形面积估算已接近或超过电池总面积；请在 COMSOL 中检查布尔几何。",
        ))

    errors = [asdict(issue) for issue in issues if issue.severity == "error"]
    warnings = [asdict(issue) for issue in issues if issue.severity == "warning"]
    return {
        "schema_version": 1,
        "status": "blocked" if errors else ("warning" if warnings else "ready"),
        "is_blocking": bool(errors),
        "summary": {
            "median_particle_diameter": median_diameter,
            "cell_area": cell_area,
            "estimated_solid_area_proxy": estimated_solid_area,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "connectivity": {"negative": negative, "positive": positive},
        "small_gap_summary": gap_summary,
        "selection_checks": selection_checks,
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "本报告在 Python 侧检查输入几何，不能替代 COMSOL 完成布尔运算后的最终实体检查。",
            "电解液连通性和最终 selection 实体数量仍应以 COMSOL 生成的几何为准。",
        ],
    }
