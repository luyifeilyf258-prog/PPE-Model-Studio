from __future__ import annotations

from pathlib import Path
from typing import Any, List

from core.geometry_model import ModelCase, Particle, BinderBridge, RegionBlock

def _java_identifier_from_filename(stem: str) -> str:
    cleaned = []
    for ch in stem:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")

    name = "".join(cleaned).strip("_")
    if not name:
        name = "GeneratedModel"

    if name[0].isdigit():
        name = f"Model_{name}"

    return name

class JavaWriterError(Exception):
    pass


def _fmt(x: float) -> str:
    return f"{float(x):.12e}"


def _find_region(case: ModelCase, role: str) -> RegionBlock:
    for region in case.regions:
        if region.role == role:
            return region
    raise JavaWriterError(f"未找到区域 role={role}")


def _method_header(name: str) -> List[str]:
    return [f"  private static void {name}(Model model) {{"]


def _method_footer() -> List[str]:
    return ["  }", ""]


def _chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _require_case_value(case: ModelCase, key: str) -> Any:
    if key in case.electrochem_params:
        return case.electrochem_params[key]
    if key in case.battery_params:
        return case.battery_params[key]
    raise JavaWriterError(f"ModelCase 中缺少必要参数: {key}")


def _build_boundary_cumulative_selections_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildBoundaryCumulativeSelections"))

    tags = [
        "sel_neg_particle_electrolyte_bnd",
        "sel_pos_particle_electrolyte_bnd",
        "sel_neg_collector_bnd",
        "sel_pos_collector_bnd",
    ]

    for tag in tags:
        lines.extend([
            f'    model.component("comp1").geom("geom1").selection().create("{tag}", "CumulativeSelection");',
            f'    model.component("comp1").geom("geom1").selection("{tag}").label("{tag}");',
            "",
        ])

    lines.extend(_method_footer())
    return lines


def _build_domain_cumulative_selections_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildDomainCumulativeSelections"))

    tags = [
        "sel_neg_region",
        "sel_sep_region",
        "sel_pos_region",
        "sel_electrolyte",
        "sel_neg_particles",
        "sel_pos_particles",
        "sel_all_particles",
        "sel_neg_binders",
        "sel_pos_binders",
        "sel_all_binders",
    ]

    for tag in tags:
        lines.extend([
            f'    model.component("comp1").geom("geom1").selection().create("{tag}", "CumulativeSelection");',
            f'    model.component("comp1").geom("geom1").selection("{tag}").label("{tag}");',
            "",
        ])

    lines.extend(_method_footer())
    return lines


def _build_regions_method(case: ModelCase) -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildRegions"))

    region_name_map = {
        "negative": "r_neg",
        "separator": "r_sep",
        "positive": "r_pos",
    }
    region_contrib_map = {
        "negative": "sel_neg_region",
        "separator": "sel_sep_region",
        "positive": "sel_pos_region",
    }

    for role in ["negative", "separator", "positive"]:
        region = _find_region(case, role)
        feat_name = region_name_map[role]
        contrib_tag = region_contrib_map[role]

        lines.extend([
            f'    model.component("comp1").geom("geom1").create("{feat_name}", "Rectangle");',
            f'    model.component("comp1").geom("geom1").feature("{feat_name}").set("pos", new double[]{{{_fmt(region.x)}, {_fmt(region.y)}}});',
            f'    model.component("comp1").geom("geom1").feature("{feat_name}").set("size", new double[]{{{_fmt(region.width)}, {_fmt(region.height)}}});',
            f'    model.component("comp1").geom("geom1").feature("{feat_name}").set("selresult", "off");',
            f'    model.component("comp1").geom("geom1").feature("{feat_name}").label("{feat_name}");',
            "",
        ])

    lines.extend(_method_footer())
    return lines


def _build_particle_method(method_name: str, particles: List[Particle]) -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header(method_name))

    for p in particles:
        lines.extend([
            f'    model.component("comp1").geom("geom1").create("{p.name}", "Circle");',
            f'    model.component("comp1").geom("geom1").feature("{p.name}").set("base", "center");',
            f'    model.component("comp1").geom("geom1").feature("{p.name}").set("r", {_fmt(p.radius)});',
            f'    model.component("comp1").geom("geom1").feature("{p.name}").set("pos", new double[]{{{_fmt(p.center.x)}, {_fmt(p.center.y)}}});',
            f'    model.component("comp1").geom("geom1").feature("{p.name}").set("selresult", "off");',
            f'    model.component("comp1").geom("geom1").feature("{p.name}").label("{p.name}");',
            "",
        ])

    lines.extend(_method_footer())
    return lines


def _binder_lines_for_one(b: BinderBridge) -> List[str]:
    rot_deg = -b.rotation_deg

    return [
        f'    model.component("comp1").geom("geom1").create("{b.name}", "Rectangle");',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").set("base", "center");',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").set("size", new double[]{{{_fmt(b.width)}, {_fmt(b.length)}}});',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").set("pos", new double[]{{{_fmt(b.center.x)}, {_fmt(b.center.y)}}});',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").set("rot", {_fmt(rot_deg)});',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").set("selresult", "off");',
        f'    model.component("comp1").geom("geom1").feature("{b.name}").label("{b.name}");',
        "",
    ]


def _build_binder_methods(group_name: str, bridges: List[BinderBridge], chunk_size: int = 120) -> List[str]:
    lines: List[str] = []
    chunks = _chunk_list(bridges, chunk_size)

    if not chunks:
        lines.extend(_method_header(group_name))
        lines.extend(_method_footer())
        return lines

    for idx, chunk in enumerate(chunks, start=1):
        part_name = f"{group_name}_part{idx}"
        lines.extend(_method_header(part_name))
        for b in chunk:
            lines.extend(_binder_lines_for_one(b))
        lines.extend(_method_footer())

    lines.extend(_method_header(group_name))
    for idx in range(1, len(chunks) + 1):
        lines.append(f"    {group_name}_part{idx}(model);")
    lines.extend(_method_footer())

    return lines


def _write_union(
    feature_name: str,
    input_names: List[str],
    label: str,
    keep_input: bool = False,
    selresultshow: str = "dom",
    contributeto: str | None = None,
    intbnd: bool = False,
) -> List[str]:
    if not input_names:
        return []

    quoted = ", ".join([f'"{name}"' for name in input_names])

    lines = [
        f'    model.component("comp1").geom("geom1").create("{feature_name}", "Union");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input").set(new String[]{{{quoted}}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("intbnd", {"true" if intbnd else "false"});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("keep", {"true" if keep_input else "false"});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresult", "on");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresultshow", "{selresultshow}");',
    ]
    if contributeto is not None:
        lines.append(
            f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("contributeto", "{contributeto}");'
        )
    lines.append(f'    model.component("comp1").geom("geom1").feature("{feature_name}").label("{label}");')
    lines.append("")
    return lines


def _write_difference(
    feature_name: str,
    input_name: str,
    tool_name: str,
    label: str,
    keep_input: bool = False,
    keep_subtract: bool = False,
    selresultshow: str = "dom",
    contributeto: str | None = None,
) -> List[str]:
    lines = [
        f'    model.component("comp1").geom("geom1").create("{feature_name}", "Difference");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input").set(new String[]{{"{input_name}"}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input2").set(new String[]{{"{tool_name}"}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("keep", {"true" if keep_input else "false"});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("keepsubtract", {"true" if keep_subtract else "false"});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresult", "on");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresultshow", "{selresultshow}");',
    ]
    if contributeto is not None:
        lines.append(
            f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("contributeto", "{contributeto}");'
        )
    lines.append(f'    model.component("comp1").geom("geom1").feature("{feature_name}").label("{label}");')
    lines.append("")
    return lines


def _write_convert_to_curve(
    feature_name: str,
    input_name: str,
    label: str,
    keep_input: bool = False,
) -> List[str]:
    return [
        f'    model.component("comp1").geom("geom1").create("{feature_name}", "ConvertToCurve");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input").set(new String[]{{"{input_name}"}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("keep", {"true" if keep_input else "false"});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresult", "on");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresultshow", "bnd");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").label("{label}");',
        "",
    ]


def _write_intersection(
    feature_name: str,
    input_names: List[str],
    label: str,
    contributeto: str | None = None,
) -> List[str]:
    quoted = ", ".join([f'"{name}"' for name in input_names])

    lines = [
        f'    model.component("comp1").geom("geom1").create("{feature_name}", "Intersection");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input").set(new String[]{{{quoted}}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresult", "on");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresultshow", "bnd");',
    ]
    if contributeto is not None:
        lines.append(
            f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("contributeto", "{contributeto}");'
        )
    lines.append(f'    model.component("comp1").geom("geom1").feature("{feature_name}").label("{label}");')
    lines.append("")
    return lines


def _write_copy(
    feature_name: str,
    input_names: List[str],
    label: str,
    contributeto: str | None = None,
) -> List[str]:
    if not input_names:
        return []

    quoted = ", ".join([f'"{name}"' for name in input_names])

    lines = [
        f'    model.component("comp1").geom("geom1").create("{feature_name}", "Copy");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").selection("input").set(new String[]{{{quoted}}});',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresult", "on");',
        f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("selresultshow", "dom");',
    ]
    if contributeto is not None:
        lines.append(
            f'    model.component("comp1").geom("geom1").feature("{feature_name}").set("contributeto", "{contributeto}");'
        )
    lines.append(f'    model.component("comp1").geom("geom1").feature("{feature_name}").label("{label}");')
    lines.append("")
    return lines


def _build_particle_curve_source_unions_method(case: ModelCase) -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildParticleCurveSourceUnions"))

    neg_particle_names = [p.name for p in case.negative_particles]
    pos_particle_names = [p.name for p in case.positive_particles]

    lines.extend(_write_union(
        "uni_neg_particles_curve_src",
        neg_particle_names,
        "uni_neg_particles_curve_src",
        keep_input=True,
    ))
    lines.extend(_write_union(
        "uni_pos_particles_curve_src",
        pos_particle_names,
        "uni_pos_particles_curve_src",
        keep_input=True,
    ))

    lines.extend(_method_footer())
    return lines


def _build_domain_booleans_method(case: ModelCase) -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildDomainBooleans"))

    neg_particle_names = [p.name for p in case.negative_particles]
    pos_particle_names = [p.name for p in case.positive_particles]
    neg_binder_names = [b.name for b in case.negative_binders]
    pos_binder_names = [b.name for b in case.positive_binders]

    lines.extend(_write_union(
        "uni_neg_particles",
        neg_particle_names,
        "uni_neg_particles",
        keep_input=True,
        contributeto="sel_neg_particles",
    ))
    lines.extend(_write_union(
        "uni_pos_particles",
        pos_particle_names,
        "uni_pos_particles",
        keep_input=True,
        contributeto="sel_pos_particles",
    ))

                    
    lines.extend(_write_union(
        "uni_all_particles",
        ["uni_neg_particles", "uni_pos_particles"],
        "uni_all_particles",
        keep_input=True,
        contributeto="sel_all_particles",
    ))

    lines.extend(_write_copy(
        "copy_neg_particles_for_solid",
        ["uni_neg_particles"],
        "copy_neg_particles_for_solid",
    ))
    lines.extend(_write_copy(
        "copy_pos_particles_for_solid",
        ["uni_pos_particles"],
        "copy_pos_particles_for_solid",
    ))

    lines.extend(_write_union(
        "uni_neg_binders_raw",
        neg_binder_names,
        "uni_neg_binders_raw",
        keep_input=False,
    ))
    lines.extend(_write_union(
        "uni_pos_binders_raw",
        pos_binder_names,
        "uni_pos_binders_raw",
        keep_input=False,
    ))

    all_binder_inputs: List[str] = []

    if neg_particle_names and neg_binder_names:
        lines.extend(_write_difference(
            "dif_neg_binders",
            "uni_neg_binders_raw",
            "uni_neg_particles",
            "dif_neg_binders",
            keep_input=False,
            keep_subtract=True,
            contributeto="sel_neg_binders",
        ))
        all_binder_inputs.append("dif_neg_binders")

    if pos_particle_names and pos_binder_names:
        lines.extend(_write_difference(
            "dif_pos_binders",
            "uni_pos_binders_raw",
            "uni_pos_particles",
            "dif_pos_binders",
            keep_input=False,
            keep_subtract=True,
            contributeto="sel_pos_binders",
        ))
        all_binder_inputs.append("dif_pos_binders")

    if all_binder_inputs:
        lines.extend(_write_union(
            "uni_all_binders",
            all_binder_inputs,
            "uni_all_binders",
            keep_input=True,
            contributeto="sel_all_binders",
        ))

    lines.extend(_write_union(
        "uni_cell_regions",
        ["r_neg", "r_sep", "r_pos"],
        "uni_cell_regions",
        keep_input=True,
        intbnd=True,
    ))

    solid_inputs = ["copy_neg_particles_for_solid", "copy_pos_particles_for_solid"]
    if neg_particle_names and neg_binder_names:
        solid_inputs.append("dif_neg_binders")
    if pos_particle_names and pos_binder_names:
        solid_inputs.append("dif_pos_binders")

    lines.extend(_write_copy(
        "copy_solid_all",
        solid_inputs,
        "copy_solid_all",
    ))

    lines.extend(_write_difference(
        "dif_electrolyte",
        "uni_cell_regions",
        "copy_solid_all",
        "dif_electrolyte",
        keep_input=True,
        contributeto="sel_electrolyte",
    ))

    lines.extend(_method_footer())
    return lines

