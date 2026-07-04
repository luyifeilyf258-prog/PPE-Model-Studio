from __future__ import annotations

from pathlib import Path
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon


def add_bridge_polygon(ax, center_x, center_y, width, length, angle_deg, **kwargs):
\
\
\
\
\
\
\
       
    theta = math.radians(angle_deg)

    ux = math.cos(theta)
    uy = math.sin(theta)

    nx = -uy
    ny = ux

    hl = length / 2.0
    hw = width / 2.0

    p1 = (center_x - hl * ux - hw * nx, center_y - hl * uy - hw * ny)
    p2 = (center_x - hl * ux + hw * nx, center_y - hl * uy + hw * ny)
    p3 = (center_x + hl * ux + hw * nx, center_y + hl * uy + hw * ny)
    p4 = (center_x + hl * ux - hw * nx, center_y + hl * uy - hw * ny)

    poly = Polygon([p1, p2, p3, p4], closed=True, **kwargs)
    ax.add_patch(poly)
    return poly


def _line_circle_interval(
    line_center_x: float,
    line_center_y: float,
    ux: float,
    uy: float,
    circle_center_x: float,
    circle_center_y: float,
    radius: float,
    t_min: float,
    t_max: float,
):
    dx = line_center_x - circle_center_x
    dy = line_center_y - circle_center_y

    b = 2.0 * (dx * ux + dy * uy)
    c = dx * dx + dy * dy - radius * radius

    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None

    sqrt_disc = math.sqrt(max(disc, 0.0))
    t1 = (-b - sqrt_disc) / 2.0
    t2 = (-b + sqrt_disc) / 2.0
    if t1 > t2:
        t1, t2 = t2, t1

    left = max(t_min, t1)
    right = min(t_max, t2)
    if right <= left:
        return None

    return left, right


def _merge_intervals(intervals):
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]

    for left, right in intervals[1:]:
        last_left, last_right = merged[-1]
        if left <= last_right:
            merged[-1] = (last_left, max(last_right, right))
        else:
            merged.append((left, right))

    return merged


def _subtract_intervals(base_left, base_right, covered_intervals):
    visible = []
    current = base_left

    for left, right in _merge_intervals(covered_intervals):
        if left > current:
            visible.append((current, left))
        current = max(current, right)

    if current < base_right:
        visible.append((current, base_right))

    return visible


def _iter_visible_binder_segments(
    binder,
    particles,
    angle_deg: float,
    surface_clearance: float = 0.0,
):
    theta = math.radians(angle_deg)
    ux = math.cos(theta)
    uy = math.sin(theta)

    length = float(binder.length)
    if length <= 0.0:
        return

    t_min = -length / 2.0
    t_max = length / 2.0

    covered = []
    for p in particles:
        interval = _line_circle_interval(
            line_center_x=binder.center.x,
            line_center_y=binder.center.y,
            ux=ux,
            uy=uy,
            circle_center_x=p.center.x,
            circle_center_y=p.center.y,
            radius=max(float(p.radius) + surface_clearance, 0.0),
            t_min=t_min,
            t_max=t_max,
        )
        if interval is not None:
            covered.append(interval)

    min_len = max(length * 1e-9, 1e-15)
    for left, right in _subtract_intervals(t_min, t_max, covered):
        segment_length = right - left
        if segment_length <= min_len:
            continue

        segment_mid_t = (left + right) / 2.0
        segment_center_x = binder.center.x + segment_mid_t * ux
        segment_center_y = binder.center.y + segment_mid_t * uy

        yield segment_center_x, segment_center_y, segment_length


def _original_region_extent(case):
    all_x = []
    all_y = []
    for region in case.regions:
        all_x.extend([float(region.x), float(region.x + region.width)])
        all_y.extend([float(region.y), float(region.y + region.height)])

    if not all_x or not all_y:
        raise ValueError("case.regions 为空，无法确定绘图范围。")

    return min(all_x), max(all_x), min(all_y), max(all_y)


def _make_clockwise_90_transform(case):
\
\
\
\
\
\
\
\
       
    x_min, x_max, y_min, y_max = _original_region_extent(case)

    def transform_xy(x: float, y: float) -> tuple[float, float]:
        return float(y) - y_min, x_max - float(x)

    return transform_xy


def _rotated_region_rect(region, transform_xy) -> tuple[float, float, float, float]:
    corners = [
        transform_xy(region.x, region.y),
        transform_xy(region.x + region.width, region.y),
        transform_xy(region.x + region.width, region.y + region.height),
        transform_xy(region.x, region.y + region.height),
    ]
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    x0 = min(xs)
    y0 = min(ys)
    return x0, y0, max(xs) - x0, max(ys) - y0


def _rotated_region_extent(case, transform_xy):
    all_x = []
    all_y = []
    for region in case.regions:
        x0, y0, width, height = _rotated_region_rect(region, transform_xy)
        all_x.extend([x0, x0 + width])
        all_y.extend([y0, y0 + height])
    return min(all_x), max(all_x), min(all_y), max(all_y)


def _auto_horizontal_figsize(case, transform_xy, figure_width_in: float = 10.0) -> tuple[float, float]:
    x_min, x_max, y_min, y_max = _rotated_region_extent(case, transform_xy)
    dx = max(x_max - x_min, 1e-30)
    dy = max(y_max - y_min, 1e-30)
    figure_height_in = figure_width_in * dy / dx
    return figure_width_in, max(figure_height_in, 2.5)


