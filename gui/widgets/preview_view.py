import json
import math
from pathlib import Path

from PyQt6.QtCore import QTimer, QRectF, QPointF, Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
)


class HoverableRectItem(QGraphicsRectItem):
    def __init__(
            self,
            rect,
            *,
            tooltip: str,
            base_brush: QBrush,
            hover_brush: QBrush,
            base_pen: QPen,
            hover_pen: QPen,
            base_z: float,
            hover_z: float,
    ):
        if not isinstance(rect, QRectF):
            rect = QRectF(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))

        super().__init__(rect)
        self.base_brush = base_brush
        self.hover_brush = hover_brush
        self.base_pen = base_pen
        self.hover_pen = hover_pen
        self.base_z = base_z
        self.hover_z = hover_z

        self.setBrush(self.base_brush)
        self.setPen(self.base_pen)
        self.setZValue(self.base_z)
        short_tooltip = "\n".join(str(tooltip).splitlines()[:2])
        self.setToolTip(short_tooltip)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(self.hover_brush)
        self.setPen(self.hover_pen)
        self.setZValue(self.hover_z)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.base_brush)
        self.setPen(self.base_pen)
        self.setZValue(self.base_z)
        super().hoverLeaveEvent(event)


class HoverableEllipseItem(QGraphicsEllipseItem):
    def __init__(
            self,
            rect,
            *,
            tooltip: str,
            base_brush: QBrush,
            hover_brush: QBrush,
            base_pen: QPen,
            hover_pen: QPen,
            base_z: float,
            hover_z: float,
    ):
        if not isinstance(rect, QRectF):
            rect = QRectF(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))

        super().__init__(rect)
        self.base_brush = base_brush
        self.hover_brush = hover_brush
        self.base_pen = base_pen
        self.hover_pen = hover_pen
        self.base_z = base_z
        self.hover_z = hover_z

        self.setBrush(self.base_brush)
        self.setPen(self.base_pen)
        self.setZValue(self.base_z)
        short_tooltip = "\n".join(str(tooltip).splitlines()[:2])
        self.setToolTip(short_tooltip)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(self.hover_brush)
        self.setPen(self.hover_pen)
        self.setZValue(self.hover_z)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.base_brush)
        self.setPen(self.base_pen)
        self.setZValue(self.base_z)
        super().hoverLeaveEvent(event)


