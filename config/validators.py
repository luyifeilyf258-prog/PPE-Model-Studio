from typing import Any, Dict, List


class ConfigValidationError(Exception):
    pass


def _is_positive(x: Any) -> bool:
    return isinstance(x, (int, float)) and x > 0


def _is_nonnegative(x: Any) -> bool:
    return isinstance(x, (int, float)) and x >= 0


def _is_fraction(x: Any) -> bool:
    return isinstance(x, (int, float)) and 0 <= x <= 1


def _require_keys(d: Dict[str, Any], keys: List[str], prefix: str = "") -> None:
    for key in keys:
        if key not in d:
            raise ConfigValidationError(f"缺少必要字段: {prefix}{key}")


def validate_geometry_unit(cfg: Dict[str, Any]) -> None:
    unit = cfg["geometry"]["unit"]
    if unit != "m":
        raise ConfigValidationError(
            f"当前只允许 geometry.unit='m'，检测到: {unit}"
        )


def validate_battery(cfg: Dict[str, Any]) -> None:
    b = cfg["battery"]
    required = ["width_h", "thickness_d", "neg_length", "sep_length", "pos_length"]
    _require_keys(b, required, prefix="battery.")

    for key in required:
        if not _is_positive(b[key]):
            raise ConfigValidationError(f"battery.{key} 必须 > 0，当前值: {b[key]}")


def validate_electrode_block(cfg: Dict[str, Any], name: str) -> None:
    e = cfg[name]

    _require_keys(
        e,
        ["active_fraction", "binder_fraction", "particle", "binder", "packing", "network"],
        prefix=f"{name}.",
    )

    if not _is_fraction(e["active_fraction"]):
        raise ConfigValidationError(f"{name}.active_fraction 必须在 [0,1]")

    if not _is_fraction(e["binder_fraction"]):
        raise ConfigValidationError(f"{name}.binder_fraction 必须在 [0,1]")

    if e["active_fraction"] + e["binder_fraction"] > 1:
        raise ConfigValidationError(
            f"{name}.active_fraction + {name}.binder_fraction 不能大于 1"
        )


def validate_electrochemistry(cfg: Dict[str, Any]) -> None:
    e = cfg["electrochemistry"]

    _require_keys(
        e,
        ["electrolyte", "perturbation", "cv", "cycling", "positive", "negative", "binder"],
        prefix="electrochemistry.",
    )

    if not _is_positive(e["electrolyte"]["cl_init"]):
        raise ConfigValidationError("electrochemistry.electrolyte.cl_init 必须 > 0")

    if not _is_nonnegative(e["perturbation"]["e_pert"]):
        raise ConfigValidationError("electrochemistry.perturbation.e_pert 必须 >= 0")

    cv = e["cv"]
    if not _is_positive(cv["scan_rate_mV_per_s"]):
        raise ConfigValidationError("electrochemistry.cv.scan_rate_mV_per_s 必须 > 0")

    if not _is_positive(cv["v_max"]):
        raise ConfigValidationError("electrochemistry.cv.v_max 必须 > 0")

    if not _is_positive(cv["v_min"]):
        raise ConfigValidationError("electrochemistry.cv.v_min 必须 > 0")

    if cv["v_max"] <= cv["v_min"]:
        raise ConfigValidationError("electrochemistry.cv.v_max 必须大于 v_min")

    if not _is_positive(e["cycling"]["c_rate"]):
        raise ConfigValidationError("electrochemistry.cycling.c_rate 必须 > 0")

    for side in ["positive", "negative"]:
        s = e[side]
        _require_keys(s, ["soc0", "k0", "r_film", "c_dl"], prefix=f"electrochemistry.{side}.")
        if not _is_fraction(s["soc0"]):
            raise ConfigValidationError(f"electrochemistry.{side}.soc0 必须在 [0,1]")
        if not _is_positive(s["k0"]):
            raise ConfigValidationError(f"electrochemistry.{side}.k0 必须 > 0")
        if not _is_nonnegative(s["r_film"]):
            raise ConfigValidationError(f"electrochemistry.{side}.r_film 必须 >= 0")
        if not _is_nonnegative(s["c_dl"]):
            raise ConfigValidationError(f"electrochemistry.{side}.c_dl 必须 >= 0")

    binder = e["binder"]
    _require_keys(binder, ["sigma_s", "sigma_l"], prefix="electrochemistry.binder.")
    if not _is_positive(binder["sigma_s"]):
        raise ConfigValidationError("electrochemistry.binder.sigma_s 必须 > 0")
    if not _is_positive(binder["sigma_l"]):
        raise ConfigValidationError("electrochemistry.binder.sigma_l 必须 > 0")

