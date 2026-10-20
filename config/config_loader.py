from pathlib import Path
from typing import Any, Dict
import copy
import yaml


def load_yaml_file(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML 文件不存在: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML 顶层必须是字典: {path}")

    return data


def deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def load_case_config(
    case_yaml_path: str | Path,
    defaults_yaml_path: str | Path | None = None,
) -> Dict[str, Any]:
    if defaults_yaml_path is not None:
        defaults = load_yaml_file(defaults_yaml_path)
        case_cfg = load_yaml_file(case_yaml_path)
        merged = deep_update(defaults, case_cfg)
        return merged

    return load_yaml_file(case_yaml_path)


def ensure_output_dirs(cfg: Dict[str, Any]) -> None:
\
\
\
\
\
\
\
\
       
    output_dir = Path(cfg["project"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runs").mkdir(parents=True, exist_ok=True)


def get_case_name(cfg: Dict[str, Any]) -> str:
    return cfg["project"]["case_name"]


def get_random_seed(cfg: Dict[str, Any]) -> int:
    return int(cfg["project"]["random_seed"])


def flatten_runtime_params(cfg: dict) -> dict:
    return {
        "case_name": cfg["project"]["case_name"],
        "unit": cfg["geometry"]["unit"],
        "random_seed": cfg["project"]["random_seed"],

        "h": cfg["battery"]["width_h"],
        "d": cfg["battery"]["thickness_d"],
        "L_neg": cfg["battery"]["neg_length"],
        "L_sep": cfg["battery"]["sep_length"],
        "L_pos": cfg["battery"]["pos_length"],

        "neg_active_fraction": cfg["negative_electrode"]["active_fraction"],
        "neg_binder_fraction": cfg["negative_electrode"]["binder_fraction"],
        "neg_particle_mean_diameter": cfg["negative_electrode"]["particle"]["mean_diameter"],
        "neg_particle_dispersion": cfg["negative_electrode"]["particle"]["diameter_dispersion"],
        "neg_particle_lognormal_std": cfg["negative_electrode"]["particle"]["lognormal_std"],
        "neg_binder_width_dispersion": cfg["negative_electrode"]["binder"]["width_dispersion"],
        "neg_binder_lognormal_std": cfg["negative_electrode"]["binder"]["lognormal_std"],
        "neg_max_attempts_per_particle": cfg["negative_electrode"]["packing"]["max_attempts_per_particle"],
        "neg_target_fill_tolerance": cfg["negative_electrode"]["packing"]["target_fill_tolerance"],

        "pos_active_fraction": cfg["positive_electrode"]["active_fraction"],
        "pos_binder_fraction": cfg["positive_electrode"]["binder_fraction"],
        "pos_particle_mean_diameter": cfg["positive_electrode"]["particle"]["mean_diameter"],
        "pos_particle_dispersion": cfg["positive_electrode"]["particle"]["diameter_dispersion"],
        "pos_particle_lognormal_std": cfg["positive_electrode"]["particle"]["lognormal_std"],
        "pos_binder_width_dispersion": cfg["positive_electrode"]["binder"]["width_dispersion"],
        "pos_binder_lognormal_std": cfg["positive_electrode"]["binder"]["lognormal_std"],
        "pos_max_attempts_per_particle": cfg["positive_electrode"]["packing"]["max_attempts_per_particle"],
        "pos_target_fill_tolerance": cfg["positive_electrode"]["packing"]["target_fill_tolerance"],

        "cl_init": cfg["electrochemistry"]["electrolyte"]["cl_init"],
        "e_pert": cfg["electrochemistry"]["perturbation"]["e_pert"],
        "cv_scan_rate_mV_per_s": cfg["electrochemistry"]["cv"]["scan_rate_mV_per_s"],
        "v_max": cfg["electrochemistry"]["cv"]["v_max"],
        "v_min": cfg["electrochemistry"]["cv"]["v_min"],
        "c_rate": cfg["electrochemistry"]["cycling"]["c_rate"],

        "soc0_pos": cfg["electrochemistry"]["positive"]["soc0"],
        "k0_pos": cfg["electrochemistry"]["positive"]["k0"],
        "r_film_pos": cfg["electrochemistry"]["positive"]["r_film"],
        "c_dl_pos": cfg["electrochemistry"]["positive"]["c_dl"],

        "soc0_neg": cfg["electrochemistry"]["negative"]["soc0"],
        "k0_neg": cfg["electrochemistry"]["negative"]["k0"],
        "r_film_neg": cfg["electrochemistry"]["negative"]["r_film"],
        "c_dl_neg": cfg["electrochemistry"]["negative"]["c_dl"],

        "binder_sigma_s": cfg["electrochemistry"]["binder"]["sigma_s"],
    }