class PreviewImageView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item: QGraphicsPixmapItem | None = None
        self.has_content = False
        self.has_model_axes = False
        self.axis_model_scale = 1.0e6
        self.model_total_x_m = 0.0
        self.model_total_h_m = 0.0
        self.model_scene_rect = QRectF()
        self.current_scale = 1.0
        self.min_scale = 0.05
        self.max_scale = 80.0
        self.layer_names = [
            "regions",
            "negative_particles",
            "positive_particles",
            "binders",
        ]
        self.layer_labels = {
            "regions": "区域",
            "negative_particles": "负极颗粒",
            "positive_particles": "正极颗粒",
            "binders": "粘结剂",
            "axes": "坐标轴",
        }
        self.layer_visibility = {name: True for name in self.layer_names}
        self.show_axes = True
        self.layer_items = {name: [] for name in self.layer_names}

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setObjectName("previewBox")

    def clear_layer_items(self):
        self.layer_items = {name: [] for name in self.layer_names}

    def add_item_to_layer(self, layer_name: str, item):
        if layer_name not in self.layer_items:
            self.layer_items[layer_name] = []
        self.layer_items[layer_name].append(item)
        item.setVisible(self.layer_visibility.get(layer_name, True))

    def set_layer_visible(self, layer_name: str, visible: bool):
        layer_name = str(layer_name)
        visible = bool(visible)

        if layer_name == "axes":
            self.show_axes = visible
            self.viewport().update()
            return

        self.layer_visibility[layer_name] = visible
        for item in self.layer_items.get(layer_name, []):
            item.setVisible(visible)
        self.viewport().update()

    def is_layer_visible(self, layer_name: str) -> bool:
        if layer_name == "axes":
            return self.show_axes
        return self.layer_visibility.get(str(layer_name), True)

    def reset_view(self):
        if self.has_content:
            self.fit_scene_to_view()

    def export_view_screenshot(self, output_path: str | Path) -> bool:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pixmap = self.viewport().grab()
        return bool(pixmap.save(str(output_path), "PNG"))

    def set_image(self, image_path: str | Path):
        image_path = Path(image_path)

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            return False

        self.scene.clear()
        self.clear_layer_items()

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())

        self.resetTransform()
        self.current_scale = 1.0
        self.has_content = True
        self.has_model_axes = False
        self.model_scene_rect = QRectF()

        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        return True

    def set_model_json(self, json_path: str | Path):
        json_path = Path(json_path)

        if not json_path.exists():
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                case_data = json.load(f)
        except Exception:
            return False

        try:
            return self.set_model_case(case_data)
        except Exception:
            return False

    def set_model_case(self, case_data: dict):
        if not isinstance(case_data, dict):
            return False

        regions = case_data.get("regions", []) or []
        negative_particles = case_data.get("negative_particles", []) or []
        positive_particles = case_data.get("positive_particles", []) or []
        negative_binders = case_data.get("negative_binders", []) or []
        positive_binders = case_data.get("positive_binders", []) or []

        if not regions:
            return False

        try:
            total_thickness_x = max(float(r["y"]) + float(r["height"]) for r in regions)
            total_width_h = max(float(r["x"]) + float(r["width"]) for r in regions)
            scale = 1.0e6                                        
        except Exception:
            return False

        self.scene.clear()
        self.clear_layer_items()
        self.pixmap_item = None
        self.resetTransform()
        self.current_scale = 1.0
        self.has_content = True
        self.has_model_axes = True
        self.axis_model_scale = scale
        self.model_total_x_m = total_thickness_x
        self.model_total_h_m = total_width_h
        self.model_scene_rect = QRectF(
            0.0,
            -total_width_h * scale,
            total_thickness_x * scale,
            total_width_h * scale,
        )

                               
                                   
                                   
        def sx(value):
            return float(value) * scale

        def sy(value):
            return -float(value) * scale

        def length(value):
            return float(value) * scale

        def fmt_m(value):
            return f"{float(value):.6e} m"

        def fmt_um(value):
            return f"{float(value) * 1.0e6:.3f} µm"

        role_style = {
            "negative": {
                "brush": QBrush(QColor(210, 230, 255, 120)),
                "hover": QBrush(QColor(140, 190, 255, 190)),
                "pen": QPen(QColor(80, 130, 190), 0.35),
                "hover_pen": QPen(QColor(20, 80, 170), 1.2),
            },
            "separator": {
                "brush": QBrush(QColor(230, 230, 230, 110)),
                "hover": QBrush(QColor(200, 200, 200, 190)),
                "pen": QPen(QColor(150, 150, 150), 0.35),
                "hover_pen": QPen(QColor(90, 90, 90), 1.2),
            },
            "positive": {
                "brush": QBrush(QColor(255, 225, 205, 130)),
                "hover": QBrush(QColor(255, 170, 120, 190)),
                "pen": QPen(QColor(200, 110, 70), 0.35),
                "hover_pen": QPen(QColor(170, 60, 20), 1.2),
            },
        }

        for region in regions:
            try:
                name = region.get("name", "region")
                role = region.get("role", "region")
                x = float(region["x"])
                y = float(region["y"])
                w = float(region["width"])
                h = float(region["height"])
            except Exception:
                continue

            style = role_style.get(role, role_style["separator"])
            rect = (sx(y), sy(x + w), length(h), length(w))
            tooltip = (
                f"区域: {name}\n"
                f"role: {role}\n"
                f"x厚度起点: {fmt_m(y)} ({fmt_um(y)})\n"
                f"x厚度长度: {fmt_m(h)} ({fmt_um(h)})\n"
                f"h宽度起点: {fmt_m(x)} ({fmt_um(x)})\n"
                f"h宽度长度: {fmt_m(w)} ({fmt_um(w)})"
            )

            item = HoverableRectItem(
                rect,
                tooltip=tooltip,
                base_brush=style["brush"],
                hover_brush=style["hover"],
                base_pen=style["pen"],
                hover_pen=style["hover_pen"],
                base_z=-100,
                hover_z=-90,
            )
            self.scene.addItem(item)
            self.add_item_to_layer("regions", item)

        particle_styles = {
            "negative": {
                                                       
                "brush": QBrush(QColor(45, 145, 220, 255)),
                "hover": QBrush(QColor(10, 95, 200, 255)),
                "pen": QPen(QColor(20, 95, 170), 0.30),
                "hover_pen": QPen(QColor(0, 55, 145), 1.20),
            },
            "positive": {
                                                       
                "brush": QBrush(QColor(230, 35, 35, 255)),
                "hover": QBrush(QColor(190, 0, 0, 255)),
                "pen": QPen(QColor(165, 20, 20), 0.30),
                "hover_pen": QPen(QColor(120, 0, 0), 1.20),
            },
        }

        def add_particle(particle: dict):
            try:
                name = particle.get("name", "particle")
                electrode = particle.get("electrode", "")
                center = particle["center"]
                cx = float(center["x"])
                cy = float(center["y"])
                radius = float(particle["radius"])
                diameter = float(particle.get("diameter", radius * 2.0))
            except Exception:
                return

            style = particle_styles.get(electrode, particle_styles["negative"])
            cx_s = sx(cy)
            cy_s = sy(cx)
            r_s = length(radius)
            rect = (cx_s - r_s, cy_s - r_s, 2.0 * r_s, 2.0 * r_s)
            tooltip = (
                f"颗粒: {name}\n"
                f"electrode: {electrode}\n"
                f"center.x厚度: {fmt_m(cy)} ({fmt_um(cy)})\n"
                f"center.h宽度: {fmt_m(cx)} ({fmt_um(cx)})\n"
                f"radius: {fmt_m(radius)} ({fmt_um(radius)})\n"
                f"diameter: {fmt_m(diameter)} ({fmt_um(diameter)})"
            )

            item = HoverableEllipseItem(
                rect,
                tooltip=tooltip,
                base_brush=style["brush"],
                hover_brush=style["hover"],
                base_pen=style["pen"],
                hover_pen=style["hover_pen"],
                base_z=20,
                hover_z=40,
            )
            self.scene.addItem(item)
            if electrode == "positive":
                self.add_item_to_layer("positive_particles", item)
            else:
                self.add_item_to_layer("negative_particles", item)

        for particle in negative_particles:
            add_particle(particle)

        for particle in positive_particles:
            add_particle(particle)

        binder_styles = {
            "negative": {
                                                             
                "brush": QBrush(QColor(15, 15, 15, 245)),
                "hover": QBrush(QColor(0, 0, 0, 255)),
                "pen": QPen(QColor(0, 0, 0), 0.25),
                "hover_pen": QPen(QColor(0, 0, 0), 0.90),
            },
            "positive": {
                "brush": QBrush(QColor(15, 15, 15, 245)),
                "hover": QBrush(QColor(0, 0, 0, 255)),
                "pen": QPen(QColor(0, 0, 0), 0.25),
                "hover_pen": QPen(QColor(0, 0, 0), 0.90),
            },
        }

        def add_binder(binder: dict):
            try:
                name = binder.get("name", "binder")
                electrode = binder.get("electrode", "")
                source = binder.get("source", "")
                owner_particle_name = binder.get("owner_particle_name")
                center = binder["center"]
                cx = float(center["x"])
                cy = float(center["y"])
                width = float(binder["width"])
                bridge_length = float(binder["length"])
                rotation_deg = float(binder.get("rotation_deg", 0.0))
            except Exception:
                return

            if bridge_length <= 0:
                return

            style = binder_styles.get(electrode, binder_styles["negative"])
            l_s = max(length(bridge_length), 0.5)
                                              
            w_s = max(length(width) * 4.0, 0.75)
            rect = (-l_s / 2.0, -w_s / 2.0, l_s, w_s)

            tooltip = (
                f"Binder: {name}\n"
                f"electrode: {electrode}\n"
                f"source: {source}\n"
                f"owner_particle: {owner_particle_name}\n"
                f"center.x厚度: {fmt_m(cy)} ({fmt_um(cy)})\n"
                f"center.h宽度: {fmt_m(cx)} ({fmt_um(cx)})\n"
                f"width: {fmt_m(width)} ({fmt_um(width)})\n"
                f"length: {fmt_m(bridge_length)} ({fmt_um(bridge_length)})\n"
                f"rotation_deg: {rotation_deg:.3f}"
            )

            item = HoverableRectItem(
                rect,
                tooltip=tooltip,
                base_brush=style["brush"],
                hover_brush=style["hover"],
                base_pen=style["pen"],
                hover_pen=style["hover_pen"],
                base_z=5,
                hover_z=15,
            )
            item.setPos(sx(cy), sy(cx))
            angle_from_x_axis = 90.0 - rotation_deg
                                             
            item.setRotation(angle_from_x_axis - 90.0)
            self.scene.addItem(item)
            self.add_item_to_layer("binders", item)

        for binder in negative_binders:
            add_binder(binder)

        for binder in positive_binders:
            add_binder(binder)


        bounds = self.scene.itemsBoundingRect()
        base_rect = self.model_scene_rect.united(bounds)
                                                                  
                                                 
        pad = max(base_rect.width(), base_rect.height()) * 1.20
        if pad <= 0:
            pad = 20.0
        self.scene.setSceneRect(base_rect.adjusted(-pad, -pad, pad, pad))

        self.fit_scene_to_view()
        return True

    def fit_scene_to_view(self):
        self.resetTransform()
        self.current_scale = 1.0

        if self.has_model_axes and not self.model_scene_rect.isNull():
            rect = self.model_scene_rect
        else:
            rect = self.scene.sceneRect()

        if rect.isNull():
            return

        if not self.has_model_axes:
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.viewport().update()
            return

        plot_rect = self.get_axis_plot_rect()
        inner_rect = plot_rect.adjusted(16.0, 16.0, -16.0, -16.0)

        if inner_rect.width() <= 2 or inner_rect.height() <= 2:
            return

                                                            
                                   
        sx = inner_rect.width() / max(rect.width(), 1.0e-12)
        sy = inner_rect.height() / max(rect.height(), 1.0e-12)
        fit_factor = min(sx, sy)

        if not math.isfinite(fit_factor) or fit_factor <= 0:
            return

        self.scale(fit_factor, fit_factor)
        self.current_scale = 1.0

                                                       
                                                                   
        viewport_center = QPointF(self.viewport().width() / 2.0, self.viewport().height() / 2.0)
        plot_center = inner_rect.center()
        offset_in_scene = QPointF(
            (viewport_center.x() - plot_center.x()) / fit_factor,
            (viewport_center.y() - plot_center.y()) / fit_factor,
        )
        target_center = rect.center() + offset_in_scene
        self.centerOn(target_center)

                                                      
                            
        for _ in range(2):
            mapped = self.mapFromScene(rect).boundingRect()
            dx = mapped.center().x() - inner_rect.center().x()
            dy = mapped.center().y() - inner_rect.center().y()
            if abs(dx) < 0.5 and abs(dy) < 0.5:
                break
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + int(round(dx)))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + int(round(dy)))

        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.has_content and self.has_model_axes and self.show_axes:
            painter = QPainter(self.viewport())
            try:
                self.draw_fixed_axis_overlay(painter)
            finally:
                painter.end()

    def get_axis_plot_rect(self) -> QRectF:
        width = self.viewport().width()
        height = self.viewport().height()

        left_margin = 58
        top_margin = 24
        right_margin = 22
        bottom_margin = 44

        plot_width = max(40, width - left_margin - right_margin)
        plot_height = max(40, height - top_margin - bottom_margin)

        return QRectF(left_margin, top_margin, plot_width, plot_height)

    def nice_tick_step(self, value_range: float, target_count: int = 5) -> float:
        value_range = abs(float(value_range))
        if value_range <= 0 or not math.isfinite(value_range):
            return 1.0

        raw_step = value_range / max(target_count - 1, 1)
        exponent = math.floor(math.log10(raw_step))
        fraction = raw_step / (10.0 ** exponent)

        if fraction <= 1.0:
            nice_fraction = 1.0
        elif fraction <= 2.0:
            nice_fraction = 2.0
        elif fraction <= 5.0:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0

        return nice_fraction * (10.0 ** exponent)

    def axis_ticks(self, min_value: float, max_value: float, target_count: int = 5) -> list[float]:
        min_value = float(min_value)
        max_value = float(max_value)

        if not math.isfinite(min_value) or not math.isfinite(max_value):
            return []

        if max_value < min_value:
            min_value, max_value = max_value, min_value

        if abs(max_value - min_value) <= 1.0e-30:
            return [min_value]

        step = self.nice_tick_step(max_value - min_value, target_count=target_count)
        start = math.ceil(min_value / step) * step
        stop = math.floor(max_value / step) * step

        ticks = []
        value = start
        guard = 0
        while value <= stop + step * 1.0e-9 and guard < 100:
            if min_value - step * 1.0e-9 <= value <= max_value + step * 1.0e-9:
                ticks.append(0.0 if abs(value) < step * 1.0e-9 else value)
            value += step
            guard += 1

        if not ticks:
            ticks = [min_value, max_value]

        return ticks

    def axis_minor_ticks(
            self,
            major_ticks: list[float],
            min_value: float,
            max_value: float,
            subdivisions: int = 2,
    ) -> list[float]:
        if len(major_ticks) < 2 or subdivisions <= 1:
            return []

        try:
            major_ticks = sorted(float(v) for v in major_ticks)
            step = abs(major_ticks[1] - major_ticks[0])
        except Exception:
            return []

        if step <= 0 or not math.isfinite(step):
            return []

        minor_step = step / subdivisions
        if minor_step <= 0:
            return []

        min_value = float(min_value)
        max_value = float(max_value)
        start = math.ceil(min_value / minor_step) * minor_step
        stop = math.floor(max_value / minor_step) * minor_step

        major_tol = minor_step * 1.0e-6
        minors = []
        value = start
        guard = 0
        while value <= stop + minor_step * 1.0e-9 and guard < 300:
            is_major = any(abs(value - major) <= major_tol for major in major_ticks)
            if not is_major:
                minors.append(0.0 if abs(value) < minor_step * 1.0e-9 else value)
            value += minor_step
            guard += 1

        return minors

    def axis_exponent(self, ticks: list[float], min_value: float, max_value: float) -> int:
