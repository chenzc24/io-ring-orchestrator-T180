# IO Ring Orchestrator Scripts — T180

CLI wrapper scripts for T180 IO Ring generation tools.

## Overview

These scripts provide command-line access to T180 IO Ring generation. They are organized into two tiers:

### Tier 1: Standalone Scripts (No Dependencies)
- **validate_intent.py** — Validate intent graph JSON files (stdlib only)

### Tier 2: Bridge-Dependent Scripts (Requires virtuoso-bridge-lite)
- **build_confirmed_config.py** — Build confirmed configuration
- **generate_schematic.py** — Generate schematic SKILL code
- **generate_layout.py** — Generate layout SKILL code
- **check_virtuoso_connection.py** — Check Virtuoso connectivity
- **run_il_with_screenshot.py** — Execute SKILL in Virtuoso
- **run_drc.py** — Run Design Rule Check
- **run_lvs.py** — Run Layout vs Schematic check

---

## Prerequisites

### virtuoso-bridge-lite (Required for Tier 2)

Install from source into the project's `.venv`:

```bash
.venv/bin/pip install -e /path/to/virtuoso-bridge-lite
```

After installing, initialize and start the bridge:

```bash
virtuoso-bridge init     # Creates ~/.virtuoso-bridge/.env
virtuoso-bridge start    # Starts SSH tunnel + daemon
```

### Python Dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

---

## Usage

All Tier 2 scripts should be invoked via `$AMS_PYTHON` (resolved in Step 0 of SKILL.md).

### 1. Validate Intent Graph

```bash
python validate_intent.py io_ring_intent_graph.json
```

### 2. Build Confirmed Config

```bash
$AMS_PYTHON build_confirmed_config.py io_ring_intent_graph.json io_ring_confirmed.json --skip-editor
```

### 3. Generate Schematic

```bash
$AMS_PYTHON generate_schematic.py io_ring_confirmed.json schematic.il
```

### 4. Generate Layout

```bash
$AMS_PYTHON generate_layout.py io_ring_confirmed.json layout.il
```

### 5. Check Virtuoso Connection

```bash
$AMS_PYTHON check_virtuoso_connection.py
```

### 6. Run SKILL with Screenshot

```bash
$AMS_PYTHON run_il_with_screenshot.py schematic.il MyLib MyCell screenshot.png schematic
```

### 7. Run DRC

```bash
$AMS_PYTHON run_drc.py MyLib MyCell layout T180
```

### 8. Run LVS

```bash
$AMS_PYTHON run_lvs.py MyLib MyCell layout T180
```

---

## Exit Codes

All scripts use:
- **0** — Success
- **1** — Tool execution error (DRC/LVS failure, Virtuoso error, etc.)
- **2** — Import/setup error (missing file, missing dependency)
