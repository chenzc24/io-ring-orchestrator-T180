---
name: io-ring-orchestrator-T180
description: Master coordinator for complete T180 (180nm) IO Ring generation. Orchestrates signal classification, device mapping, pin configuration, JSON generation, and complete workflow through DRC/LVS verification.
---

# IO Ring Orchestrator - T180

You are the master coordinator for T180 IO Ring generation. You orchestrate specialized skills and tools to complete the end-to-end workflow.

## Prerequisites

This skill uses a **hybrid approach** with two tiers of functionality:

### Tier 1: Bundled Scripts (Always Available)
These scripts are bundled with this skill and work standalone:
- **validate_intent.py** - JSON validation (no external dependencies)

Located at: `<skill_path>/scripts/`

### Tier 2: Optional AMS-IO-Agent Tools
For advanced features (schematic/layout generation, Virtuoso execution), you need AMS-IO-Agent installed.

See `references/ams_io_agent_setup.md` for installation instructions (when available).

**Note:** You can still use this skill for classification, mapping, and JSON generation without AMS-IO-Agent. The workflow will stop at validation if advanced tools are not available.

## Your Mission

Guide Claude Code through the complete IO Ring generation workflow by:
1. Invoking specialized T180 skills in sequence
2. Passing data between skills
3. Using bundled scripts for validation
4. Calling optional Python tools for advanced features
5. Reporting results to user

## Complete Workflow

Follow the same workflow as T28 orchestrator, but invoke T180-specific skills:

### Steps 1-6: Invoke T180 Skills

1. **signal-classifier-T180** - Classify signals
2. **device-mapper-T180** - Map to T180 devices
3. **direction-determiner-T180** - Determine directions
4. **pin-configurator-T180** - Configure pins
5. **corner-selector-T180** - Select corners (T180 uses single PCORNER type)
6. **json-constructor-T180** - Build JSON

### Step 7: Validate JSON

**Use bundled validation script:**
```python
import subprocess
import sys

# Get the skill path (this will be available in the execution context)
skill_path = "<skill_path>"  # Path to this skill directory
script_path = f"{skill_path}/scripts/validate_intent.py"

# Run validation
result = subprocess.run(
    [sys.executable, script_path, intent_graph_path],
    capture_output=True,
    text=True
)

# Check exit code
if result.returncode == 0:
    print(result.stdout)  # Shows ✅ message
else:
    print(result.stdout)  # Shows ❌ message with details
    # Stop workflow on validation failure
    raise ValueError("Intent graph validation failed")
```

**Alternative (if AMS-IO-Agent is available):**
```python
# Can also use the Python tool for more detailed validation
validate_intent_graph(config_file_path=intent_graph_path)
```

### Steps 8-14: Advanced Features (Requires AMS-IO-Agent)

If AMS-IO-Agent is available, call Python tools with `process_node="T180"`:

8. `build_io_ring_confirmed_config(...)` - Build confirmed config
9. `generate_io_ring_schematic(...)` - Generate schematic
10. `generate_io_ring_layout(...)` - Generate layout
11. `check_virtuoso_connection()` - Check Virtuoso
12. `run_il_with_screenshot(...)` - Execute and capture
13. `run_drc(...)` - DRC check
14. `run_lvs(...)` - LVS check

## T180-Specific Details

### Devices
- **Analog IO:** PVDD1ANA / PVSS1ANA (vs PDB3AC in T28)
- **Digital IO:** PDDW0412SCDG (vs PDDW16SDGZ in T28)
- **Corners:** PCORNER (single type, vs PCORNER_G/PCORNERA_G in T28)

### DRC Rules
- Minimum spacing: ≥ 0.28 µm
- Minimum width: ≥ 0.28 µm
- Metal layers: METAL1-METAL5

## Error Handling

If any skill invocation fails:
1. Report which skill failed
2. Show error message
3. Show intermediate results collected so far
4. Suggest next steps

## Example Usage

User: "Generate T180 IO ring with signals A, B, C. Clockwise, 3x3."

Orchestrator:
1. Invokes signal-classifier-T180 → classifies signals
2. Invokes device-mapper-T180 → maps to T180 devices
3. Invokes direction-determiner-T180 → determines directions
4. Invokes pin-configurator-T180 → generates pin configs
5. Invokes corner-selector-T180 → selects PCORNER for all corners
6. Invokes json-constructor-T180 → builds JSON
7. Validates with bundled script → PASSED
8-14. (If AMS-IO-Agent available) Generates and executes designs

For detailed workflow steps, see T28 orchestrator SKILL.md.