def _build_region_curve_geometries_method() -> List[str]:
\
\
\
\
       
    lines: List[str] = []
    lines.extend(_method_header("buildRegionCurveGeometries"))

    lines.extend([
        '    model.component("comp1").geom("geom1").create("ccur_cell_regions", "ConvertToCurve");',
        '    model.component("comp1").geom("geom1").feature("ccur_cell_regions").selection("input").set(new String[]{"uni_cell_regions"});',
        '    model.component("comp1").geom("geom1").feature("ccur_cell_regions").set("selresult", "on");',
        '    model.component("comp1").geom("geom1").feature("ccur_cell_regions").set("selresultshow", "bnd");',
        '    model.component("comp1").geom("geom1").feature("ccur_cell_regions").label("ccur_cell_regions");',
        "",
    ])

    lines.extend(_method_footer())
    return lines


def _build_collector_strip_rectangles_method(case: ModelCase) -> List[str]:
\
\
\
       
    lines: List[str] = []
    lines.extend(_method_header("buildCollectorStripRectangles"))
    lines.extend(_method_footer())
    return lines

def _build_collector_boundary_geometries_method(case: ModelCase) -> List[str]:
\
\
\
       
    lines: List[str] = []
    lines.extend(_method_header("buildCollectorBoundaryGeometries"))

    neg = _find_region(case, "negative")
    pos = _find_region(case, "positive")

    neg_dy = min(1.0e-7, 0.02 * neg.height)
    pos_dy = min(1.0e-7, 0.02 * pos.height)

    neg_xmin = neg.x
    neg_xmax = neg.x + neg.width
    neg_ymin = neg.y - neg_dy
    neg_ymax = neg.y + neg_dy

    pos_top = pos.y + pos.height
    pos_xmin = pos.x
    pos_xmax = pos.x + pos.width
    pos_ymin = pos_top - pos_dy
    pos_ymax = pos_top + pos_dy

    lines.extend([
        '    model.component("comp1").geom("geom1").create("gboxsel_neg_collector", "BoxSelection");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("entitydim", 1);',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("condition", "inside");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("inputent", "selections");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("input", new String[]{"ccur_cell_regions"});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("xmin", {_fmt(neg_xmin)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("xmax", {_fmt(neg_xmax)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("ymin", {_fmt(neg_ymin)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("ymax", {_fmt(neg_ymax)});',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("selshow", "on");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").set("contributeto", "sel_neg_collector_bnd");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_neg_collector").label("gboxsel_neg_collector");',
        "",

        '    model.component("comp1").geom("geom1").create("gboxsel_pos_collector", "BoxSelection");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("entitydim", 1);',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("condition", "inside");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("inputent", "selections");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("input", new String[]{"ccur_cell_regions"});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("xmin", {_fmt(pos_xmin)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("xmax", {_fmt(pos_xmax)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("ymin", {_fmt(pos_ymin)});',
        f'    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("ymax", {_fmt(pos_ymax)});',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("selshow", "on");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").set("contributeto", "sel_pos_collector_bnd");',
        '    model.component("comp1").geom("geom1").feature("gboxsel_pos_collector").label("gboxsel_pos_collector");',
        "",
    ])

    lines.extend(_method_footer())
    return lines

def _build_particle_electrolyte_boundary_geometries_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildParticleElectrolyteBoundaryGeometries"))

    lines.extend(_write_convert_to_curve(
        "ccur_neg_particles",
        "uni_neg_particles_curve_src",
        "ccur_neg_particles",
        keep_input=True,
    ))
    lines.extend(_write_convert_to_curve(
        "ccur_pos_particles",
        "uni_pos_particles_curve_src",
        "ccur_pos_particles",
        keep_input=True,
    ))
    lines.extend(_write_convert_to_curve(
        "ccur_electrolyte",
        "dif_electrolyte",
        "ccur_electrolyte",
        keep_input=True,
    ))

    lines.extend(_write_intersection(
        "int_neg_particle_electrolyte",
        ["ccur_neg_particles", "ccur_electrolyte"],
        "int_neg_particle_electrolyte",
        contributeto="sel_neg_particle_electrolyte_bnd",
    ))
    lines.extend(_write_intersection(
        "int_pos_particle_electrolyte",
        ["ccur_pos_particles", "ccur_electrolyte"],
        "int_pos_particle_electrolyte",
        contributeto="sel_pos_particle_electrolyte_bnd",
    ))

    lines.extend(_method_footer())
    return lines

def _build_final_component_selections_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildFinalComponentSelections"))

    lines.extend([
                                       
                                 
                                       
        '    model.component("comp1").selection().create("sel_electrolyte_dom_final", "Union");',
        '    model.component("comp1").selection("sel_electrolyte_dom_final").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_electrolyte_dom_final").set("input", new String[]{"geom1_dif_electrolyte_dom"});',
        '    model.component("comp1").selection("sel_electrolyte_dom_final").label("Electrolyte domains final");',
        "",

        '    model.component("comp1").selection().create("sel_neg_particles", "Union");',
        '    model.component("comp1").selection("sel_neg_particles").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_neg_particles").set("input", new String[]{"geom1_uni_neg_particles_dom"});',
        '    model.component("comp1").selection("sel_neg_particles").label("Negative particle domains final");',
        "",

        '    model.component("comp1").selection().create("sel_pos_particles", "Union");',
        '    model.component("comp1").selection("sel_pos_particles").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_pos_particles").set("input", new String[]{"geom1_uni_pos_particles_dom"});',
        '    model.component("comp1").selection("sel_pos_particles").label("Positive particle domains final");',
        "",

        '    model.component("comp1").selection().create("sel_neg_binders", "Union");',
        '    model.component("comp1").selection("sel_neg_binders").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_neg_binders").set("input", new String[]{"geom1_dif_neg_binders_dom"});',
        '    model.component("comp1").selection("sel_neg_binders").label("Negative binder domains final");',
        "",

        '    model.component("comp1").selection().create("sel_pos_binders", "Union");',
        '    model.component("comp1").selection("sel_pos_binders").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_pos_binders").set("input", new String[]{"geom1_dif_pos_binders_dom"});',
        '    model.component("comp1").selection("sel_pos_binders").label("Positive binder domains final");',
        "",

        '    model.component("comp1").selection().create("sel_all_particles", "Union");',
        '    model.component("comp1").selection("sel_all_particles").geom("geom1", 2);',
        '    model.component("comp1").selection("sel_all_particles").set("input", new String[]{"geom1_uni_all_particles_dom"});',
        '    model.component("comp1").selection("sel_all_particles").label("All particle domains final");',
        "",

                                       
                                   
                                       
        '    model.component("comp1").selection().create("sel_neg_collector_bnd", "Union");',
        '    model.component("comp1").selection("sel_neg_collector_bnd").geom("geom1", 1);',
        '    model.component("comp1").selection("sel_neg_collector_bnd").set("input", new String[]{"geom1_gboxsel_neg_collector"});',
        '    model.component("comp1").selection("sel_neg_collector_bnd").label("Negative collector boundary final");',
        "",

        '    model.component("comp1").selection().create("sel_pos_collector_bnd", "Union");',
        '    model.component("comp1").selection("sel_pos_collector_bnd").geom("geom1", 1);',
        '    model.component("comp1").selection("sel_pos_collector_bnd").set("input", new String[]{"geom1_gboxsel_pos_collector"});',
        '    model.component("comp1").selection("sel_pos_collector_bnd").label("Positive collector boundary final");',
        "",

        '    model.component("comp1").selection().create("sel_neg_particle_electrolyte_bnd", "Union");',
        '    model.component("comp1").selection("sel_neg_particle_electrolyte_bnd").geom("geom1", 1);',
        '    model.component("comp1").selection("sel_neg_particle_electrolyte_bnd").set("input", new String[]{"geom1_int_neg_particle_electrolyte_bnd"});',
        '    model.component("comp1").selection("sel_neg_particle_electrolyte_bnd").label("Negative particle-electrolyte boundary final");',
        "",

        '    model.component("comp1").selection().create("sel_pos_particle_electrolyte_bnd", "Union");',
        '    model.component("comp1").selection("sel_pos_particle_electrolyte_bnd").geom("geom1", 1);',
        '    model.component("comp1").selection("sel_pos_particle_electrolyte_bnd").set("input", new String[]{"geom1_int_pos_particle_electrolyte_bnd"});',
        '    model.component("comp1").selection("sel_pos_particle_electrolyte_bnd").label("Positive particle-electrolyte boundary final");',
        "",
    ])

    lines.extend(_method_footer())
    return lines

def _sel_tag(name: str) -> str:
    return f'geom1_{name}_dom'

def _build_global_parameters_method(case: ModelCase) -> List[str]:
    bp = case.battery_params
    ep = case.electrochem_params

    lines: List[str] = []
    lines.extend(_method_header("buildGlobalParameters"))

    lines.extend([
        f'    model.param().set("H_ele", "{bp["h"]}[m]");',
        '    model.param().descr("H_ele", "电池宽度");',

        f'    model.param().set("D_ele", "{bp["d"]}[m]");',
        '    model.param().descr("D_ele", "电池厚度");',

        f'    model.param().set("L_neg", "{bp["L_neg"]}[m]");',
        '    model.param().descr("L_neg", "负极长度");',

        f'    model.param().set("L_sep", "{bp["L_sep"]}[m]");',
        '    model.param().descr("L_sep", "隔膜长度");',

        f'    model.param().set("L_pos", "{bp["L_pos"]}[m]");',
        '    model.param().descr("L_pos", "正极长度");',

        f'    model.param().set("ephn", "{ep["ephn"]}");',
        '    model.param().descr("ephn", "负极活性物质比例");',

        f'    model.param().set("ephp", "{ep["ephp"]}");',
        '    model.param().descr("ephp", "正极活性物质比例");',

        f'    model.param().set("cl_init", "{ep["cl_init"]}[mol/m^3]");',
        '    model.param().descr("cl_init", "初始电解质盐浓度");',

        f'    model.param().set("C", "{ep["c_rate"]}");',
        '    model.param().descr("C", "充放电循环倍率");',

        f'    model.param().set("soc0_pos", "{ep["soc0_pos"]}");',
        '    model.param().descr("soc0_pos", "正极初始荷电状态");',

        f'    model.param().set("k_pos", "{ep["k0_pos"]}[mol/m^2/s]");',
        '    model.param().descr("k_pos", "正极交换电流");',

        f'    model.param().set("Rfilm_pos", "{ep["r_film_pos"]}[ohm*m^2]");',
        '    model.param().descr("Rfilm_pos", "正极膜阻");',

        f'    model.param().set("cdl_pos", "{ep["c_dl_pos"]}[F/m^2]");',
        '    model.param().descr("cdl_pos", "正极双电层电容");',

        f'    model.param().set("soc0_neg", "{ep["soc0_neg"]}");',
        '    model.param().descr("soc0_neg", "负极初始荷电状态");',

        f'    model.param().set("k_neg", "{ep["k0_neg"]}[mol/m^2/s]");',
        '    model.param().descr("k_neg", "负极交换电流");',

        f'    model.param().set("Rfilm_neg", "{ep["r_film_neg"]}[ohm*m^2]");',
        '    model.param().descr("Rfilm_neg", "负极膜阻");',

        f'    model.param().set("cdl_neg", "{ep["c_dl_neg"]}[F/m^2]");',
        '    model.param().descr("cdl_neg", "负极双电层电容");',

        '    model.param().set("D", "2.2/5.5*10^(-10)");',
        '    model.param().set("T", "298.15[K]");',
        '    model.param().set("max", "35000*0.95[mol/m^3]");',
        "",
    ])

    lines.extend(_method_footer())
    return lines

def _build_derived_variables_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildDerivedVariables"))

    lines.extend([
        '    model.component("comp1").variable().create("var1");',
        '    model.component("comp1").variable("var1").label("derived_vars");',
        "",

        '    model.component("comp1").variable("var1").set("i0_pos", "k_pos*F_const*mat3.eeq.cEeqref/2[mol/m^3]*1000^0.5*2");',
        '    model.component("comp1").variable("var1").descr("i0_pos", "正极交换电流");',

        '    model.component("comp1").variable("var1").set("i0_neg", "k_neg*F_const*mat2.eeq.cEeqref/2[mol/m^3]*1000^0.5");',
        '    model.component("comp1").variable("var1").descr("i0_neg", "负极交换电流");',

        '    model.component("comp1").variable("var1").set("csinit_neg", "soc0_neg*mat2.eeq.cEeqref");',
        '    model.component("comp1").variable("var1").descr("csinit_neg", "初始负极浓度");',

        '    model.component("comp1").variable("var1").set("csinit_pos", "soc0_pos*mat3.eeq.cEeqref");',
        '    model.component("comp1").variable("var1").descr("csinit_pos", "初始正极浓度");',

        '    model.component("comp1").variable("var1").set("E_cell_init", "mat3.def.Eeq(soc0_pos)-mat2.def.Eeq(soc0_neg)");',
        '    model.component("comp1").variable("var1").descr("E_cell_init", "初始电压");',

        '    model.component("comp1").variable("var1").set("phil_init", "-mat2.def.Eeq(soc0_neg)");',
        '    model.component("comp1").variable("var1").descr("phil_init", "初始电解质电位");',

        '    model.component("comp1").variable("var1").set("i_0", "((1-soc0_pos)*mat3.eeq.cEeqref*L_pos*H_ele*D_ele*ephp)*F_const/1[h]");',
        '    model.component("comp1").variable("var1").descr("i_0", "电流");',
        "",
    ])

    lines.extend(_method_footer())
    return lines


def _build_liion_parameterized_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildLiionParameterized"))

    lines.extend([
        '    model.component("comp1").physics().create("liion", "LithiumIonBatteryMPH", "geom1");',
        '    model.component("comp1").physics("liion").label("锂离子电池");',
        '    model.component("comp1").physics("liion").prop("d").set("d", "D_ele");',
        "",
        '    model.component("comp1").physics("liion").feature("init1").label("负极及电解液初始值");',
        '    model.component("comp1").physics("liion").feature("init1").set("phil", "phil_init");',
        '    model.component("comp1").physics("liion").feature("init1").set("cl", "cl_init");',
        "",
        '    model.component("comp1").physics("liion").create("init2", "init", 2);',
        '    model.component("comp1").physics("liion").feature("init2").label("正极初始值");',
        '    model.component("comp1").physics("liion").feature("init2").selection().named("geom1_uni_pos_particles_dom");',
        '    model.component("comp1").physics("liion").feature("init2").set("phil", "phil_init");',
        '    model.component("comp1").physics("liion").feature("init2").set("cl", "cl_init");',
        '    model.component("comp1").physics("liion").feature("init2").set("phis", "E_cell_init");',
        "",
        '    model.component("comp1").physics("liion").create("bei1", "InternalElectrodeSurface", 1);',
        '    model.component("comp1").physics("liion").feature("bei1").label("内部电极表面_正极");',
        '    model.component("comp1").physics("liion").feature("bei1").selection().named("geom1_int_pos_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("liion").feature("bei1").set("FilmResistanceType", "SurfaceResistance");',
        '    model.component("comp1").physics("liion").feature("bei1").set("Rf", "Rfilm_pos");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("MaterialOption", "mat3");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("ElectrodeKinetics", "ButlerVolmer");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("i0", "i0_pos");',
        "",

        '    model.component("comp1").physics("liion").feature().duplicate("bei2", "bei1");',
        '    model.component("comp1").physics("liion").feature("bei2").label("内部电极表面_负极");',
        '    model.component("comp1").physics("liion").feature("bei2").selection().named("geom1_int_neg_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("liion").feature("bei2").set("Rf", "Rfilm_neg");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("MaterialOption", "mat2");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("ElectrodeKinetics", "LithiumInsertion");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("i0_ref", "i0_neg");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("i0", "i0_neg");',
        "",
        '    model.component("comp1").physics("liion").create("pce1", "PorousElectrode", 2);',
        '    model.component("comp1").physics("liion").feature("pce1").label("多孔电极_正极");',
        '    model.component("comp1").physics("liion").feature("pce1").selection().named("geom1_uni_pos_particles_dom");',
        "",
        '    model.component("comp1").physics("liion").feature().duplicate("pce2", "pce1");',
        '    model.component("comp1").physics("liion").feature("pce2").label("多孔电极_负极");',
        '    model.component("comp1").physics("liion").feature("pce2").selection().named("geom1_uni_neg_particles_dom");',
        "",
        '    model.component("comp1").physics("liion").create("egnd1", "ElectricGround", 1);',
        '    model.component("comp1").physics("liion").feature("egnd1").label("负极接地");',
        '    model.component("comp1").physics("liion").feature("egnd1").selection().named("geom1_gboxsel_neg_collector");',
        "",
        '    model.component("comp1").physics("liion").create("pot1", "ElectricPotential", 1);',
        '    model.component("comp1").physics("liion").feature("pot1").label("阻抗");',
        '    model.component("comp1").physics("liion").feature("pot1").selection().named("geom1_gboxsel_pos_collector");',
        '    model.component("comp1").physics("liion").feature("pot1").set("phisbnd", "E_cell_init");',
        '    model.component("comp1").physics("liion").feature("pot1").create("hp1", "HarmonicPerturbation", 1);',
        '    model.component("comp1").physics("liion").feature("pot1").feature("hp1").set("deltaphis", "E_pert");',
        "",
        '    model.component("comp1").physics("liion").create("pot2", "ElectricPotential", 1);',
        '    model.component("comp1").physics("liion").feature("pot2").label("循环伏安");',
        '    model.component("comp1").physics("liion").feature("pot2").selection().named("geom1_gboxsel_pos_collector");',
        '    model.component("comp1").physics("liion").feature("pot2").set("phisbnd", "wv1(t/1[s]-(E_cell_init-V_min)/omega[s])+(V_min+V_max)/2");',
        "",
        '    model.component("comp1").physics("liion").create("ec1", "ElectrodeCurrent", 1);',
        '    model.component("comp1").physics("liion").feature("ec1").label("放电");',
        '    model.component("comp1").physics("liion").feature("ec1").selection().named("geom1_gboxsel_pos_collector");',
        '    model.component("comp1").physics("liion").feature("ec1").set("Its", "-i_0*C");',
        '    model.component("comp1").physics("liion").feature("ec1").set("phis0init", "E_cell_init");',
        "",
        '    model.component("comp1").physics("liion").create("cdc1", "ChargeDischargeCycling", 1);',
        '    model.component("comp1").physics("liion").feature("cdc1").label("充放电循环");',
        '    model.component("comp1").physics("liion").feature("cdc1").selection().named("geom1_gboxsel_pos_collector");',
        '    model.component("comp1").physics("liion").feature("cdc1").set("Vmin", "V_min");',
        '    model.component("comp1").physics("liion").feature("cdc1").set("Vmax", "V_max");',
        '    model.component("comp1").physics("liion").feature("cdc1").set("Idch", "-i_0*C");',
        '    model.component("comp1").physics("liion").feature("cdc1").set("Ich", "i_0*C");',
        '    model.component("comp1").physics("liion").feature("cdc1").set("phis0init", "E_cell_init");',
        "",
    ])

    lines.extend(_method_footer())
    return lines


NMC_333_DATA = """0,2.63,-5.62
0,3.28,-7.22
0.1,2.78,-3.95
0.1,3.31,-4.69
0.3,2.83,-2.94
0.3,3.33,-3.27
0.5,2.73,-2.47
0.5,3.34,-2.82
0.75,3.35,-2.16
0.75,2.79,-1.90
"""
def _write_auxiliary_material_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    nmc_file = output_dir / "NMC_333.txt"
    nmc_file.write_text(NMC_333_DATA, encoding="utf-8", newline="\n")

_REFERENCE_MATERIAL_STATEMENTS: List[str] = [
    '    model.component("comp1").material().create("mat1", "Common");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func().create("an1", "Analytic");',
    '    model.component("comp1").material("mat1").propertyGroup()\n         .create("ElectrolyteConductivity", "ElectrolyteConductivity", "Electrolyte conductivity");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func()\n         .create("an1", "Analytic");',
    '    model.component("comp1").material("mat1").propertyGroup()\n         .create("SpeciesProperties", "SpeciesProperties", "Species properties");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func().create("an1", "Analytic");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int1", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int2", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int3", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func().create("an2", "Analytic");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int4", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int5", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func()\n         .create("int6", "Interpolation");',
    '    model.component("comp1").material("mat1").propertyGroup()\n         .create("ElectrolyteSaltConcentration", "ElectrolyteSaltConcentration", "Electrolyte salt concentration");',
    '    model.component("comp1").material("mat1").label("LiPF6 in 3:7 EC:EMC (Liquid, Li-ion Battery)");',
    '    model.component("comp1").material("mat1").propertyGroup("def").label("Basic");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1").label("Analytic 1");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1").set("funcname", "Dl");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1")\n         .set("expr", "1.01e3*exp(1.01*c)*exp(-1.56e3/T)*exp(-4.87e2/T*c)*1e-6");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1").set("args", new String[]{"c", "T"});',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1").set("fununit", "cm^2/s");',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1")\n         .set("argunit", new String[]{"mol/L", "K"});',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1")\n         .set("plotaxis", new String[]{"on", "on"});',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1")\n         .set("plotfixedvalue", new String[]{"0", "0"});',
    '    model.component("comp1").material("mat1").propertyGroup("def").func("an1")\n         .set("plotargs", new String[][]{{"c", "0", "3000"}, {"T", "263.15[K]", "263.15[K]"}});',
    '    model.component("comp1").material("mat1").propertyGroup("def")\n         .set("diffusion", new String[]{"Dl(min(max(c,eps),3[M]),min(max(T,-10[degC]),50[degC]))", "0", "0", "0", "Dl(min(max(c,eps),3[M]),min(max(T,-10[degC]),50[degC]))", "0", "0", "0", "Dl(min(max(c,eps),3[M]),min(max(T,-10[degC]),50[degC]))"});',
    '    model.component("comp1").material("mat1").propertyGroup("def")\n         .setPropertyInfo("diffusion", "Johannes Landesfeind and Hubert A. Gasteiger, Temperature and Concentration Dependence of the Ionic Transport Properties of Lithium-Ion Battery Electrolytes, Journal of The Electrochemical Society, 166 (14) A3079-A3097 (2019)");',
    '    model.component("comp1").material("mat1").propertyGroup("def").addInput("concentration");',
    '    model.component("comp1").material("mat1").propertyGroup("def").addInput("temperature");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity")\n         .label("Electrolyte conductivity");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .label("Analytic 1");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("funcname", "sigmal");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("expr", "5.21e-1*(1+(T-2.28e2))*c*(1-1.06*sqrt(c)+3.53e-1*(1-3.59e-3*exp(1000/T))*c)/(1+c^4*1.48e-3*(exp(1000/T)))");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("args", new String[]{"c", "T"});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("fununit", "mS/cm");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("argunit", new String[]{"mol/L", "K"});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("plotaxis", new String[]{"on", "on"});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("plotfixedvalue", new String[]{"0", "0"});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").func("an1")\n         .set("plotargs", new String[][]{{"c", "0", "5000"}, {"T", "-10[degC]", "50[degC]"}});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity")\n         .set("sigmal", new String[]{"sigmal(max(c,eps),min(max(T,-10[degC]),50[degC]))", "0", "0", "0", "sigmal(max(c,eps),min(max(T,-10[degC]),50[degC]))", "0", "0", "0", "sigmal(max(c,eps),min(max(T,-10[degC]),50[degC]))"});',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity")\n         .setPropertyInfo("sigmal", "Johannes Landesfeind and Hubert A. Gasteiger, Temperature and Concentration Dependence of the Ionic Transport Properties of Lithium-Ion Battery Electrolytes, Journal of The Electrochemical Society, 166 (14) A3079-A3097 (2019)");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").addInput("concentration");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteConductivity").addInput("temperature");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").label("Species properties");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1").label("Analytic 1");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1").set("funcname", "TDF");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("expr", "p1_TDF(T)*c^2+p2_TDF(T)*c+p3_TDF(T)");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("args", new String[]{"c", "T"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1").set("fununit", "1");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("argunit", new String[]{"mol/L", "K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("plotaxis", new String[]{"on", "on"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("plotfixedvalue", new String[]{"0", "0"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an1")\n         .set("plotargs", new String[][]{{"c", "0", "3000"}, {"T", "-10[degC]", "50[degC]"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int1")\n         .label("Interpolation 1");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int1")\n         .set("funcname", "p1_TDF");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int1")\n         .set("table", new String[][]{{"263.15", "2.45e-1"}, \n         {"273.15", "7.23e-1"}, \n         {"283.15", "7.36e-1"}, \n         {"293.15", "6.65e-1"}, \n         {"303.15", "3.7e-1"}, \n         {"313.15", "1.85e-2"}, \n         {"323.15", "-3.92e-2"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int1")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int1")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int2")\n         .label("Interpolation 2");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int2")\n         .set("funcname", "p2_TDF");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int2")\n         .set("table", new String[][]{{"263.15", "4.49e-1"}, \n         {"273.15", "9.8e-2"}, \n         {"283.15", "-1.55e-1"}, \n         {"293.15", "-2.57e-1"}, \n         {"303.15", "7.6e-1"}, \n         {"313.15", "1.75"}, \n         {"323.15", "1.76"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int2")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int2")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int3")\n         .label("Interpolation 3");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int3")\n         .set("funcname", "p3_TDF");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int3")\n         .set("table", new String[][]{{"263.15", "3.41e-1"}, \n         {"273.15", "5e-1"}, \n         {"283.15", "8.63e-1"}, \n         {"293.15", "1.03"}, \n         {"303.15", "7.17e-1"}, \n         {"313.15", "4.8e-1"}, \n         {"323.15", "6.75e-1"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int3")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int3")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2").label("Analytic 2");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("funcname", "tplus");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("expr", "p1_tplus(T)*c^2+p2_tplus(T)*c+p3_tplus(T)");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("args", new String[]{"c", "T"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2").set("fununit", "1");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("argunit", new String[]{"mol/L", "K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("plotaxis", new String[]{"on", "on"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("plotfixedvalue", new String[]{"0", "0"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("an2")\n         .set("plotargs", new String[][]{{"c", "0", "3000"}, {"T", "-10[degC]", "50[degC]"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int4")\n         .label("Interpolation 4");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int4")\n         .set("funcname", "p1_tplus");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int4")\n         .set("table", new String[][]{{"263.15", "4.1e-2"}, \n         {"273.15", "1.04e-1"}, \n         {"283.15", "1.09e-1"}, \n         {"293.15", "1.4e-1"}, \n         {"303.15", "2.97e-2"}, \n         {"313.15", "-1.39e-2"}, \n         {"323.15", "-5.87e-3"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int4")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int4")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int5")\n         .label("Interpolation 5");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int5")\n         .set("funcname", "p2_tplus");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int5")\n         .set("table", new String[][]{{"263.15", "-3.63e-1"}, \n         {"273.15", "-3.38e-1"}, \n         {"283.15", "-4.12e-1"}, \n         {"293.15", "-5.74e-1"}, \n         {"303.15", "-2.1e-1"}, \n         {"313.15", "-9.01e-2"}, \n         {"323.15", "-1.3e-1"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int5")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int5")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int6")\n         .label("Interpolation 6");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int6")\n         .set("funcname", "p3_tplus");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int6")\n         .set("table", new String[][]{{"263.15", "-9.17e-2"}, \n         {"273.15", "2.13e-1"}, \n         {"283.15", "3.98e-1"}, \n         {"293.15", "5.57e-1"}, \n         {"303.15", "4.92e-1"}, \n         {"313.15", "5.26e-1"}, \n         {"323.15", "6.12e-1"}});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int6")\n         .set("fununit", new String[]{"1"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").func("int6")\n         .set("argunit", new String[]{"K"});',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties")\n         .set("transpNum", "tplus(min(max(c,eps),3[M]),min(max(T,-10[degC]),50[degC]))");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties")\n         .setPropertyInfo("transpNum", "Johannes Landesfeind and Hubert A. Gasteiger, Temperature and Concentration Dependence of the Ionic Transport Properties of Lithium-Ion Battery Electrolytes, Journal of The Electrochemical Society, 166 (14) A3079-A3097 (2019)");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties")\n         .set("fcl", "TDF(min(max(c,eps),3[M]),min(max(T,-10[degC]),50[degC]))-1");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties")\n         .setPropertyInfo("fcl", "Johannes Landesfeind and Hubert A. Gasteiger, Temperature and Concentration Dependence of the Ionic Transport Properties of Lithium-Ion Battery Electrolytes, Journal of The Electrochemical Society, 166 (14) A3079-A3097 (2019)");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").addInput("concentration");',
    '    model.component("comp1").material("mat1").propertyGroup("SpeciesProperties").addInput("temperature");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteSaltConcentration")\n         .label("Electrolyte salt concentration");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteSaltConcentration").identifier("cElsalt");',
    '    model.component("comp1").material("mat1").propertyGroup("ElectrolyteSaltConcentration")\n         .set("cElsalt", "1200[mol/m^3]");',
    '    model.component("comp1").material().create("mat2", "Common");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func().create("int1", "Interpolation");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func().create("int2", "Interpolation");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func().create("int3", "Interpolation");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func().create("int4", "Interpolation");',
    '    model.component("comp1").material("mat2").propertyGroup()\n         .create("ElectrodePotential", "ElectrodePotential", "Equilibrium potential");',
    '    model.component("comp1").material("mat2").propertyGroup()\n         .create("OperationalSOC", "OperationalSOC", "Operational electrode state of charge");',
    '    model.component("comp1").material("mat2").propertyGroup().create("ic", "ic", "Intercalation strain");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func().create("int1", "Interpolation");',
    '    model.component("comp1").material("mat2").propertyGroup()\n         .create("EquilibriumConcentration", "EquilibriumConcentration", "Equilibrium concentration");',
    '    model.component("comp1").material("mat2").propertyGroup()\n         .create("EquilibriumPotentialWithDOCInput", "EquilibriumPotentialWithDOCInput", "Equilibrium potential (using degree of conversion as model input)");',
    '    model.component("comp1").material("mat2").propertyGroup()\n         .create("EquilibriumDegreeOfConversion", "EquilibriumDegreeOfConversion", "Equilibrium degree of conversion");',
    '    model.component("comp1").material("mat2").label("Graphite, LixC6 MCMB (Negative, Li-ion Battery)");',
    '    model.component("comp1").material("mat2").propertyGroup("def").label("Basic");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int1").label("Interpolation 1");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int1").set("funcname", "E_int");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int1")\n         .set("table", new String[][]{{"0", "32.47"}, {"0.333", "28.56"}, {"0.5", "58.06"}, {"1", "108.67"}});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int1").set("fununit", new String[]{"GPa"});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int1").set("argunit", new String[]{"1"});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int2").label("Interpolation 2");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int2").set("funcname", "nu_int");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int2")\n         .set("table", new String[][]{{"0", "0.32"}, {"0.333", "0.39"}, {"0.5", "0.34"}, {"1", "0.24"}});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int2").set("fununit", new String[]{""});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").label("Interpolation 3");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("funcname", "Eeq");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3")\n         .set("table", new String[][]{{"0", "2.781186612"}, \n         {"0.01", "1.520893224"}, \n         {"0.02", "0.893922607"}, \n         {"0.03", "0.581284406"}, \n         {"0.04", "0.42452844"}, \n         {"0.05", "0.344895805"}, \n         {"0.06", "0.303146342"}, \n         {"0.07", "0.279578072"}, \n         {"0.08", "0.264093089"}, \n         {"0.09", "0.251347845"}, \n         {"0.1", "0.238588379"}, \n         {"0.11", "0.224803164"}, \n         {"0.12", "0.210294358"}, \n         {"0.13", "0.196408586"}, \n         {"0.14", "0.184624188"}, \n         {"0.15", "0.175188157"}, \n         {"0.16", "0.167373311"}, \n         {"0.17", "0.160452107"}, \n         {"0.18", "0.154025412"}, \n         {"0.19", "0.147948522"}, \n         {"0.2", "0.142214997"}, \n         {"0.21", "0.13688271"}, \n         {"0.22", "0.132033114"}, \n         {"0.23", "0.127747573"}, \n         {"0.24", "0.124091616"}, \n         {"0.25", "0.121103387"}, \n         {"0.26", "0.11878567"}, \n         {"0.27", "0.117102317"}, \n         {"0.28", "0.115980205"}, \n         {"0.29", "0.115317054"}, \n         {"0.3", "0.114993965"}, \n         {"0.31", "0.114890105"}, \n         {"0.32", "0.114886278"}, \n         {"0.33", "0.114884619"}, \n         {"0.34", "0.114873068"}, \n         {"0.35", "0.114824904"}, \n         {"0.36", "0.114644725"}, \n         {"0.37", "0.114372614"}, \n         {"0.38", "0.114017954"}, \n         {"0.39", "0.11359371"}, \n         {"0.4", "0.11311133"}, \n         {"0.41", "0.112575849"}, \n         {"0.42", "0.111980245"}, \n         {"0.43", "0.111297682"}, \n         {"0.44", "0.110470149"}, \n         {"0.45", "0.109393081"}, \n         {"0.46", "0.107900592"}, \n         {"0.47", "0.10576964"}, \n         {"0.48", "0.102783317"}, \n         {"0.49", "0.09889031"}, \n         {"0.5", "0.094391564"}, \n         {"0.51", "0.089921069"}, \n         {"0.52", "0.086112415"}, \n         {"0.53", "0.083265315"}, \n         {"0.54", "0.081326247"}, \n         {"0.55", "0.080074892"}, \n         {"0.56", "0.07928329"}, \n         {"0.57", "0.078778765"}, \n         {"0.58", "0.078447703"}, \n         {"0.59", "0.078220432"}, \n         {"0.6", "0.078055641"}, \n         {"0.61", "0.077929111"}, \n         {"0.62", "0.077826563"}, \n         {"0.63", "0.077739397"}, \n         {"0.64", "0.077662227"}, \n         {"0.65", "0.077591472"}, \n         {"0.66", "0.077524557"}, \n         {"0.67", "0.077459463"}, \n         {"0.68", "0.077394455"}, \n         {"0.69", "0.077327934"}, \n         {"0.7", "0.077258337"}, \n         {"0.71", "0.077184077"}, \n         {"0.72", "0.077103499"}, \n         {"0.73", "0.077014851"}, \n         {"0.74", "0.076916258"}, \n         {"0.75", "0.07680571"}, \n         {"0.76", "0.07668104"}, \n         {"0.77", "0.07653992"}, \n         {"0.78", "0.076379839"}, \n         {"0.79", "0.076198086"}, \n         {"0.8", "0.075991699"}, \n         {"0.81", "0.075757371"}, \n         {"0.82", "0.075491288"}, \n         {"0.83", "0.075188813"}, \n         {"0.84", "0.07484398"}, \n         {"0.85", "0.074448647"}, \n         {"0.86", "0.07399118"}, \n         {"0.87", "0.073454466"}, \n         {"0.88", "0.072812991"}, \n         {"0.89", "0.072028722"}, \n         {"0.9", "0.071045433"}, \n         {"0.91", "0.069780996"}, \n         {"0.92", "0.068116222"}, \n         {"0.93", "0.065874599"}, \n         {"0.94", "0.062770873"}, \n         {"0.95", "0.058253898"}, \n         {"0.96", "0.051075794"}, \n         {"0.97", "0.038790069"}, \n         {"0.98", "0.020172191"}});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("extrap", "linear");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("fununit", new String[]{"V"});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("argunit", new String[]{""});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("defineinv", true);',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int3").set("funcinvname", "Eeq_inv");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int4").label("Interpolation 4");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int4").set("funcname", "dEeqdT");',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int4")\n         .set("table", new String[][]{{"0", "3.0e-4"}, \n         {"0.17", "0"}, \n         {"0.24", "-6e-5"}, \n         {"0.28", "-1.6e-4"}, \n         {"0.5", "-1.6e-4"}, \n         {"0.54", "-9e-5"}, \n         {"0.71", "-9e-5"}, \n         {"0.85", "-1.0e-4"}, \n         {"1.0", "-1.2e-4"}});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int4").set("fununit", new String[]{"V/K"});',
    '    model.component("comp1").material("mat2").propertyGroup("def").func("int4").set("argunit", new String[]{""});',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("youngsmodulus", "");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("poissonsratio", "");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("youngsmodulus", "E_int(c/csmax)");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("youngsmodulus", "Yue Qi et al 2010 J. Electrochem. Soc. 157 A558");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("poissonsratio", "nu_int(c/csmax)");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("poissonsratio", "Yue Qi et al 2010 J. Electrochem. Soc. 157 A558");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .set("electricconductivity", new String[]{"100[S/m]", "0", "0", "0", "100[S/m]", "0", "0", "0", "100[S/m]"});',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("electricconductivity", "V. Srinivasan, and J. Newman, \\u201cDesign and Optimization of a Natural Graphite/Iron Phosphate Lithium Ion Cell,\\u201d J. Electrochem. Soc., vol. 151, p. 1530, 2004.");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .set("diffusion", new String[]{"1.4523e-13*exp(68025.7/8.314*(1/(T_ref/1[K])-1/(T2/1[K])))[m^2/s]", "0", "0", "0", "1.4523e-13*exp(68025.7/8.314*(1/(T_ref/1[K])-1/(T2/1[K])))[m^2/s]", "0", "0", "0", "1.4523e-13*exp(68025.7/8.314*(1/(T_ref/1[K])-1/(T2/1[K])))[m^2/s]"});',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("diffusion", "K. Kumaresan, G. Sikha, and R. E. White, \\u201cThermal Model for a Li-Ion Cell,\\u201d J. Electrochem. Soc., vol. 155, p. A164, 2008.");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .set("thermalconductivity", new String[]{"1[W/(m*K)]", "0", "0", "0", "1[W/(m*K)]", "0", "0", "0", "1[W/(m*K)]"});',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("thermalconductivity", "S. Chen, C. Wan, and Y. Wang, J. Power Sources, 140, 111 (2005).");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("heatcapacity", "750[J/(kg*K)]");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("heatcapacity", "SI Chemical Data, John Wiley & Sons, 1994");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("density", "2300[kg/m^3]");',
    '    model.component("comp1").material("mat2").propertyGroup("def")\n         .setPropertyInfo("density", "SI Chemical Data, John Wiley & Sons, 1994");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("csmax", "31507[mol/m^3]");',
    '    model.component("comp1").material("mat2").propertyGroup("def").descr("csmax", "");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("T_ref", "318[K]");',
    '    model.component("comp1").material("mat2").propertyGroup("def").descr("T_ref", "");',
    '    model.component("comp1").material("mat2").propertyGroup("def").set("T2", "min(393.15,max(T,223.15))");',
    '    model.component("comp1").material("mat2").propertyGroup("def").descr("T2", "");',
    '    model.component("comp1").material("mat2").propertyGroup("def").addInput("temperature");',
    '    model.component("comp1").material("mat2").propertyGroup("def").addInput("concentration");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").label("Equilibrium potential");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").identifier("eeq");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential")\n         .set("Eeq", "def.Eeq(doc)+def.dEeqdT(doc)*(T-298[K])");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential")\n         .setPropertyInfo("Eeq", "D. P Karthikeyan, G. Sikha, and R. E. White, \\u201cThermodynamic model development for lithium intercalation electrodes,\\u201d J. Power Sources, vol. 185, p. 1398, 2008.");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").set("dEeqdT", "def.dEeqdT(doc)");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential")\n         .setPropertyInfo("dEeqdT", "K. E. Thomas, and J. Newman, \\u201cHeats of mixing and of entropy in porous insertion electrodes,\\u201d J. Power Sources., vol. 119-121, p. 844, 2003.");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").set("cEeqref", "def.csmax");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").set("doc", "c/cEeqref");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential")\n         .descr("doc", "Degree of conversion (state of lithiation)");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").addInput("concentration");',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").addInput("temperature");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC")\n         .label("Operational electrode state of charge");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").identifier("opsoc");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").set("socmax", "def.Eeq_inv(E_min)");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").set("socmin", "def.Eeq_inv(E_max)");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").set("E_max", "1[V]");',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").set("E_min", "0.075[V]");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").label("Intercalation strain");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1").label("Interpolation 1");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1").set("funcname", "dVOLdSOL");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1")\n         .set("table", new String[][]{{"0", "0"}, \n         {"0.006802721088435382", "0.12500000000000178"}, \n         {"0.06316812439261421", "1.2736486486486491"}, \n         {"0.11175898931000966", "2.523648648648649"}, \n         {"0.17978620019436342", "3.5709459459459474"}, \n         {"0.2400388726919339", "4.449324324324325"}, \n         {"0.2905733722060252", "5.192567567567568"}, \n         {"0.3566569484936831", "5.66554054054054"}, \n         {"0.4188532555879494", "5.969594594594595"}, \n         {"0.48104956268221566", "6.10472972972973"}, \n         {"0.5432458697764819", "6.173648648648647"}, \n         {"0.58600583090379", "6.306081081081081"}, \n         {"0.6112730806608356", "7.726351351351352"}, \n         {"0.6443148688046647", "8.570945945945946"}, \n         {"0.694849368318756", "9.449324324324323"}, \n         {"0.7414965986394557", "10.29391891891892"}, \n         {"0.7764820213799805", "10.902027027027025"}, \n         {"0.8231292517006802", "11.543918918918918"}, \n         {"0.8542274052478133", "12.152027027027026"}, \n         {"0.8833819241982507", "12.827702702702702"}, \n         {"0.9183673469387755", "12.996621621621621"}, \n         {"0.9494655004859086", "13.16554054054054"}});',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1").set("extrap", "linear");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1").set("fununit", new String[]{"%"});',
    '    model.component("comp1").material("mat2").propertyGroup("ic").func("int1").set("argunit", new String[]{"1"});',
    '    model.component("comp1").material("mat2").propertyGroup("ic").identifier("is");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").set("dvol", "dVOLdSOL(c/def.csmax)");',
    '    model.component("comp1").material("mat2").propertyGroup("ic")\n         .setPropertyInfo("dvol", "S. Schweidler, L. de Biasi, A. Schiele, P. Hartmann, T. Brezesinski and J. Janek, \\"Volume Changes of Graphite Anodes Revisited: A Combined Operando X-Ray Diffraction and In Situ Pressure Analysis Study\\", J. Phys. Chem. C, 2018, 122, 8829\\u20138835");',
    '    model.component("comp1").material("mat2").propertyGroup("ic").addInput("concentration");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumConcentration")\n         .label("Equilibrium concentration");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumConcentration")\n         .set("csEq", "def.csmax*def.Eeq_inv(V)");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumConcentration")\n         .addInput("electricpotential");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .label("Equilibrium potential (using degree of conversion as model input)");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .set("Eeq", "def.Eeq(doc)+def.dEeqdT(doc)*(T-298[K])");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .set("dEeqdT", "def.dEeqdT(doc)");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .addInput("degreeofconversion");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .addInput("temperature");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumDegreeOfConversion")\n         .label("Equilibrium degree of conversion");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumDegreeOfConversion")\n         .set("docEq", "def.Eeq_inv(V)");',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumDegreeOfConversion")\n         .addInput("electricpotential");',
    '    model.component("comp1").material().create("mat3", "Common");',
    '    model.component("comp1").material("mat3").propertyGroup("def").func().create("int1", "Interpolation");',
    '    model.component("comp1").material("mat3").propertyGroup()\n         .create("ElectrodePotential", "ElectrodePotential", "Equilibrium potential");',
    '    model.component("comp1").material("mat3").propertyGroup()\n         .create("OperationalSOC", "OperationalSOC", "Operational electrode state of charge");',
    '    model.component("comp1").material("mat3").propertyGroup().create("ic", "ic", "Intercalation strain");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func().create("int1", "Interpolation");',
    '    model.component("comp1").material("mat3").propertyGroup()\n         .create("EquilibriumConcentration", "EquilibriumConcentration", "Equilibrium concentration");',
    '    model.component("comp1").material("mat3").propertyGroup()\n         .create("EquilibriumPotentialWithDOCInput", "EquilibriumPotentialWithDOCInput", "Equilibrium potential (using degree of conversion as model input)");',
    '    model.component("comp1").material("mat3").propertyGroup()\n         .create("EquilibriumDegreeOfConversion", "EquilibriumDegreeOfConversion", "Equilibrium degree of conversion");',
    '    model.component("comp1").material("mat3").propertyGroup().create("pg1", "def", "Electric conductivity");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func().create("int1", "Interpolation");',
    '    model.component("comp1").material("mat3").label("NMC 111, LiNi0.33Mn0.33Co0.33O2 (Positive, Li-ion Battery)");',
    '    model.component("comp1").material("mat3").propertyGroup("def").label("Basic");',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").label("Interpolation 1");',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("funcname", "Eeq");',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1")\n         .set("table", new String[][]{{"0", "4.44"}, \n         {"0.032", "4.34"}, \n         {"0.102", "4.23"}, \n         {"0.187", "4.13"}, \n         {"0.289", "4.025"}, \n         {"0.38", "3.945"}, \n         {"0.543", "3.835"}, \n         {"0.775", "3.71"}, \n         {"0.872", "3.62"}, \n         {"0.925", "3.51"}, \n         {"0.943", "3.42"}, \n         {"0.957", "3.30"}, \n         {"0.966", "3.165"}, \n         {"0.970", "3.02"}, \n         {"0.972", "2.90"}, \n         {"0.975", "2.688"}});',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("extrap", "linear");',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("fununit", new String[]{"V"});',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("argunit", new String[]{""});',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("defineinv", true);',
    '    model.component("comp1").material("mat3").propertyGroup("def").func("int1").set("funcinvname", "Eeq_inv");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("poissonsratio", "");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("youngsmodulus", "");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("thermalconductivity", "");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("thermalexpansioncoefficient", "");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("poissonsratio", "0.25");',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .setPropertyInfo("poissonsratio", "Mechanical and physical properties of LiNi0.33Mn0.33Co0.33O2 (NMC),\\nE Cheng, K. Hong, N. Taylor, H. Choe,\\nJ. Wolfenstinec, J. Sakamotoa,\\nJournal of the European Ceramic Society 37 (2017) 3213\\u20133217");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("youngsmodulus", "199[GPa]");',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .setPropertyInfo("youngsmodulus", "Mechanical and physical properties of LiNi0.33Mn0.33Co0.33O2 (NMC),\\nE Cheng, K. Hong, N. Taylor, H. Choe,\\nJ. Wolfenstinec, J. Sakamotoa,\\nJournal of the European Ceramic Society 37 (2017) 3213\\u20133217");',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .set("thermalconductivity", new String[]{"3.6[W/(m*K)]", "0", "0", "0", "3.6[W/(m*K)]", "0", "0", "0", "3.6[W/(m*K)]"});',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .setPropertyInfo("thermalconductivity", "Mechanical and physical properties of LiNi0.33Mn0.33Co0.33O2 (NMC),\\nE Chenga, K. Hong, N. Taylor, H. Choe,\\nJ. Wolfenstinec, J. Sakamotoa,\\nJournal of the European Ceramic Society 37 (2017) 3213\\u20133217");',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .set("thermalexpansioncoefficient", new String[]{"1.2e-5[1/K]", "0", "0", "0", "1.2e-5[1/K]", "0", "0", "0", "1.2e-5[1/K]"});',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .setPropertyInfo("thermalexpansioncoefficient", "Mechanical and physical properties of LiNi0.33Mn0.33Co0.33O2 (NMC),\\nE Chenga, K. Hong, N. Taylor, H. Choe,\\nJ. Wolfenstinec, J. Sakamotoa,\\nJournal of the European Ceramic Society 37 (2017) 3213\\u20133217");',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .set("diffusion", new String[]{"1e-14[m^2/s]", "0", "0", "0", "1e-14[m^2/s]", "0", "0", "0", "1e-14[m^2/s]"});',
    '    model.component("comp1").material("mat3").propertyGroup("def")\n         .setPropertyInfo("diffusion", "Jing Ying Ko et al, J. Electrochem. Soc., 166, A2939");',
    '    model.component("comp1").material("mat3").propertyGroup("def").set("csmax", "49000[mol/m^3]");',
    '    model.component("comp1").material("mat3").propertyGroup("def").descr("csmax", "");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").label("Equilibrium potential");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").identifier("eeq");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .set("Eeq", "def.Eeq(doc)+dEeqdT*(T-298[K])");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .setPropertyInfo("Eeq", "W. Zheng, M. Shui, J. Shu, S. Gao, D. Xu, L. Chen, L. Feng and Y. Ren, \\" GITT studies on oxide cathode LiNi1/3Co1/3Mn1/3O2 synthesized by citric acid assisted high-energy ball milling\\", Bull. Mater. Sci., vol. 36, p. A495, 2013");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .set("dEeqdT", "-10[J/mol/K]/F_const");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .setPropertyInfo("dEeqdT", "V Viswanathan, D Choi, D Wang, W Xu, S Towne, R Williford, JG Zhang, J Liu and Z Yang \\"Effect of entropy change on lithium intercalation in cathodes and anodes on Li-ion battery thermal management\\", Journal of Power Sources 195 (2010) 3720-3729");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").set("cEeqref", "def.csmax");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .setPropertyInfo("cEeqref", "W. Zheng, M. Shui, J. Shu, S. Gao, D. Xu, L. Chen, L. Feng and Y. Ren, \\" GITT studies on oxide cathode LiNi1/3Co1/3Mn1/3O2 synthesized by citric acid assisted high-energy ball milling\\", Bull. Mater. Sci., vol. 36, p. A495, 2013");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").set("doc", "c/cEeqref");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential")\n         .descr("doc", "Degree of conversion (state of lithiation)");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").addInput("concentration");',
    '    model.component("comp1").material("mat3").propertyGroup("ElectrodePotential").addInput("temperature");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC")\n         .label("Operational electrode state of charge");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC").identifier("opsoc");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC").set("socmax", "def.Eeq_inv(E_min)");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC").set("socmin", "def.Eeq_inv(E_max)");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC").set("E_max", "4.4[V]");',
    '    model.component("comp1").material("mat3").propertyGroup("OperationalSOC").set("E_min", "3.3[V]");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").label("Intercalation strain");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1").label("Interpolation 1");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1").set("funcname", "dVOLdSOL");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1")\n         .set("table", new String[][]{{"1", "0"}, \n         {"0.9260263416001121", "-0.010256410256411108"}, \n         {"0.8670351688384477", "-0.1948717948717955"}, \n         {"0.8113086731119519", "-0.27692307692307727"}, \n         {"0.7506669468964551", "-0.37948717948718036"}, \n         {"0.6949460557657279", "-0.502564102564103"}, \n         {"0.628563822334314", "-0.5846153846153856"}, \n         {"0.55562421185372", "-0.6666666666666674"}, \n         {"0.501531455793751", "-0.7076923076923083"}, \n         {"0.4441600112091916", "-0.7487179487179496"}, \n         {"0.3851716407454113", "-0.953846153846154"}, \n         {"0.3278338237354632", "-1.241025641025642"}, \n         {"0.2737943113352951", "-1.671794871794872"}, \n         {"0.24269440941572107", "-2.0205128205128213"}});',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1").set("extrap", "linear");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1").set("fununit", new String[]{"%"});',
    '    model.component("comp1").material("mat3").propertyGroup("ic").func("int1").set("argunit", new String[]{"1"});',
    '    model.component("comp1").material("mat3").propertyGroup("ic").identifier("is");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").set("dvol", "dVOLdSOL(c/def.csmax)");',
    '    model.component("comp1").material("mat3").propertyGroup("ic")\n         .setPropertyInfo("dvol", "R. Koerver and others, \\u201cChemo-mechanical expansion of lithium electrode materials \\u2014 on the route to mechanically optimized all-solid-state batteries,\\u201d Energy Environ. Sci., vol. 11, pp. 2142\\u20132158, 201");',
    '    model.component("comp1").material("mat3").propertyGroup("ic").addInput("concentration");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumConcentration")\n         .label("Equilibrium concentration");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumConcentration")\n         .set("csEq", "def.csmax*def.Eeq_inv(V)");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumConcentration")\n         .addInput("electricpotential");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .label("Equilibrium potential (using degree of conversion as model input)");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .set("Eeq", "def.Eeq(doc)+dEeqdT*(T-298[K])");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .set("dEeqdT", "-10[J/mol/K]/F_const");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .addInput("degreeofconversion");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumPotentialWithDOCInput")\n         .addInput("temperature");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumDegreeOfConversion")\n         .label("Equilibrium degree of conversion");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumDegreeOfConversion")\n         .set("docEq", "def.Eeq_inv(V)");',
    '    model.component("comp1").material("mat3").propertyGroup("EquilibriumDegreeOfConversion")\n         .addInput("electricpotential");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("source", "file");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").label("Interpolation 1");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("importedname", "NMC_333.txt");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("importeddim", "2D");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")\n         .set("funcnametable", new String[][]{{"log_sigmas", "1"}});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("filecolumns", 3);',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")\n         .set("columnKeys", new String[]{"col1", "col2", "col3"});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")\n         .set("columnType", new String[]{"col1", "arg", "col2", "arg", "col3", "value"});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")\n         .set("funcnames", new String[]{"col1", "int1", "col2", "int1", "col3", "log_sigmas"});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("fununit", new String[]{""});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")\n         .set("argunit", new String[]{"1", "1/K"});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("sourcetype", "model");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1")\n         .set("electricconductivity", new String[]{"10^log_sigmas(x,1000/T)[S/cm]", "0", "0", "0", "10^log_sigmas(x,1000/T)[S/cm]", "0", "0", "0", "10^log_sigmas(x,1000/T)[S/cm]"});',
    '    model.component("comp1").material("mat3").propertyGroup("pg1")\n         .setPropertyInfo("electricconductivity", "Ruhul Amin and Yet-Ming Chiang 2016 J. Electrochem. Soc. 163 A1512");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").set("x", "min(max(1-c/def.csmax,0),1)");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").descr("x", "Degree of delithiation");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").addInput("temperature");',
    '    model.component("comp1").material("mat3").propertyGroup("pg1").addInput("concentration");',
    '    model.component("comp1").material("mat1").selection()\n         .set(1, 2, 3, 6, 7, 10, 11, 14, 15, 18, 19, 21, 25, 28, 30, 34, 37, 39, 41, 44, 47, 51, 54, 57, 58, 60, 63, 68, 69, 70, 74, 75, 78, 81, 83, 85, 88, 90, 97, 98, 101, 103, 106, 110, 111, 114, 115, 118, 119, 121, 123, 129, 133, 138, 139, 141, 143, 145, 149, 150, 153, 155, 157, 159, 163, 167);',
    '    model.component("comp1").material("mat1").selection().set();',
    '    model.component("comp1").material("mat1").selection().set();',
    '    model.component("comp1").material("mat2").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("def").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("ic").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumConcentration").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput").active(false);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumDegreeOfConversion").active(false);',
    '    model.component("comp1").material("mat3").active(false);',
    '    model.component("comp1").material("mat2").active(true);',
    '    model.component("comp1").material("mat2").active(false);',
    '    model.component("comp1").material("mat2").active(true);',
    '    model.component("comp1").material("mat3").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("def").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("ElectrodePotential").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("OperationalSOC").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("ic").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumConcentration").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumPotentialWithDOCInput").active(true);',
    '    model.component("comp1").material("mat2").propertyGroup("EquilibriumDegreeOfConversion").active(true);',
    '    model.component("comp1").material().create("mat4", "Common");',
    '    model.component("comp1").material("mat4").label("\\u7c98\\u7ed3\\u5242");',
    '    model.component("comp1").material("mat4").propertyGroup("def")\n         .set("electricconductivity", new String[]{"100", "0", "0", "0", "100", "0", "0", "0", "100"});',
    '    model.component("comp1").material("mat4").propertyGroup("def").featureInfo().create("info");',
    '    model.component("comp1").material("mat4").propertyGroup()\n         .create("ElectrolyteConductivity", "ElectrolyteConductivity", "\\u7535\\u89e3\\u8d28\\u7535\\u5bfc\\u7387");',
    '    model.component("comp1").material("mat4").propertyGroup("ElectrolyteConductivity")\n         .set("sigmal", new String[]{"100", "0", "0", "0", "100", "0", "0", "0", "100"});',
    '    model.component("comp1").material("mat4").propertyGroup("ElectrolyteConductivity").info("category").title(null);',
    '    model.component("comp1").material("mat4").propertyGroup("ElectrolyteConductivity").info("category")\n         .body("Electrochemistry");',
    '    model.component("comp1").material("mat4").propertyGroup("ElectrolyteConductivity").featureInfo().create("info");',
    '    model.component("comp1").material("mat4").selection()\n         .set(4, 5, 8, 9, 12, 13, 16, 17, 20, 22, 23, 24, 26, 27, 29, 31, 32, 33, 35, 36, 38, 40, 42, 43, 45, 46, 48, 49, 50, 52, 53, 55, 56, 59, 61, 62, 64, 65, 66, 67, 71, 72, 73, 76, 77, 79, 80, 82, 84, 86, 87, 89, 91, 92, 93, 94, 95, 96, 99, 100, 102, 104, 105, 107, 108, 109, 112, 113, 116, 117, 120, 122, 124, 125, 126, 127, 128, 130, 131, 132, 134, 135, 136, 137, 140, 142, 144, 146, 147, 148, 151, 152, 154, 156, 158, 160, 161, 162, 164, 165, 166, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179);',
    '    model.component("comp1").material("mat4").propertyGroup("def").set("diffusion", new String[]{"0"});',
    '    model.component("comp1").material("mat4").propertyGroup()\n         .create("SpeciesProperties", "SpeciesProperties", "Species_properties");',
    '    model.component("comp1").material("mat4").propertyGroup("SpeciesProperties").set("transpNum", new String[]{"0"});',
    '    model.component("comp1").material("mat4").propertyGroup("SpeciesProperties").set("fcl", new String[]{"0"});',
                                '    model.component("comp1").material("mat1").selection().named("geom1_dif_electrolyte_dom");',
    '    model.component("comp1").material("mat2").selection().named("geom1_uni_neg_particles_dom");',
    '    model.component("comp1").material("mat3").selection().named("geom1_uni_pos_particles_dom");',
    '    model.component("comp1").material("mat4").selection().named("geom1_uni_all_binders_dom");',
]


