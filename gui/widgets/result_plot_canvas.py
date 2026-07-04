from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Mapping

import pandas as pd
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ResultPlotCanvas(FigureCanvas):
\
\
\
\
\
\
\
\
       

    DEFAULT_X_LIMIT = (0.0, 1.0)
    DEFAULT_X_TICKS = [0, 0.25, 0.50, 0.75, 1.00]
    DEFAULT_Y_LIMIT = (2.5, 4.5)
    DEFAULT_Y_TICKS = [2.5, 3.0, 3.5, 4.0, 4.5]

    def __init__(self, parent=None):
        self.fig = Figure(facecolor="#FFFFFF")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#FFFFFF")
        super().__init__(self.fig)
        self.setParent(parent)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._advance_animation)
        self._animation_series: list[dict] = []
        self._animation_lines = []
        self._animation_frame = 0
        self._animation_total_frames = 1

        self._apply_fixed_layout()

    def stop_animation(self):
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        self._animation_series = []
        self._animation_lines = []
        self._animation_frame = 0
        self._animation_total_frames = 1

    def _apply_fixed_layout(self):
\
\
\
\
\
           
        self.fig.subplots_adjust(
            left=0.16,
            right=0.98,
            bottom=0.28,
            top=0.94,
        )

    def _apply_axes_style(self):
        self.ax.set_xlabel("Time × C-rate (h)")
        self.ax.set_ylabel("Potential (V)")

                                                          
        self.ax.set_title("")

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color("#CBD5E1")
        self.ax.spines["bottom"].set_color("#CBD5E1")

        self.ax.tick_params(colors="#475569", labelsize=9)
        self.ax.xaxis.label.set_color("#334155")
        self.ax.yaxis.label.set_color("#334155")

        self.ax.grid(True, color="#E2E8F0", linewidth=0.7, alpha=0.85)

    def _reset_empty_axes_range(self):
        self.ax.set_xlim(*self.DEFAULT_X_LIMIT)
        self.ax.set_xticks(self.DEFAULT_X_TICKS)
        self.ax.set_ylim(*self.DEFAULT_Y_LIMIT)
        self.ax.set_yticks(self.DEFAULT_Y_TICKS)
        self.ax.margins(x=0)

    def _apply_x_axis_range(self, x_max_values: list[float]):
        self.ax.set_xlim(*self.DEFAULT_X_LIMIT)
        self.ax.set_xticks(self.DEFAULT_X_TICKS)

        if x_max_values:
            x_max = max(x_max_values)
            if x_max > self.DEFAULT_X_LIMIT[1]:
                self.ax.set_xlim(0, x_max)
                step = x_max / 4.0
                self.ax.set_xticks([0, step, step * 2.0, step * 3.0, x_max])

        self.ax.margins(x=0)

    def _apply_y_axis_range(self, series_data: list[dict]):
        y_values = []
        for series in series_data:
            y = series.get("y")
            if y is not None and len(y) > 0:
                y_values.extend([float(v) for v in y])

        if not y_values:
            self.ax.set_ylim(*self.DEFAULT_Y_LIMIT)
            self.ax.set_yticks(self.DEFAULT_Y_TICKS)
            return

        y_min = min(y_values)
        y_max = max(y_values)

        if math.isclose(y_min, y_max):
            margin = max(abs(y_min) * 0.03, 0.05)
        else:
            margin = (y_max - y_min) * 0.06

        self.ax.set_ylim(y_min - margin, y_max + margin)

    def clear_plot(self):
        self.stop_animation()
        self.ax.clear()
        self._reset_empty_axes_range()
        self._apply_axes_style()
        self._apply_fixed_layout()
        self.draw()

    def read_numeric_csv(self, csv_path: str | Path) -> pd.DataFrame:
        csv_path = Path(csv_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在：{csv_path}")

        skip_header_rows = 5

        read_attempts = [
            {"sep": ",", "engine": "python"},
            {"sep": ";", "engine": "python"},
            {"sep": "\t", "engine": "python"},
            {"sep": r"\s+", "engine": "python"},
        ]

        for kwargs in read_attempts:
            try:
                temp_df = pd.read_csv(
                    csv_path,
                    skiprows=skip_header_rows,
                    **kwargs,
                )

                if temp_df.empty:
                    continue

                temp_df = temp_df.dropna(axis=0, how="all")
                temp_df = temp_df.dropna(axis=1, how="all")

                numeric_df = temp_df.copy()

                for col in numeric_df.columns:
                    numeric_df[col] = (
                        numeric_df[col]
                        .astype(str)
                        .str.strip()
                        .str.replace(",", "", regex=False)
                    )
                    numeric_df[col] = pd.to_numeric(numeric_df[col], errors="coerce")

                numeric_df = numeric_df.dropna(axis=0, how="all")
                numeric_df = numeric_df.dropna(axis=1, how="all")

                if not numeric_df.empty and numeric_df.shape[1] >= 2:
                    return numeric_df

            except Exception:
                continue

        raise ValueError(
            f"CSV 中没有可绘制的两列数值数据。已跳过前 5 行，但仍未识别到横纵坐标数据：{csv_path}"
        )

    def _label_override_for_path(
            self,
            csv_path: Path,
            label_overrides: Mapping[str | Path, str] | None = None,
    ) -> str | None:
        if not label_overrides:
            return None

        if csv_path in label_overrides:
            return str(label_overrides[csv_path])

        csv_path_text = str(csv_path)
        if csv_path_text in label_overrides:
            return str(label_overrides[csv_path_text])

        for key, value in label_overrides.items():
            try:
                if Path(key) == csv_path:
                    return str(value)
            except Exception:
                continue

        return None

    def make_curve_label(
            self,
            csv_path: str | Path,
            index: int,
            total: int,
            default_single_label: str | None = None,
            label_overrides: Mapping[str | Path, str] | None = None,
    ) -> str:
\
\
\
\
\
           
        csv_path = Path(csv_path)

        override = self._label_override_for_path(csv_path, label_overrides)
        if override:
            return override

        if total == 1 and default_single_label:
            return default_single_label

        if total == 1:
            return "Curve"

        return csv_path.stem or f"Curve {index}"

    def _resolve_c_rate(self, default_single_label: str | None = None) -> float:
\
\
\
\
\
\
           
        if default_single_label is None:
            return 1.0

        text = str(default_single_label).strip()
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
        if not match:
            return 1.0

        try:
            c_rate = float(match.group(0))
        except ValueError:
            return 1.0

        if c_rate <= 0:
            return 1.0

        return c_rate

    def _prepare_series_data(
            self,
            csv_paths: list[str | Path],
            default_single_label: str | None = None,
            label_overrides: Mapping[str | Path, str] | None = None,
    ) -> tuple[list[dict], list[float]]:
        if not csv_paths:
            raise ValueError("未选择 CSV 文件。")

        series_data = []
        x_max_values = []
        total = len(csv_paths)

        for index, csv_path in enumerate(csv_paths, start=1):
            csv_path = Path(csv_path)
            df = self.read_numeric_csv(csv_path)

                                                                                           
                                                   
                                                                                  
            x_raw = df.iloc[:, 0]
            y_raw = df.iloc[:, 1]

            label = self.make_curve_label(
                csv_path=csv_path,
                index=index,
                total=total,
                default_single_label=default_single_label,
                label_overrides=label_overrides,
            )

            x = pd.to_numeric(
                pd.Series(x_raw).reset_index(drop=True),
                errors="coerce",
            )
            y = pd.to_numeric(
                pd.Series(y_raw).reset_index(drop=True),
                errors="coerce",
            )

            valid = x.notna() & y.notna()
            x = x[valid].reset_index(drop=True)
            y = y[valid].reset_index(drop=True)

            if x.empty:
                continue

            c_rate = self._resolve_c_rate(default_single_label)

                                                                       
                                                             
            x_values = x.to_numpy() * c_rate / 3600.0
            y_values = y.to_numpy()

            x_max = float(x_values.max())
            if x_max > 0:
                x_max_values.append(x_max)

            series_data.append(
                {
                    "csv_path": csv_path,
                    "x": x_values,
                    "y": y_values,
                    "label": label,
                }
            )

        if not series_data:
            raise ValueError("CSV 中没有可绘制的数据点。")

        return series_data, x_max_values

    def _finish_plot_style(self, series_data: list[dict], x_max_values: list[float], fixed_y_axis: bool = True):
        self._apply_axes_style()
        self._apply_x_axis_range(x_max_values)

        if fixed_y_axis:
            self._apply_y_axis_range(series_data)

                                                                     
        self._apply_fixed_layout()

    def plot_csv_files(
            self,
            csv_paths: list[str | Path],
            default_single_label: str | None = None,
            label_overrides: Mapping[str | Path, str] | None = None,
    ):
        self.stop_animation()
        series_data, x_max_values = self._prepare_series_data(
            csv_paths=csv_paths,
            default_single_label=default_single_label,
            label_overrides=label_overrides,
        )

        self.ax.clear()

        for series in series_data:
            self.ax.plot(
                series["x"],
                series["y"],
                marker="o",
                markersize=2,
                markeredgewidth=0.4,
                linewidth=0.9,
            )

        self._finish_plot_style(series_data, x_max_values, fixed_y_axis=True)
        self.draw()

    def plot_csv_files_animated(
            self,
            csv_paths: list[str | Path],
            default_single_label: str | None = None,
            label_overrides: Mapping[str | Path, str] | None = None,
            duration_ms: int = 800,
            max_frames: int = 70,
    ):
        self.stop_animation()
        series_data, x_max_values = self._prepare_series_data(
            csv_paths=csv_paths,
            default_single_label=default_single_label,
            label_overrides=label_overrides,
        )

        self.ax.clear()
        self._animation_series = series_data
        self._animation_lines = []

        for series in series_data:
            line, = self.ax.plot(
                [],
                [],
                marker="o",
                markersize=2,
                markeredgewidth=0.4,
                linewidth=0.9,
            )
            self._animation_lines.append(line)

        self._finish_plot_style(series_data, x_max_values, fixed_y_axis=True)
        self.draw()

        max_points = max(len(series["x"]) for series in series_data)
        self._animation_total_frames = max(1, min(int(max_frames), int(max_points)))
        self._animation_frame = 0

        interval_ms = max(16, int(duration_ms / self._animation_total_frames))
        self.animation_timer.start(interval_ms)

    def _advance_animation(self):
        if not self._animation_series or not self._animation_lines:
            self.stop_animation()
            return

        self._animation_frame += 1
        progress = min(1.0, self._animation_frame / max(1, self._animation_total_frames))

        for line, series in zip(self._animation_lines, self._animation_series):
            x = series["x"]
            y = series["y"]
            point_count = max(1, int(math.ceil(len(x) * progress)))
            line.set_data(x[:point_count], y[:point_count])

        self.draw_idle()

        if progress >= 1.0:
            self.animation_timer.stop()

    def plot_csv(self, csv_path: str | Path, default_single_label: str | None = None):
        self.plot_csv_files(
            [csv_path],
            default_single_label=default_single_label,
        )
