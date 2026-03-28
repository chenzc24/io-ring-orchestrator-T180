# IO Ring Orchestrator Scripts

This directory contains standalone CLI wrapper scripts for AMS-IO-Agent tools.

## Overview

These scripts provide command-line access to AMS-IO-Agent's IO Ring generation tools. They are organized into two tiers:

### Tier 1: Standalone Scripts (No Dependencies)
- **validate_intent.py** - Validate intent graph JSON files
  - Uses Python stdlib only
  - Works without AMS-IO-Agent

### Tier 2: AMS-IO-Agent Wrappers (Requires Installation)
- **build_confirmed_config.py** - Build confirmed configuration
- **generate_schematic.py** - Generate schematic SKILL code
- **generate_layout.py** - Generate layout SKILL code
- **check_virtuoso_connection.py** - Check Virtuoso connectivity
- **run_il_with_screenshot.py** - Execute SKILL in Virtuoso
- **run_drc.py** - Run Design Rule Check
- **run_lvs.py** - Run Layout vs Schematic check

---

## Setup

### For Tier 1 (Validation Only)

No setup needed! Just run:
```bash
python3 validate_intent.py your_file.json
```

### For Tier 2 (Full Features)

**Option 1: Set Environment Variable**
```bash
export AMS_IO_AGENT_PATH=/path/to/AMS-IO-Agent
```

**Option 2: Install AMS-IO-Agent**
```bash
cd /path/to/AMS-IO-Agent
pip install -r requirements.txt
```

The scripts will automatically search these locations:
1. `$AMS_IO_AGENT_PATH` (if set)
2. `/home/chenzc_intern25/AMS-IO-Agent_processes_combined/AMS-IO-Agent`
3. `../../../AMS-IO-Agent` (relative to script)
4. `../../AMS-IO-Agent` (relative to script)

---

## Usage Guide

### 1. Validate Intent Graph

```bash
python3 validate_intent.py io_ring_intent_graph.json
```

**Exit codes:**
- 0: Validation passed
- 1: Validation failed
- 2: File or JSON error

**Example output:**
```
✅ Intent graph validation passed!
   Validation passed: 52 pads, 0 corners
```

---

### 2. Build Confirmed Config

```bash
python3 build_confirmed_config.py \
    io_ring_intent_graph.json \
    io_ring_confirmed.json \
    T28
```

**Arguments:**
- `intent_graph.json` - Input intent graph file
- `output_confirmed.json` - Output confirmed config file
- `process_node` - Optional: T28 or T180 (default: T28)

---

### 3. Generate Schematic

```bash
python3 generate_schematic.py \
    io_ring_confirmed.json \
    schematic.il \
    T28
```

**Arguments:**
- `config.json` - Input confirmed config file
- `output.il` - Output schematic SKILL file
- `process_node` - Optional: T28 or T180 (default: T28)

---

### 4. Generate Layout

```bash
python3 generate_layout.py \
    io_ring_confirmed.json \
    layout.il \
    T28
```

**Arguments:**
- `config.json` - Input confirmed config file
- `output.il` - Output layout SKILL file
- `process_node` - Optional: T28 or T180 (default: T28)

---

### 5. Check Virtuoso Connection

```bash
python3 check_virtuoso_connection.py
```

**Exit codes:**
- 0: Virtuoso is connected
- 1: Virtuoso not connected

**Example output:**
```
🔧 Checking Virtuoso connection...
✅ Virtuoso is running and accessible
```

---

### 6. Run SKILL with Screenshot

```bash
python3 run_il_with_screenshot.py \
    schematic.il \
    MyLib \
    MyCell \
    screenshot.png \
    schematic
```

**Arguments:**
- `il_file` - SKILL file to execute
- `lib` - Virtuoso library name
- `cell` - Virtuoso cell name
- `screenshot_path` - Optional: Output screenshot path
- `view` - Optional: schematic or layout (default: layout)

---

### 7. Run DRC

```bash
python3 run_drc.py MyLib MyCell layout T28
```

**Arguments:**
- `lib` - Virtuoso library name
- `cell` - Virtuoso cell name
- `view` - Optional: View name (default: layout)
- `tech_node` - Optional: T28 or T180 (default: T28)

**Exit codes:**
- 0: DRC passed
- 1: DRC failed

