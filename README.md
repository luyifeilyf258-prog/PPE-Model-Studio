# PPE Model Studio

PPE Model Studio is a local desktop application for constructing and previewing two-dimensional particle-packed electrode models for lithium-ion batteries. It supports YAML-based parameter configuration, particle/binder structure generation, COMSOL Java model export, COMSOL batch execution, and CSV result plotting.

Current version: `v1.0.0`

## Main Features

- Read, edit, and save YAML configuration files
- Generate two-dimensional positive/negative electrode particle and binder structures
- Preview the generated model structure in the graphical interface
- Export structure preview images and ModelCase JSON files
- Generate COMSOL Java model files
- Compile and run models through COMSOL batch tools
- Export COMSOL MPH files and simulation result CSV files
- Import one or more CSV files and plot voltage curves
- Configure and check local COMSOL executable paths in the software

## Download

Users can download the fixed release package from the GitHub Releases page:

```text
https://github.com/<your-username>/<your-repository>/releases
```

Recommended installer:

```text
PPE_Model_Studio_v1.0.0_Setup.exe
```

Alternatively, users may download the folder-based Windows package:

```text
PPE_Model_Studio_v1.0.0_Windows.zip
```

Replace `<your-username>` and `<your-repository>` with the actual GitHub account and repository name.

## Installation and Startup

### Option 1: Installer Package

If you downloaded the installer:

```text
PPE_Model_Studio_v1.0.0_Setup.exe
```

Steps:

1. Double-click the installer.
2. Follow the installation wizard.
3. Start `PPE Model Studio` from the desktop shortcut or the Start menu.

### Option 2: Folder Package

If you downloaded the folder-based ZIP package, extract it first. The extracted folder should look similar to:

```text
PPE_Model_Studio/
├─ PPE_Model_Studio.exe
├─ _internal/
├─ config/
└─ output/
```

Start the software by double-clicking:

```text
PPE_Model_Studio.exe
```

Do not copy only `PPE_Model_Studio.exe`. The complete `PPE_Model_Studio` folder must be kept, otherwise the program may not start correctly.

## User Environment Requirements

For the installer or folder-based package, normal users do not need to install Python or Python packages manually. The packaged version already includes the required Python runtime and dependencies.

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

## Run from Source

To run from source, install Python first and execute the following commands in the project root directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If the startup file is not `main.py`, replace it with the actual entry file.

Main dependencies include:

```text
numpy
scipy
matplotlib
PyYAML
pandas
PyQt6
```

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

9. After the simulation is completed, import the CSV result file to plot the voltage curve.

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

## Troubleshooting

### The software does not start

Make sure you did not copy only the `.exe` file. For the folder package, `_internal`, `config`, and `output` must be kept with the executable.

### COMSOL cannot be found

Reconfigure the paths to `comsolcompile.exe` and `comsolbatch.exe` in the software, and make sure that the COMSOL license is available.

### No CSV result is generated

Check whether the COMSOL run finished successfully and inspect:

```text
output/runs/run_xxx/logs/comsol_batch.log
```

### No curve appears after importing CSV

Make sure the selected file is a valid result file, such as:

```text
output/runs/run_xxx/results/discharge_voltage.csv
```

## License

This project is distributed under the GNU General Public License v3.0.

The graphical user interface depends on PyQt6. COMSOL Multiphysics is not included in this project and must be installed separately by users.

## Citation

If you use this software in a publication, report, or teaching material, please cite the associated article and the archived software DOI.

```text
PPE Model Studio, version 1.0.0. Zenodo, 2026. https://doi.org/<Zenodo DOI>
```

Replace `<Zenodo DOI>` with the DOI generated after the official archived release.
