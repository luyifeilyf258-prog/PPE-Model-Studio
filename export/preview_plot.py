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
\
\
\
\
\
\
       
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
\
\
\
       
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
\
\
\
\
\
       
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


def plot_model_case(
    case,
    output_path: str | Path,
    binder_display_scale: float = 10.0,
    binder_display_width: float | None = None,
    trim_binder_inside_particles: bool = True,
    binder_surface_clearance: float = 0.0,
    draw_binder_on_top: bool = False,
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
\
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

    fig, ax = plt.subplots(figsize=(8, 10))

    role_color = {
        "negative": "#d9edf7",
        "separator": "#f5f5f5",
        "positive": "#fce4d6",
    }

         
    for region in case.regions:
        ax.add_patch(
            Rectangle(
                (region.x, region.y),
                region.width,
                region.height,
                facecolor=role_color.get(region.role, "#ffffff"),
                edgecolor="black",
                linewidth=1.2,
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
            ax.add_patch(
                Circle(
                    (p.center.x, p.center.y),
                    radius=p.radius,
                    facecolor="#377eb8",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=1.0,
                    zorder=3,
                )
            )

        for p in case.positive_particles:
            ax.add_patch(
                Circle(
                    (p.center.x, p.center.y),
                    radius=p.radius,
                    facecolor="#e41a1c",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=1.0,
                    zorder=3,
                )
            )

    def draw_one_binder_group(binders, particles, color):
        for b in binders:
            angle_deg = 90.0 - b.rotation_deg
            width = get_binder_width(b)

            if trim_binder_inside_particles:
                for seg_x, seg_y, seg_len in _iter_visible_binder_segments(
                    b,
                    particles,
                    angle_deg=angle_deg,
                    surface_clearance=binder_surface_clearance,
                ):
                    add_bridge_polygon(
                        ax,
                        center_x=seg_x,
                        center_y=seg_y,
                        width=width,
                        length=seg_len,
                        angle_deg=angle_deg,
                        facecolor=color,
                        edgecolor="none",
                        alpha=0.8,
                        zorder=4,
                    )
            else:
                add_bridge_polygon(
                    ax,
                    center_x=b.center.x,
                    center_y=b.center.y,
                    width=width,
                    length=b.length,
                    angle_deg=angle_deg,
                    facecolor=color,
                    edgecolor="none",
                    alpha=0.6,
                    zorder=2,
                )

    def draw_binders():
        draw_one_binder_group(
            case.negative_binders,
            case.negative_particles,
            color="#4daf4a",
        )
        draw_one_binder_group(
            case.positive_binders,
            case.positive_particles,
            color="#984ea3",
        )

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

    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"Preview: {case.case_name}")

          
    all_x = []
    all_y = []
    for region in case.regions:
        all_x.extend([region.x, region.x + region.width])
        all_y.extend([region.y, region.y + region.height])

    if all_x and all_y:
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        dx = x_max - x_min
        dy = y_max - y_min
        ax.set_xlim(x_min - 0.05 * dx, x_max + 0.05 * dx)
        ax.set_ylim(y_min - 0.05 * dy, y_max + 0.05 * dy)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