def _chunk_statements_by_byte_limit(statements: List[str], max_bytes: int = 45000) -> List[List[str]]:
    chunks: List[List[str]] = []
    current: List[str] = []
    current_bytes = 0

    for stmt in statements:
        stmt_bytes = len((stmt + "\n").encode("utf-8"))
        if current and current_bytes + stmt_bytes > max_bytes:
            chunks.append(current)
            current = [stmt]
            current_bytes = stmt_bytes
        else:
            current.append(stmt)
            current_bytes += stmt_bytes

    if current:
        chunks.append(current)

    return chunks

def _patch_mat3_log_sigmas_external_file(statements: List[str], model_dir: str) -> List[str]:
    start_marker = '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("source", "file");'
    end_marker = '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("sourcetype", "model");'

    try:
        start_idx = statements.index(start_marker)
        end_idx = statements.index(end_marker)
    except ValueError as exc:
        raise JavaWriterError("未找到 mat3/pg1/int1 的文件插值定义，无法修补。") from exc

    if end_idx < start_idx:
        raise JavaWriterError("mat3/pg1/int1 插值定义起止位置异常。")

    patched_block = [
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("source", "file");',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").label("Interpolation 1");',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("importedname", "NMC_333.txt");',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("importeddim", "2D");',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("funcnametable", new String[][]{{"log_sigmas", "1"}});',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("filecolumns", 3);',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("columnKeys", new String[]{"col1", "col2", "col3"});',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("columnType", new String[]{"col1", "arg", "col2", "arg", "col3", "value"});',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("funcnames", new String[]{"col1", "int1", "col2", "int1", "col3", "log_sigmas"});',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("fununit", new String[]{""});',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("argunit", new String[]{"1", "1/K"});',
        f'    java.io.File nmc333File = new java.io.File("{model_dir}/NMC_333.txt");',
        '    if (!nmc333File.isFile()) {',
        '      throw new RuntimeException("NMC_333.txt not found: " + nmc333File.getAbsolutePath());',
        '    }',
        '    System.out.println("NMC_333.txt path: " + nmc333File.getAbsolutePath());',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        '\n         .set("filename", nmc333File.getAbsolutePath());',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("sourcetype", "user");',
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").importData();',
    ]

    return statements[:start_idx] + patched_block + statements[end_idx + 1:]