def validate_project(cfg: Dict[str, Any]) -> None:
    p = cfg["project"]
    _require_keys(p, ["case_name", "output_dir", "random_seed"], prefix="project.")

    if not isinstance(p["case_name"], str) or not p["case_name"].strip():
        raise ConfigValidationError("project.case_name 必须是非空字符串")

    if not isinstance(p["output_dir"], str) or not p["output_dir"].strip():
        raise ConfigValidationError("project.output_dir 必须是非空字符串")

    if not isinstance(p["random_seed"], int):
        raise ConfigValidationError("project.random_seed 必须是整数")


def validate_build(cfg: Dict[str, Any]) -> None:
    b = cfg["build"]
    _require_keys(
        b,
        ["mode", "save_json", "save_preview_png", "save_java", "run_comsol", "save_mph"],
        prefix="build.",
    )

    if b["mode"] not in {"geometry_only", "liion_framework"}:
        raise ConfigValidationError("build.mode 只能是 geometry_only 或 liion_framework")

def validate_comsol(cfg: Dict[str, Any]) -> None:
    comsol = cfg.get("comsol")
    if comsol is None:
        return

    if not isinstance(comsol, dict):
        raise ConfigValidationError("comsol 必须是字典")

    java_cfg = comsol.get("java")
    if java_cfg is not None:
        if not isinstance(java_cfg, dict):
            raise ConfigValidationError("comsol.java 必须是字典")

        if "java_output_dir" in java_cfg:
            value = java_cfg["java_output_dir"]
            if not isinstance(value, str) or not value.strip():
                raise ConfigValidationError("comsol.java.java_output_dir 如果存在，必须是非空字符串")

        if "class_name" in java_cfg:
            value = java_cfg["class_name"]
            if not isinstance(value, str) or not value.strip():
                raise ConfigValidationError("comsol.java.class_name 如果存在，必须是非空字符串")

    mph_cfg = comsol.get("mph")
    if mph_cfg is not None:
        if not isinstance(mph_cfg, dict):
            raise ConfigValidationError("comsol.mph 必须是字典")

        if "mph_output_dir" in mph_cfg:
            value = mph_cfg["mph_output_dir"]
            if not isinstance(value, str) or not value.strip():
                raise ConfigValidationError("comsol.mph.mph_output_dir 如果存在，必须是非空字符串")


def validate_advanced_settings(cfg: Dict[str, Any]) -> None:
    advanced = cfg.get("advanced_settings")
    if advanced is None:
        return

    if not isinstance(advanced, dict):
        raise ConfigValidationError("advanced_settings 必须是字典")

    allowed_mesh = {
        "extremely_fine": 1,
        "extra_fine": 2,
        "finer": 3,
        "fine": 4,
        "normal": 5,
        "coarse": 6,
        "coarser": 7,
        "extremely_coarse": 8,
    }

    mesh_size = advanced.get("mesh_size", "normal")
    if mesh_size not in allowed_mesh:
        raise ConfigValidationError(
            "advanced_settings.mesh_size 必须是 extremely_fine、extra_fine、finer、fine、normal、coarse、coarser 或 extremely_coarse"
        )

    mesh_hauto = advanced.get("mesh_hauto", allowed_mesh[mesh_size])
    if not isinstance(mesh_hauto, int) or not (1 <= mesh_hauto <= 8):
        raise ConfigValidationError("advanced_settings.mesh_hauto 必须是 1 到 8 的整数")

    transient_max_iter = advanced.get("transient_max_iter", 100)
    if not isinstance(transient_max_iter, int) or transient_max_iter <= 0:
        raise ConfigValidationError("advanced_settings.transient_max_iter 必须是正整数")

    stationary_max_iter = advanced.get("stationary_max_iter", 100)
    if not isinstance(stationary_max_iter, int) or stationary_max_iter <= 0:
        raise ConfigValidationError("advanced_settings.stationary_max_iter 必须是正整数")

    cutoff_voltage = advanced.get("cutoff_voltage", 3.3)
    if not _is_positive(cutoff_voltage):
        raise ConfigValidationError("advanced_settings.cutoff_voltage 必须 > 0")

    time_step = advanced.get("time_step", 2.0)
    if not _is_positive(time_step):
        raise ConfigValidationError("advanced_settings.time_step 必须 > 0")

def validate_config(cfg: Dict[str, Any]) -> None:
    _require_keys(cfg, ["project", "build", "geometry", "battery", "negative_electrode", "positive_electrode", "electrochemistry"], prefix="")

    validate_project(cfg)
    validate_build(cfg)
    validate_geometry_unit(cfg)
    validate_battery(cfg)
    validate_electrode_block(cfg, "negative_electrode")
    validate_electrode_block(cfg, "positive_electrode")
    validate_electrochemistry(cfg)
    validate_comsol(cfg)
    validate_advanced_settings(cfg)
