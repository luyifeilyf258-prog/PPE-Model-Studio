# PPE Model Studio
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21194303.svg)](https://doi.org/10.5281/zenodo.21194303)

PPE Model Studio is a local desktop application for constructing and previewing two-dimensional particle-packed electrode models for lithium-ion batteries. 

Current version: `v1.0.1`

## Main Features

- Read, edit, and save YAML configuration files
- Generate two-dimensional positive/negative electrode particle and binder structures
- Preview the generated model structure in the graphical interface
- Export structure preview images and ModelCase JSON files
- Generate COMSOL Java model files
- Compile and run models through COMSOL batch tools
- Export COMSOL MPH files and simulation result CSV files
- Import one or more CSV files and plot voltage curves

## Download

Users can download the fixed release package from the GitHub Releases page:

```text
https://github.com/luyifeilyf258-prog/PPE-Model-Studio/releases
```

Recommended installer:

```text
PPE_Model_Studio_v1.0.0_Setup.exe
```

## Installation and Startup

Steps:

1. Double-click the installer.
2. Follow the installation wizard.
3. Start `PPE Model Studio` from the desktop shortcut or the Start menu.

## User Environment Requirements

The packaged version already includes the required Python runtime and dependencies.

Recommended system:

```text
Windows 10/11 64-bit
```

The following functions do not require COMSOL:

- Open and edit YAML files
- Validate parameters
- Generate the model structure
- Preview the structure
- Export preview images
- Import CSV files and plot voltage curves

The following functions require COMSOL:

- Generate COMSOL model files
- Run COMSOL simulations
- Export MPH model files
- Export simulation result CSV files

## COMSOL Path Configuration

COMSOL Multiphysics is not included in this software. Users must install COMSOL separately and ensure that a valid COMSOL license is available.

To configure COMSOL paths in the software:

```text
Calculation -> Configure COMSOL Path...
```

Select the following two executable files:

```text
comsolcompile.exe
comsolbatch.exe
```

Common path examples:

```text
C:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolcompile.exe
C:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolbatch.exe
```

The actual path may vary depending on the local COMSOL installation. After configuration, use:

```text
Calculation -> Check COMSOL Path
```

to verify the paths.

## Quick Start

A typical first run follows these steps:

1. Start `PPE Model Studio`.
2. Open the example configuration file:

```text
config/case_demo.yaml
```

3. Check or modify the parameters.
4. Validate the parameters:

```text
Parameter -> Validate Parameters
```

5. Click:

```text
Generate Model
```

to generate the two-dimensional structure preview.

6. To use COMSOL functions, configure and check the COMSOL paths first.
7. Click:

```text
Generate Model File Only
```

to generate an MPH file that can be opened in COMSOL.

8. Or click:

```text
Run COMSOL
```

to perform the full simulation workflow.

## Output Files

Each run creates an independent folder under `output/runs/`:

```text
output/runs/run_YYYYMMDD_HHMMSS/
```

Typical output files include:

```text
json/case_preview.json
preview/case_preview.png
java/PPE_model.java
logs/comsol_batch.log
mph/case_demo.mph
results/discharge_voltage.csv
```

Folder meanings:

- `json/`: model structure data
- `preview/`: structure preview image
- `java/`: COMSOL Java file
- `logs/`: run logs
- `mph/`: COMSOL model file
- `results/`: simulation result CSV files

## Example Configuration

The default demonstration file is:

```text
config/case_demo.yaml
```

When creating a new case, it is recommended to keep the original example file unchanged and save a new YAML file, for example:

```text
case_1C.yaml
case_high_porosity.yaml
case_large_particle.yaml
```

## Citation

If you use this software, please cite the archived software release:

PPE Model Builder, version 1.0.1. Zenodo. https://doi.org/10.5281/zenodo.21194303


## License

This project is distributed under the GNU General Public License v3.0.

The graphical user interface depends on PyQt6. COMSOL Multiphysics is not included in this software and must be installed separately by users.