def _patch_mat3_log_sigmas_file_import(statements: List[str], model_dir: str) -> List[str]:
    marker = '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").set("sourcetype", "model");'

    try:
        idx = statements.index(marker)
    except ValueError as exc:
        raise JavaWriterError("未找到 mat3/pg1/int1 的 sourcetype 定义，无法补充文件导入。") from exc

    filename_stmt = (
        '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1")'
        f'\n         .set("filename", "{model_dir}/NMC_333.txt");'
    )
    import_stmt = '    model.component("comp1").material("mat3").propertyGroup("pg1").func("int1").importData();'

    patched = list(statements)
    patched[idx:idx + 1] = [marker, filename_stmt, import_stmt]
    return patched
def _build_materials_method(model_dir: str) -> List[str]:
    statements = list(_REFERENCE_MATERIAL_STATEMENTS)
    statements = _patch_mat3_log_sigmas_external_file(statements, model_dir)

    chunks = _chunk_statements_by_byte_limit(statements, max_bytes=45000)

    lines: List[str] = []

    if not chunks:
        lines.extend(_method_header("buildMaterials"))
        lines.extend(_method_footer())
        return lines

    for idx, chunk in enumerate(chunks, start=1):
        part_name = f"buildMaterials_part{idx}"
        lines.extend(_method_header(part_name))
        for stmt in chunk:
            lines.append(stmt)
            lines.append("")
        lines.extend(_method_footer())

    lines.extend(_method_header("buildMaterials"))
    for idx in range(1, len(chunks) + 1):
        lines.append(f"    buildMaterials_part{idx}(model);")
    lines.extend(_method_footer())
    return lines