\
\
\
\
\
           
        base = 0.0

        try:
            sorted_ticks = sorted(float(v) for v in ticks if math.isfinite(float(v)))
            diffs = [abs(b - a) for a, b in zip(sorted_ticks[:-1], sorted_ticks[1:])]
            diffs = [d for d in diffs if d > 1.0e-30]
            if diffs:
                base = min(diffs)
        except Exception:
            base = 0.0

        if base <= 0:
            try:
                base = abs(float(max_value) - float(min_value))
            except Exception:
                base = 0.0

        if base <= 0:
            try:
                base = max(abs(float(min_value)), abs(float(max_value)))
            except Exception:
                base = 0.0

        if base <= 0 or not math.isfinite(base):
            return 0

        exponent = int(math.floor(math.log10(base)))

                                                                        
        if -2 <= exponent <= 3:
            return 0

        return exponent

    def format_axis_number(self, value: float, exponent: int = 0) -> str:
        value = float(value)
        exponent = int(exponent)

        if exponent != 0:
            value = value / (10.0 ** exponent)

        if abs(value) < 1.0e-12:
            return "0"

        if abs(value - round(value)) < 1.0e-9:
            return str(int(round(value)))

        return f"{value:.4g}"

    def format_axis_multiplier(self, exponent: int) -> str:
        exponent = int(exponent)
        if exponent == 0:
            return ""
        return f"×10^{exponent}"

    def draw_fixed_axis_overlay(self, painter: QPainter):
        viewport_width = self.viewport().width()
        viewport_height = self.viewport().height()

        if viewport_width <= 20 or viewport_height <= 20:
            return

        plot_rect = self.get_axis_plot_rect()
        scale = float(getattr(self, "axis_model_scale", 1.0e6))
        if scale <= 0:
            scale = 1.0e6

                        
        left_bottom = self.mapToScene(int(plot_rect.left()), int(plot_rect.bottom()))
        right_bottom = self.mapToScene(int(plot_rect.right()), int(plot_rect.bottom()))
        left_top = self.mapToScene(int(plot_rect.left()), int(plot_rect.top()))

        x_min = min(left_bottom.x(), right_bottom.x()) / scale
        x_max = max(left_bottom.x(), right_bottom.x()) / scale

                                        
        h_a = -left_bottom.y() / scale
        h_b = -left_top.y() / scale
        h_min = min(h_a, h_b)
        h_max = max(h_a, h_b)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        frame_pen = QPen(QColor(70, 70, 70), 1.0)
        tick_pen = QPen(QColor(70, 70, 70), 1.0)
        text_color = QColor(20, 20, 20)
        background = QColor(250, 253, 255, 255)

                                         
        painter.fillRect(QRectF(0, 0, viewport_width, plot_rect.top()), background)
        painter.fillRect(QRectF(0, plot_rect.bottom(), viewport_width, viewport_height - plot_rect.bottom()), background)
        painter.fillRect(QRectF(0, plot_rect.top(), plot_rect.left(), plot_rect.height()), background)
        painter.fillRect(QRectF(plot_rect.right(), plot_rect.top(), viewport_width - plot_rect.right(), plot_rect.height()), background)

        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)

        x_ticks = self.axis_ticks(x_min, x_max, target_count=7)
        h_ticks = self.axis_ticks(h_min, h_max, target_count=7)
        x_minor_ticks = self.axis_minor_ticks(x_ticks, x_min, x_max, subdivisions=2)
        h_minor_ticks = self.axis_minor_ticks(h_ticks, h_min, h_max, subdivisions=2)
        x_exponent = self.axis_exponent(x_ticks, x_min, x_max)
        h_exponent = self.axis_exponent(h_ticks, h_min, h_max)

                                  
        painter.setPen(frame_pen)
        painter.drawRect(plot_rect)

        tick_len = 5
        minor_tick_len = 3
        painter.setPen(tick_pen)
        painter.setPen(text_color)

                          
        for x_value in x_minor_ticks:
            px = self.mapFromScene(QPointF(x_value * scale, 0.0)).x()
            if not (plot_rect.left() <= px <= plot_rect.right()):
                continue
            painter.setPen(tick_pen)
            painter.drawLine(int(px), int(plot_rect.bottom()), int(px), int(plot_rect.bottom() + minor_tick_len))
            painter.drawLine(int(px), int(plot_rect.top()), int(px), int(plot_rect.top() - minor_tick_len))

        for h_value in h_minor_ticks:
            py = self.mapFromScene(QPointF(0.0, -h_value * scale)).y()
            if not (plot_rect.top() <= py <= plot_rect.bottom()):
                continue
            painter.setPen(tick_pen)
            painter.drawLine(int(plot_rect.left() - minor_tick_len), int(py), int(plot_rect.left()), int(py))
            painter.drawLine(int(plot_rect.right()), int(py), int(plot_rect.right() + minor_tick_len), int(py))

                                   
        for x_value in x_ticks:
            px = self.mapFromScene(QPointF(x_value * scale, 0.0)).x()
            if not (plot_rect.left() <= px <= plot_rect.right()):
                continue

            painter.setPen(tick_pen)
            painter.drawLine(int(px), int(plot_rect.bottom()), int(px), int(plot_rect.bottom() + tick_len))
            painter.drawLine(int(px), int(plot_rect.top()), int(px), int(plot_rect.top() - tick_len))

            label = self.format_axis_number(x_value, x_exponent)
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.setPen(text_color)
            painter.drawText(
                int(px - text_rect.width() / 2),
                int(plot_rect.bottom() + tick_len + text_rect.height() + 2),
                label,
            )

                                  
        for h_value in h_ticks:
            py = self.mapFromScene(QPointF(0.0, -h_value * scale)).y()
            if not (plot_rect.top() <= py <= plot_rect.bottom()):
                continue

            painter.setPen(tick_pen)
            painter.drawLine(int(plot_rect.left() - tick_len), int(py), int(plot_rect.left()), int(py))
            painter.drawLine(int(plot_rect.right()), int(py), int(plot_rect.right() + tick_len), int(py))

            label = self.format_axis_number(h_value, h_exponent)
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.setPen(text_color)
            painter.drawText(
                int(plot_rect.left() - tick_len - text_rect.width() - 6),
                int(py + text_rect.height() / 2 - 3),
                label,
            )

                                       
        multiplier_font = QFont("Microsoft YaHei", 8)
        painter.setFont(multiplier_font)

        x_multiplier = self.format_axis_multiplier(x_exponent)
        if x_multiplier:
            text_rect = painter.fontMetrics().boundingRect(x_multiplier)
            painter.drawText(
                int(plot_rect.right() - text_rect.width() - 6),
                int(plot_rect.bottom() - 6),
                x_multiplier,
            )

        h_multiplier = self.format_axis_multiplier(h_exponent)
        if h_multiplier:
            painter.drawText(
                int(plot_rect.left() + 6),
                int(plot_rect.top() + painter.fontMetrics().height() + 2),
                h_multiplier,
            )

                                    
        painter.setPen(text_color)
        painter.drawText(
            int(plot_rect.right() - 46),
            int(viewport_height - 12),
            "x / m",
        )
        painter.drawText(
            8,
            int(plot_rect.top() - 8),
            "h / m",
        )

        painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)

                                               
        if self.has_content:
            QTimer.singleShot(0, self.fit_scene_to_view)

    def wheelEvent(self, event):
        if not self.has_content:
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.zoom_with_wheel(delta)
            event.accept()
            return

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.pan_horizontally(delta)
            event.accept()
            return

        self.pan_vertically(delta)
        event.accept()

    def zoom_with_wheel(self, delta: int):
        if delta == 0:
            return

        zoom_in_factor = 1.12
        zoom_out_factor = 1 / zoom_in_factor

        factor = zoom_in_factor if delta > 0 else zoom_out_factor
        new_scale = self.current_scale * factor

        if new_scale < self.min_scale or new_scale > self.max_scale:
            return

        self.scale(factor, factor)
        self.current_scale = new_scale

    def pan_horizontally(self, delta: int):
        step = 45

        bar = self.horizontalScrollBar()

        if delta > 0:
            bar.setValue(bar.value() + step)
        else:
            bar.setValue(bar.value() - step)

    def pan_vertically(self, delta: int):
        step = 45

        bar = self.verticalScrollBar()

        if delta > 0:
            bar.setValue(bar.value() - step)
        else:
            bar.setValue(bar.value() + step)

    def mouseDoubleClickEvent(self, event):
        if self.has_content:
            self.fit_scene_to_view()
        event.accept()