def _make_binder_clip_patch(
    ax,
    region_rect,
    binder_width: float,
    electrode: str,
    is_collector_binder: bool,
    collector_clip_margin_factor: float,
):
\
\
\
\
\
\
       
    x0, y0, w, h = region_rect
    x = x0
    width = w

    if is_collector_binder:
        margin = max(float(binder_width) * float(collector_clip_margin_factor), 1e-9)
        margin = min(margin, 0.25 * w)

        if electrode == "negative":
            x = x0 + margin
            width = max(w - margin, 1e-9)
        elif electrode == "positive":
            x = x0
            width = max(w - margin, 1e-9)

    clip_patch = Rectangle((x, y0), width, h, transform=ax.transData)
    return clip_patch


def plot_model_case_for_paper(
    case,
    output_path: str | Path,
    binder_display_scale: float = 10.0,
    binder_display_width: float | None = None,
    trim_binder_inside_particles: bool = True,
    binder_surface_clearance: float = 0.0,
    draw_binder_on_top: bool = False,
    dpi: int = 300,
    figure_width_in: float = 10.0,
    padding_fraction: float = 0.02,
    transparent: bool = False,
    binder_color: str = "#000000",
    show_collector_binders: bool = True,
    collector_clip_margin_factor: float = 0.15,
):
\
\
\
\
\
\
\
\
\
       
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    transform_xy = _make_clockwise_90_transform(case)
    figsize = _auto_horizontal_figsize(case, transform_xy, figure_width_in=figure_width_in)

    fig, ax = plt.subplots(figsize=figsize)

    role_color = {
        "negative": "#d9edf7",
        "separator": "#f5f5f5",
        "positive": "#fce4d6",
    }

    rotated_region_rects = {}
    for region in case.regions:
        rotated_region_rects[region.role] = _rotated_region_rect(region, transform_xy)

                                             
    for region in case.regions:
        x0, y0, width, height = rotated_region_rects[region.role]
        ax.add_patch(
            Rectangle(
                (x0, y0),
                width,
                height,
                facecolor=role_color.get(region.role, "#ffffff"),
                edgecolor="none",
                linewidth=0.0,
                alpha=0.6,
                zorder=0,
            )
        )

    def get_binder_width(binder):
        if binder_display_width is not None:
            return float(binder_display_width)
        return float(binder.width) * float(binder_display_scale)

    def draw_particles():
        for p in case.negative_particles:
            x_new, y_new = transform_xy(p.center.x, p.center.y)
            ax.add_patch(
                Circle(
                    (x_new, y_new),
                    radius=p.radius,
                    facecolor="#377eb8",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=1.0,
                    zorder=3,
                )
            )

        for p in case.positive_particles:
            x_new, y_new = transform_xy(p.center.x, p.center.y)
            ax.add_patch(
                Circle(
                    (x_new, y_new),
                    radius=p.radius,
                    facecolor="#e41a1c",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=1.0,
                    zorder=3,
                )
            )

    def draw_one_binder_group(binders, particles, electrode_role):
        region_rect = rotated_region_rects[electrode_role]

        for b in binders:
            is_collector_binder = getattr(b, "source", None) == "particle_collector"

            if (not show_collector_binders) and is_collector_binder:
                continue

            original_angle_deg = 90.0 - b.rotation_deg
            rotated_angle_deg = original_angle_deg - 90.0
            width = get_binder_width(b)

            clip_patch = _make_binder_clip_patch(
                ax=ax,
                region_rect=region_rect,
                binder_width=width,
                electrode=electrode_role,
                is_collector_binder=is_collector_binder,
                collector_clip_margin_factor=collector_clip_margin_factor,
            )

            if trim_binder_inside_particles:
                for seg_x, seg_y, seg_len in _iter_visible_binder_segments(
                    b,
                    particles,
                    angle_deg=original_angle_deg,
                    surface_clearance=binder_surface_clearance,
                ):
                    seg_x_new, seg_y_new = transform_xy(seg_x, seg_y)

                    poly = add_bridge_polygon(
                        ax,
                        center_x=seg_x_new,
                        center_y=seg_y_new,
                        width=width,
                        length=seg_len,
                        angle_deg=rotated_angle_deg,
                        facecolor=binder_color,
                        edgecolor="none",
                        alpha=0.95,
                        zorder=4,
                    )
                    poly.set_clip_path(clip_patch)
            else:
                center_x_new, center_y_new = transform_xy(b.center.x, b.center.y)

                poly = add_bridge_polygon(
                    ax,
                    center_x=center_x_new,
                    center_y=center_y_new,
                    width=width,
                    length=b.length,
                    angle_deg=rotated_angle_deg,
                    facecolor=binder_color,
                    edgecolor="none",
                    alpha=0.95,
                    zorder=2,
                )
                poly.set_clip_path(clip_patch)

    def draw_binders():
        draw_one_binder_group(case.negative_binders, case.negative_particles, "negative")
        draw_one_binder_group(case.positive_binders, case.positive_particles, "positive")

    if trim_binder_inside_particles:
        draw_particles()
        draw_binders()
    else:
        if draw_binder_on_top:
            draw_particles()
            draw_binders()
        else:
            draw_binders()
            draw_particles()

                               
    for region in case.regions:
        x0, y0, width, height = rotated_region_rects[region.role]
        ax.add_patch(
            Rectangle(
                (x0, y0),
                width,
                height,
                facecolor="none",
                edgecolor="black",
                linewidth=1.2,
                zorder=10,
            )
        )

    ax.set_aspect("equal")
    ax.set_axis_off()

    x_min, x_max, y_min, y_max = _rotated_region_extent(case, transform_xy)
    dx = x_max - x_min
    dy = y_max - y_min
    pad_x = padding_fraction * dx
    pad_y = padding_fraction * dy

    ax.set_xlim(x_min - pad_x, x_max + pad_x)
    ax.set_ylim(y_min - pad_y, y_max + pad_y)

    fig.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.02,
        transparent=transparent,
    )
    plt.close(fig)