def _build_liion_skeleton_method(case: ModelCase) -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildLiionSkeleton"))

    lines.extend([
        '    model.component("comp1").physics().create("liion", "LithiumIonBatteryMPH", "geom1");',
        '    model.component("comp1").physics("liion").label("锂离子电池");',
        '    model.component("comp1").physics("liion").prop("d").set("d", "D_ele");',
        "",

                   
        '    model.component("comp1").physics("liion").feature("init1").label("负极及电解液初始值");',
        '    model.component("comp1").physics("liion").feature("init1").set("phil", "phil_init");',
        '    model.component("comp1").physics("liion").feature("init1").set("cl", "cl_init");',
        "",

              
        '    model.component("comp1").physics("liion").create("ice1", "Electrolyte", 2);',
        '    model.component("comp1").physics("liion").feature("ice1").label("电解质1");',
        '    model.component("comp1").physics("liion").feature("ice1").selection().named("geom1_dif_electrolyte_dom");',
        '    model.component("comp1").physics("liion").feature("ice1").set("ElectrolyteMaterial", "mat1");',
        "",

                     
        '    model.component("comp1").physics("liion").create("init3", "init", 2);',
        '    model.component("comp1").physics("liion").feature("init3").label("负极及电解液初始值 1");',
        '    model.component("comp1").physics("liion").feature("init3").selection().all();',
        '    model.component("comp1").physics("liion").feature("init3").set("phil", "phil_init");',
        '    model.component("comp1").physics("liion").feature("init3").set("cl", "cl_init");',
        "",

               
        '    model.component("comp1").physics("liion").create("init2", "init", 2);',
        '    model.component("comp1").physics("liion").feature("init2").label("正极初始值");',
        '    model.component("comp1").physics("liion").feature("init2").selection().named("geom1_uni_pos_particles_dom");',
        '    model.component("comp1").physics("liion").feature("init2").set("phil", "phil_init");',
        '    model.component("comp1").physics("liion").feature("init2").set("cl", "cl_init");',
        '    model.component("comp1").physics("liion").feature("init2").set("phis", "E_cell_init");',
        "",

                   
        '    model.component("comp1").physics("liion").create("bei1", "InternalElectrodeSurface", 1);',
        '    model.component("comp1").physics("liion").feature("bei1").label("内部电极表面_正极");',
        '    model.component("comp1").physics("liion").feature("bei1").selection().named("geom1_int_pos_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("liion").feature("bei1").set("FilmResistanceType", "SurfaceResistance");',
        '    model.component("comp1").physics("liion").feature("bei1").set("Rf", "Rfilm_pos");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("MaterialOption", "mat3");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("ElectrodeKinetics", "ButlerVolmer");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("i0", "i0_pos");',
        "",

                   
        '    model.component("comp1").physics("liion").feature().duplicate("bei2", "bei1");',
        '    model.component("comp1").physics("liion").feature("bei2").label("内部电极表面_负极");',
        '    model.component("comp1").physics("liion").feature("bei2").selection().named("geom1_int_neg_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("liion").feature("bei2").set("Rf", "Rfilm_neg");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("MaterialOption", "mat2");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("ElectrodeKinetics", "LithiumInsertion");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("i0_ref", "i0_neg");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("i0", "i0_neg");',
        "",

                       
        '    model.component("comp1").physics("liion").create("pce1", "PorousElectrode", 2);',
        '    model.component("comp1").physics("liion").feature("pce1").label("多孔电极_正极binder");',
        '    model.component("comp1").physics("liion").feature("pce1").selection().named("geom1_dif_pos_binders_dom");',
        '    model.component("comp1").physics("liion").feature("pce1").set("ElectrodeMaterial", "dommat");',
        '    model.component("comp1").physics("liion").feature("pce1").set("ElectrolyteMaterial", "mat1");',
        '    model.component("comp1").physics("liion").feature("pce1").set("IntercalationOption", "NonIntercalatingParticles");',
        '    model.component("comp1").physics("liion").feature("pce1").feature("per1").active(false);',
        "",

                       
        '    model.component("comp1").physics("liion").create("pce2", "PorousElectrode", 2);',
        '    model.component("comp1").physics("liion").feature("pce2").label("多孔电极_负极binder");',
        '    model.component("comp1").physics("liion").feature("pce2").selection().named("geom1_dif_neg_binders_dom");',
        '    model.component("comp1").physics("liion").feature("pce2").set("ElectrodeMaterial", "dommat");',
        '    model.component("comp1").physics("liion").feature("pce2").set("ElectrolyteMaterial", "mat1");',
        '    model.component("comp1").physics("liion").feature("pce2").set("IntercalationOption", "NonIntercalatingParticles");',
        '    model.component("comp1").physics("liion").feature("pce2").feature("per1").active(false);',
        "",

              
        '    model.component("comp1").physics("liion").create("egnd1", "ElectricGround", 1);',
        '    model.component("comp1").physics("liion").feature("egnd1").label("负极接地");',
        '    model.component("comp1").physics("liion").feature("egnd1").selection().named("geom1_gboxsel_neg_collector");',
        "",

            
        '    model.component("comp1").physics("liion").create("ec1", "ElectrodeCurrent", 1);',
        '    model.component("comp1").physics("liion").feature("ec1").label("放电");',
        '    model.component("comp1").physics("liion").feature("ec1").selection().named("geom1_gboxsel_pos_collector");',
        '    model.component("comp1").physics("liion").feature("ec1").set("Its", "-i_0*C");',
        '    model.component("comp1").physics("liion").feature("ec1").set("phis0init", "E_cell_init");',
        "",

               
        '    model.component("comp1").physics("liion").create("cc1", "CurrentConductor", 2);',
        '    model.component("comp1").physics("liion").feature("cc1").label("电流导体1");',
        '    model.component("comp1").physics("liion").feature("cc1").selection().named("geom1_uni_pos_particles_dom");',
        '    model.component("comp1").physics("liion").feature("cc1").set("minput_concentration_src", "fromCommonDef");',
        "",

               
        '    model.component("comp1").physics("liion").create("cc2", "CurrentConductor", 2);',
        '    model.component("comp1").physics("liion").feature("cc2").label("电流导体2");',
        '    model.component("comp1").physics("liion").feature("cc2").selection().named("geom1_uni_neg_particles_dom");',
        '    model.component("comp1").physics("liion").feature("cc2").set("minput_concentration_src", "fromCommonDef");',
        "",
    ])

    lines.extend(_method_footer())
    return lines
