from __future__ import annotations

import math
from typing import Optional

import numpy as np


class SamplingError(Exception):
    pass


def compute_min_max_from_dispersion(mean_value: float, dispersion: float) -> tuple[float, float]:
    min_value = mean_value * (1.0 - dispersion)
    max_value = mean_value * (1.0 + dispersion)

    if min_value <= 0:
        raise SamplingError(
            f"根据 mean={mean_value} 和 dispersion={dispersion} 算出的最小值 <= 0，请检查参数。"
        )

    if max_value <= min_value:
        raise SamplingError(
            f"计算得到的 max <= min，请检查参数。min={min_value}, max={max_value}"
        )

    return min_value, max_value


def lognormal_mu_sigma_from_mean_and_logsigma(
    mean_value: float,
    lognormal_sigma: float,
) -> tuple[float, float]:
\
\
\
\
\
\
\
       
    if mean_value <= 0:
        raise SamplingError("mean_value 必须 > 0")
    if lognormal_sigma < 0:
        raise SamplingError("lognormal_sigma 必须 >= 0")

    sigma = lognormal_sigma
    mu = math.log(mean_value) - 0.5 * sigma * sigma
    return mu, sigma


def sample_truncated_lognormal(
    n: int,
    min_value: float,
    max_value: float,
    mean_value: float,
    sd_value: float,
    rng: np.random.Generator,
    max_trials: int = 100000,
) -> np.ndarray:
    if n <= 0:
        raise SamplingError(f"n 必须为正整数，当前 n={n}")
    if min_value <= 0:
        raise SamplingError(f"min_value 必须 > 0，当前 min_value={min_value}")
    if max_value <= min_value:
        raise SamplingError(
            f"max_value 必须大于 min_value，当前 min={min_value}, max={max_value}"
        )
    if mean_value <= 0:
        raise SamplingError(f"mean_value 必须 > 0，当前 mean_value={mean_value}")
    if sd_value < 0:
        raise SamplingError(f"sd_value 必须 >= 0，当前 sd_value={sd_value}")

    mu, sigma = lognormal_mu_sigma_from_mean_and_logsigma(mean_value, sd_value)

    accepted = []
    trials = 0

    while len(accepted) < n:
        remaining = n - len(accepted)
        batch_size = max(remaining * 3, 16)

        samples = rng.lognormal(mean=mu, sigma=sigma, size=batch_size)
        valid = samples[(samples >= min_value) & (samples <= max_value)]
        accepted.extend(valid.tolist())

        trials += batch_size
        if trials > max_trials:
            raise SamplingError(
                "截断 log-normal 采样失败：超过最大尝试次数。"
                f" n={n}, min={min_value}, max={max_value}, mean={mean_value}, sd={sd_value}"
            )

    return np.array(accepted[:n], dtype=float)


def sample_particle_diameters(
    n: int,
    mean_diameter: float,
    diameter_dispersion: float,
    lognormal_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    min_d, max_d = compute_min_max_from_dispersion(mean_diameter, diameter_dispersion)

    return sample_truncated_lognormal(
        n=n,
        min_value=min_d,
        max_value=max_d,
        mean_value=mean_diameter,
        sd_value=lognormal_std,
        rng=rng,
    )


def sample_binder_widths(
    n: int,
    mean_width: float,
    width_dispersion: float,
    lognormal_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    min_w, max_w = compute_min_max_from_dispersion(mean_width, width_dispersion)

    return sample_truncated_lognormal(
        n=n,
        min_value=min_w,
        max_value=max_w,
        mean_value=mean_width,
        sd_value=lognormal_std,
        rng=rng,
    )


def make_rng(seed: Optional[int] = None) -> np.random.Generator:
    return np.random.default_rng(seed)