---

### 8. Run LVS

```bash
python3 run_lvs.py MyLib MyCell layout T28
```

**Arguments:**
- `lib` - Virtuoso library name
- `cell` - Virtuoso cell name
- `view` - Optional: View name (default: layout)
- `tech_node` - Optional: T28 or T180 (default: T28)

**Exit codes:**
- 0: LVS passed
- 1: LVS failed

---

## Complete Workflow Example

```bash
# Step 1: Validate intent graph
python3 validate_intent.py io_ring.json

# Step 2: Build confirmed config
python3 build_confirmed_config.py io_ring.json io_ring_confirmed.json T28

# Step 3: Generate schematic
python3 generate_schematic.py io_ring_confirmed.json schematic.il T28

# Step 4: Generate layout
python3 generate_layout.py io_ring_confirmed.json layout.il T28

# Step 5: Check Virtuoso
python3 check_virtuoso_connection.py

# Step 6: Execute schematic in Virtuoso
python3 run_il_with_screenshot.py schematic.il MyLib MyCell sch.png schematic

# Step 7: Execute layout in Virtuoso
python3 run_il_with_screenshot.py layout.il MyLib MyCell layout.png layout

# Step 8: Run DRC
python3 run_drc.py MyLib MyCell layout T28

# Step 9: Run LVS
python3 run_lvs.py MyLib MyCell layout T28
```

---

## Troubleshooting

### Error: AMS-IO-Agent not found

**Solution 1:** Set environment variable
```bash
export AMS_IO_AGENT_PATH=/actual/path/to/AMS-IO-Agent
```

**Solution 2:** Verify AMS-IO-Agent location
```bash
ls /home/chenzc_intern25/AMS-IO-Agent_processes_combined/AMS-IO-Agent
```

### Error: Could not import AMS-IO-Agent tools

**Check dependencies are installed:**
```bash
cd /path/to/AMS-IO-Agent
pip install -r requirements.txt
```

**Verify Python version:**
```bash
python3 --version  # Should be 3.7+
```

### Error: Virtuoso not connected

**Check Virtuoso is running:**
```bash
ps aux | grep virtuoso
```

**Start Virtuoso if needed** (consult Virtuoso documentation)

---

## Using from Claude Code Skills

Skills automatically reference these scripts:

```python
import subprocess
import sys

# Example: Validation
result = subprocess.run(
    [sys.executable, f"{skill_path}/scripts/validate_intent.py", json_file],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Validation passed!")
else:
    print(f"❌ Validation failed:\n{result.stdout}")
```

---

## Script Features

All scripts include:
- ✅ Clear usage messages
- ✅ Proper error handling
- ✅ Exit codes (0=success, 1=failure, 2=setup error)
- ✅ Automatic AMS-IO-Agent path detection
- ✅ Helpful error messages
- ✅ Progress indicators

---

## Dependencies

### Tier 1 Scripts
- Python 3.7+ (stdlib only)

### Tier 2 Scripts
- Python 3.7+
- AMS-IO-Agent installation
- AMS-IO-Agent dependencies (from requirements.txt)
- Virtuoso (for execution/DRC/LVS scripts)

---

## File Organization

```
scripts/
├── README.md (this file)
├── requirements.txt
│
├── validate_intent.py         (Tier 1 - Standalone)
│
├── build_confirmed_config.py  (Tier 2 - AMS-IO-Agent)
├── generate_schematic.py      (Tier 2 - AMS-IO-Agent)
├── generate_layout.py         (Tier 2 - AMS-IO-Agent)
├── check_virtuoso_connection.py  (Tier 2 - AMS-IO-Agent + Virtuoso)
├── run_il_with_screenshot.py     (Tier 2 - AMS-IO-Agent + Virtuoso)
├── run_drc.py                    (Tier 2 - AMS-IO-Agent + Virtuoso)
└── run_lvs.py                    (Tier 2 - AMS-IO-Agent + Virtuoso)
```

---

## Version

**Created:** 2026-03-16
**Skills Version:** 4.0
**Compatible with:** AMS-IO-Agent 1.0+

---

For more information, see:
- Parent skill: `../SKILL.md`
- Setup guide: `../references/ams_io_agent_setup.md` (when available)
- Skill documentation: `../../../../README.md`