def _build_tds_skeleton_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildTdsSkeleton"))

    lines.extend([
        '    model.component("comp1").physics().create("tds", "DilutedSpecies", new String[]{"c"});',
        '    model.component("comp1").physics("tds").label("稀物质传递");',
        '    model.component("comp1").physics("tds").selection().named("geom1_uni_all_particles_dom");',
        '    model.component("comp1").physics("tds").prop("TransportMechanism").set("Convection", false);',
        "",

        '    model.component("comp1").physics("tds").feature("cdm1").label("负极传递属性");',
        '    model.component("comp1").physics("tds").feature("cdm1").set("DiffusionMaterialList", "mat2");',
        '    model.component("comp1").physics("tds").feature("cdm1").set("D_c_mat", "userdef");',
        "",

        '    model.component("comp1").physics("tds").feature("init1").label("负极初始值");',
        '    model.component("comp1").physics("tds").feature("init1").setIndex("initc", "csinit_neg", 0);',
        "",

        '    model.component("comp1").physics("tds").create("cdm2", "ConvectionDiffusionMigration", 2);',
        '    model.component("comp1").physics("tds").feature("cdm2").label("正极传递属性");',
        '    model.component("comp1").physics("tds").feature("cdm2").selection().named("geom1_uni_pos_particles_dom");',
        '    model.component("comp1").physics("tds").feature("cdm2").set("DiffusionMaterialList", "mat3");',
        '    model.component("comp1").physics("tds").feature("cdm2").set("D_c_mat", "userdef");',
        "",

        '    model.component("comp1").physics("tds").create("init2", "init", 2);',
        '    model.component("comp1").physics("tds").feature("init2").label("正极初始值");',
        '    model.component("comp1").physics("tds").feature("init2").selection().named("geom1_uni_pos_particles_dom");',
        '    model.component("comp1").physics("tds").feature("init2").setIndex("initc", "csinit_pos", 0);',
        "",

        '    model.component("comp1").physics("tds").create("eeic1", "ElectrodeElectrolyteInterfaceCoupling", 1);',
        '    model.component("comp1").physics("tds").feature("eeic1").label("正极表面耦合");',
        '    model.component("comp1").physics("tds").feature("eeic1").selection().named("geom1_int_pos_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("tds").feature("eeic1").feature("rc1").set("iloc_src", "root.comp1.liion.bei1.er1.iloc");',
        '    model.component("comp1").physics("tds").feature("eeic1").feature("rc1").setIndex("Vib", 1, 0);',
        "",

        '    model.component("comp1").physics("tds").create("eeic2", "ElectrodeElectrolyteInterfaceCoupling", 1);',
        '    model.component("comp1").physics("tds").feature("eeic2").label("负极表面耦合");',
        '    model.component("comp1").physics("tds").feature("eeic2").selection().named("geom1_int_neg_particle_electrolyte_bnd");',
        '    model.component("comp1").physics("tds").feature("eeic2").feature("rc1").set("iloc_src", "root.comp1.liion.bei2.er1.iloc");',
        '    model.component("comp1").physics("tds").feature("eeic2").feature("rc1").setIndex("Vib", 1, 0);',
        "",
    ])

    lines.extend(_method_footer())
    return lines
def _build_liion_concentration_links_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildLiionConcentrationLinks"))

    lines.extend([
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("MaterialOption", "mat3");',
        '    model.component("comp1").physics("liion").feature("bei1").feature("er1").set("minput_concentration_src", "root.comp1.c");',
        "",
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("MaterialOption", "mat2");',
        '    model.component("comp1").physics("liion").feature("bei2").feature("er1").set("minput_concentration_src", "root.comp1.c");',
        "",
    ])

    lines.extend(_method_footer())
    return lines

def _build_probes_method() -> List[str]:
\
\
\
\
       
    lines: List[str] = []
    lines.extend(_method_header("buildProbes"))

    lines.extend([
        '    model.component("comp1").probe().create("bnd1", "Boundary");',
        '    model.component("comp1").probe("bnd1").label("电势探针");',
        '    model.component("comp1").probe("bnd1").selection().named("geom1_ccur_pos_particles_bnd");',
        '    model.component("comp1").probe("bnd1").set("intsurface", true);',
        '    model.component("comp1").probe("bnd1").set("expr", "phis");',
        '    model.component("comp1").probe("bnd1").set("descr", "正极集流体电势");',
        "",
    ])

    lines.extend(_method_footer())
    return lines
def _advanced_float(case: ModelCase, key: str, default: float) -> float:
    value = case.electrochem_params.get(key, default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _advanced_int(case: ModelCase, key: str, default: int) -> int:
    value = case.electrochem_params.get(key, default)
    try:
        return int(value)
    except Exception:
        return int(default)


def _advanced_mesh_hauto(case: ModelCase) -> int:
    value = case.electrochem_params.get("mesh_hauto", 5)
    try:
        value_int = int(value)
    except Exception:
        value_int = 5
    return max(1, min(8, value_int))


def _build_time_study_method(case: ModelCase) -> List[str]:
    time_step = _advanced_float(case, "time_step", 2.0)
    if time_step <= 0:
        time_step = 2.0

    lines: List[str] = []
    lines.extend(_method_header("buildTimeStudy"))

    lines.extend([
        '    model.study().create("std2");',
        '    model.study("std2").label("放电研究");',
        '    model.study("std2").create("cdi", "CurrentDistributionInitialization");',
        '    model.study("std2").feature("cdi").set("solnum", "auto");',
        '    model.study("std2").feature("cdi").set("notsolnum", "auto");',
        '    model.study("std2").feature("cdi").set("outputmap", new String[]{});',
        '    model.study("std2").feature("cdi").set("ngenAUX", "1");',
        '    model.study("std2").feature("cdi").set("goalngenAUX", "1");',
        '    model.study("std2").feature("cdi").set("initType", "secondary");',
        "",
        '    model.study("std2").create("time", "Transient");',
        '    model.study("std2").feature("time").label("时间依赖");',
        '    model.study("std2").feature("time").set("initialtime", "0");',
        '    model.study("std2").feature("time").set("solnum", "auto");',
        '    model.study("std2").feature("time").set("notsolnum", "auto");',
        '    model.study("std2").feature("time").set("outputmap", new String[]{});',
        f'    model.study("std2").feature("time").set("tlist", "range(0,{time_step:g},3600/C)");',
        "",
        '    model.study("std2").setGenPlots(false);',
        '    model.study("std2").setGenConv(true);',
        '    model.study("std2").createAutoSequences("all");',
        "",
    ])

    lines.extend(_method_footer())
    return lines


def _build_poststudy_adjustments_method(case: ModelCase) -> List[str]:
    stationary_max_iter = _advanced_int(case, "stationary_max_iter", 100)
    transient_max_iter = _advanced_int(case, "transient_max_iter", 100)
    cutoff_voltage = _advanced_float(case, "cutoff_voltage", 3.3)

    lines: List[str] = []
    lines.extend(_method_header("buildPostStudyAdjustments"))

    lines.extend([
        f'    model.sol("sol1").feature("s1").feature("fc1").set("maxiter", {stationary_max_iter});',
        '    try {',
        f'      model.sol("sol1").feature("t1").feature("fc1").set("maxiter", {transient_max_iter});',
        '    } catch (Exception e) {',
        '      System.out.println("Transient maxiter setting skipped: " + e.getMessage());',
        '    }',
        '    model.sol("sol1").feature("t1").create("st1", "StopCondition");',
        '    model.sol("sol1").feature("t1").feature("st1").setIndex("stopcondarr", "", 0);',
        '    model.sol("sol1").feature("t1").feature("st1").setIndex("stopcondterminateon", "true", 0);',
        '    model.sol("sol1").feature("t1").feature("st1").setIndex("stopcondActive", true, 0);',
        '    model.sol("sol1").feature("t1").feature("st1").setIndex("stopconddesc", "停止表达式 1", 0);',
        f'    model.sol("sol1").feature("t1").feature("st1").setIndex("stopcondarr", "comp1.bnd1<{cutoff_voltage:g}", 0);',
        "",
    ])

    lines.extend(_method_footer())
    return lines


def _build_mesh_method(case: ModelCase) -> List[str]:
    mesh_hauto = _advanced_mesh_hauto(case)
    lines: List[str] = []
    lines.extend(_method_header("buildMesh"))

    lines.extend([
        '    model.component("comp1").mesh().create("mesh1");',
        '    model.component("comp1").mesh("mesh1").automatic(true);',
        f'    model.component("comp1").mesh("mesh1").autoMeshSize({mesh_hauto});',
        '    model.component("comp1").mesh("mesh1").run();',
        "",
    ])

    lines.extend(_method_footer())
    return lines
def _escape_java_string(value: str | Path) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _build_result_exports_method(model_dir: str) -> List[str]:
    java_dir = Path(model_dir)
    result_dir = java_dir.parent / "results"
    result_csv = result_dir / "discharge_voltage.csv"

    result_dir_java = _escape_java_string(result_dir.as_posix())
    result_csv_java = _escape_java_string(result_csv.as_posix())

    lines: List[str] = []
    lines.extend(_method_header("buildResultExports"))

    lines.extend([
        f'    java.io.File resultDir = new java.io.File("{result_dir_java}");',
        '    resultDir.mkdirs();',
        f'    java.io.File resultFile = new java.io.File("{result_csv_java}");',
        '    System.out.println("CSV result file: " + resultFile.getAbsolutePath());',
        "",
        '    model.result().table().create("tbl_discharge", "Table");',
        '    model.result().table("tbl_discharge").label("discharge_voltage");',
        "",
        '    model.result().numerical().create("gev_discharge", "EvalGlobal");',
        '    model.result().numerical("gev_discharge").set("data", "dset1");',
        '    model.result().numerical("gev_discharge").set("table", "tbl_discharge");',
        '    model.result().numerical("gev_discharge").set("expr", new String[]{"comp1.bnd1"});',
        '    model.result().numerical("gev_discharge").set("descr", new String[]{"positive collector potential"});',
        '    model.result().numerical("gev_discharge").setResult();',
        "",
        '    model.result().table("tbl_discharge").save(resultFile.getAbsolutePath());',
        '    System.out.println("CSV exists after save: " + resultFile.exists());',
        "",
    ])

    lines.extend(_method_footer())
    return lines
def _build_wave_functions_method() -> List[str]:
    lines: List[str] = []
    lines.extend(_method_header("buildWaveFunctions"))
    lines.extend(_method_footer())
    return lines
def model_case_to_java_lines(
    case: ModelCase,
    *,
    class_name: str,
    model_dir: str,
    run_study: bool = True,
    export_results: bool = True,
) -> List[str]:
    lines: List[str] = []
    model_dir_java = _escape_java_string(model_dir)
    case_name_java = _escape_java_string(case.case_name)

    lines.extend([
        "import com.comsol.model.*;",
        "import com.comsol.model.util.*;",
        "",
        f"public class {class_name} {{",
        "",
    ])

    lines.extend(_build_boundary_cumulative_selections_method())
    lines.extend(_build_domain_cumulative_selections_method())
    lines.extend(_build_regions_method(case))
    lines.extend(_build_particle_method("buildNegativeParticles", case.negative_particles))
    lines.extend(_build_particle_method("buildPositiveParticles", case.positive_particles))
    lines.extend(_build_binder_methods("buildNegativeBinders", case.negative_binders, chunk_size=120))
    lines.extend(_build_binder_methods("buildPositiveBinders", case.positive_binders, chunk_size=120))
    lines.extend(_build_particle_curve_source_unions_method(case))
    lines.extend(_build_domain_booleans_method(case))
    lines.extend(_build_region_curve_geometries_method())
    lines.extend(_build_collector_strip_rectangles_method(case))
    lines.extend(_build_collector_boundary_geometries_method(case))
    lines.extend(_build_particle_electrolyte_boundary_geometries_method())

    lines.extend(_build_global_parameters_method(case))

    lines.extend(_build_derived_variables_method())
    lines.extend(_build_wave_functions_method())
    lines.extend(_build_materials_method(model_dir))

    lines.extend(_build_liion_skeleton_method(case))
    lines.extend(_build_tds_skeleton_method())
    lines.extend(_build_liion_concentration_links_method())
    lines.extend(_build_probes_method())
    lines.extend(_build_mesh_method(case))
    lines.extend(_build_time_study_method(case))
    lines.extend(_build_poststudy_adjustments_method(case))
    if export_results:
        lines.extend(_build_result_exports_method(model_dir))

    lines.extend([
        "  public static Model run() {",
        f'    Model model = ModelUtil.create("{case_name_java}");',
        f'    model.modelPath("{model_dir_java}");',
        f'    model.label("{case_name_java}.mph");',
        '    model.component().create("comp1", true);',
        '    model.component("comp1").geom().create("geom1", 2);',
        f'    model.component("comp1").geom("geom1").lengthUnit("{case.unit}");',
        '    model.component("comp1").geom("geom1").useConstrDim(false);',
        "",
        "    buildBoundaryCumulativeSelections(model);",
        "    buildDomainCumulativeSelections(model);",
        "    buildRegions(model);",
        "    buildNegativeParticles(model);",
        "    buildPositiveParticles(model);",
        "    buildNegativeBinders(model);",
        "    buildPositiveBinders(model);",
        "    buildParticleCurveSourceUnions(model);",
        "    buildDomainBooleans(model);",
        "    buildRegionCurveGeometries(model);",
        "    buildCollectorStripRectangles(model);",
        "    buildCollectorBoundaryGeometries(model);",
        "    buildParticleElectrolyteBoundaryGeometries(model);",
        "",
        '    model.component("comp1").geom("geom1").run("fin");',
        "",
        "    buildGlobalParameters(model);",
        "    buildDerivedVariables(model);",
        "    buildWaveFunctions(model);",
        "    buildMaterials(model);",
        "    buildLiionSkeleton(model);",
        "    buildTdsSkeleton(model);",
        "    buildLiionConcentrationLinks(model);",
        "    buildProbes(model);",
        "    buildMesh(model);",
        "    buildTimeStudy(model);",
        "    buildPostStudyAdjustments(model);",
    ])

    if run_study:
        lines.append('    model.study("std2").run();')
        if export_results:
            lines.append("    buildResultExports(model);")
    else:
        lines.append('    System.out.println("Model-only mode: study is not run.");')

    lines.extend([
        "    return model;",
        "  }",
        "",
        "  public static void main(String[] args) {",
        "    run();",
        "  }",
        "}",
        "",
    ])

    return lines


def write_model_case_to_java(
    case: ModelCase,
    output_path: str | Path,
    *,
    run_study: bool = True,
    export_results: bool = True,
) -> Path:
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _write_auxiliary_material_files(output_path.parent)

    class_name = _java_identifier_from_filename(output_path.stem)
    model_dir = output_path.parent.as_posix()

    lines = model_case_to_java_lines(
        case,
        class_name=class_name,
        model_dir=model_dir,
        run_study=run_study,
        export_results=export_results,
    )

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    return output_path
