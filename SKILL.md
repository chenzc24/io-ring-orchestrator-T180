---
name: io-ring-orchestrator-T180
description: Master coordinator for complete T180 (180nm) IO Ring generation. Handles signal classification, device mapping, pin configuration, JSON generation, and complete workflow through DRC/LVS verification. Use this skill for any T180 IO Ring generation task. Trigger when user mentions T180, 180nm, 180nm IO ring, or any IO ring task targeting the 180nm process node.
---

# IO Ring Orchestrator - T180

You are the master coordinator for T180 (180nm) IO Ring generation. You handle the **entire** workflow as a single skill — from parsing requirements through DRC/LVS verification.

## Scripts Path verification

```bash

SCRIPTS_PATH="/absolute_path/to/io-ring-orchestrator-T180/scripts"

# Verify:
ls "$SCRIPTS_PATH/validate_intent.py" || echo "ERROR: SCRIPTS_PATH not found"
```

## Entry Points

- **User provides text requirements only** → Start at Step 0, then continue directly to Step 2 (Draft) and Step 3 (Enrichment)
- **User provides image input (with or without text)** → Start at Step 0, then run Step 1 (Image Input Processing), then continue directly to Step 2 (Draft) and Step 3 (Enrichment)
- **User provides draft intent graph file** → Skip to Step 3 (Enrichment)
- **User provides final intent graph file** → Skip to Step 5 (Validation)
- Determine entry path automatically. Do NOT run any pre-step wizard eligibility/opt-in flow.

## Output Path Contract (Mandatory)

- Use a single workspace output root for the entire run.
- Create `output_dir` exactly once per run and reuse it for all Step 2-12 artifacts.
- Do not regenerate `timestamp` after Step 0.
- Export `AMS_OUTPUT_ROOT` once in Step 0 so script-level outputs remain deterministic.

Required conventions:

- `AMS_OUTPUT_ROOT`: workspace-level output root
- `output_dir`: per-run directory under `${AMS_OUTPUT_ROOT}/generated/${timestamp}`
- DRC/LVS reports: `${AMS_OUTPUT_ROOT}` and its fixed subdirs (`drc`, `lvs`)

## Complete Workflow

### Step 0: Directory Setup & Parse Input

```bash
# Resolve stable workspace root (prefer AMS_IO_AGENT_PATH, fallback to current directory)
if [ -n "${AMS_IO_AGENT_PATH:-}" ]; then
  WORK_ROOT="${AMS_IO_AGENT_PATH}"
else
  WORK_ROOT="$(pwd)"
fi

# Unified output root for script-level artifacts (DRC/LVS/PEX/screenshots fallback)
export AMS_OUTPUT_ROOT="${WORK_ROOT}/output"
mkdir -p "${AMS_OUTPUT_ROOT}/generated"

# Create per-run directory once and reuse it across all steps
if [ -n "${output_dir:-}" ] && [ -d "${output_dir}" ]; then
  echo "Reusing existing output_dir: ${output_dir}"
else
  timestamp="${timestamp:-$(date +%Y%m%d_%H%M%S)}"
  output_dir="${AMS_OUTPUT_ROOT}/generated/${timestamp}"
fi

mkdir -p "$output_dir"
echo "AMS_OUTPUT_ROOT=${AMS_OUTPUT_ROOT}"
echo "output_dir=${output_dir}"
```

Parse user input: signal list, ring dimensions (chip_width × chip_height), pad counts per side, placement order, voltage domain specifications.

### Step 1: Image Input Processing Rules (Before Step 2)

Apply this step only when image input is provided.

Rules:

1. Load image-analysis instruction from `references/image_vision_instruction.md` first.
2. Use the instruction to extract structured requirements from image(s):
  - topology (Single/Double ring)
  - counter-clockwise outer-ring signal order
  - pad count description
  - inner-pad insertion directives (if Double Ring)
3. Treat extracted structure as Step 2 input. If user text and image conflict, prefer explicit user text constraints and keep unresolved conflicts explicit in the report.
4. Keep extraction/output conventions unchanged:
  - right side is read bottom-to-top
  - top side is read right-to-left
  - ignore `PFILLER*` devices

### Step 2: Build Draft JSON (Structural Only)

Build a draft JSON with only structural fields. No device/pin/corner inference in this step.

Primary reference:

- `references/draft_builder_T180.md`

Process:

1. Parse user structural inputs (signal list, chip_width, chip_height, top_count, bottom_count, left_count, right_count, placement_order).
  - If `placement_order`/dimensions/counts cannot be uniquely resolved, ask the user directly, then continue.
2. Compute `ring_config`.
3. Generate `instances` for `pad` with only:
  - `name`
  - `position`
  - `type`
4. Save draft to `{output_dir}/io_ring_intent_graph_draft.json`.

Strict boundary:

- Do NOT add `device`, `pin_connection`, `direction`, `domain`, `view_name`, or any `corner` instance in Step 2.

### Step 3: Enrich Draft JSON to Final Intent Graph

Read the Step 2 draft and enrich in a single pass.

Mandatory inputs for Step 3:

- Step 2 draft JSON (primary source for structural fields)
- Original user prompt (source for explicit intent not encoded structurally, such as voltage-domain assignment, provider naming, and direction overrides)

Input precedence:

- Keep structural fields from Step 2 draft immutable (`ring_config`, `name`, `position`, `type`) unless a hard inconsistency is reported.
- Apply constraints in this order when they do not conflict with immutable draft structure:
  1. Explicit user prompt constraints
  2. Enrichment default inference

Primary reference:

- `references/enrichment_rules_T180.md`

Process:

1. Read `ring_config` and all draft instances (`name`, `position`, `type`) and user prompt constraints.
2. Classify each signal's domain (analog/digital) using the Mandatory Signal Classification Dictionary.
3. Add per-instance `device` based on device selection tables.
4. Add per-instance `direction` for digital IO (`PDDW0412SCDG` only).
5. Add per-instance `pin_connection` according to the Pin Configuration Matrix.
6. Add per-instance `domain`, `view_name`, `pad_width`, `pad_height`.
7. Insert 4 corners (`PCORNER`) at correct transition positions.
8. Run pre-save rule gates (must pass before saving), as defined in `references/enrichment_rules_T180.md`:
  - Continuity gate
  - Position-identity gate
  - Pin-family gate
  - VSS-consistency gate
  - Provider-count gate
9. Save final JSON to `{output_dir}/io_ring_intent_graph.json`.

Handoff rule:

- Treat draft structural fields as immutable unless a hard inconsistency must be reported.

### Step 4: Reference-Guided Gate Check (Mandatory)

Before Step 5 validation, explicitly verify Step 3 output against references:

- `references/enrichment_rules_T180.md` -> Classification Priority, Domain Isolation, Voltage Domain Logic
- `references/enrichment_rules_T180.md` -> Analog Pin Configuration, Digital Pin Configuration, Corner Rules
- `references/enrichment_rules_T180.md` -> Direction Rules, Pin-Family Gate, VSS-Consistency Gate

Also verify that Step 3 output preserves explicit constraints from the original user prompt (especially voltage-domain assignments, provider names, and direction overrides).

If any gate fails, repair JSON first and repeat Step 4. Do not proceed to Step 5.

### Step 5: Validate JSON

```bash
python3 $SCRIPTS_PATH/validate_intent.py {output_dir}/io_ring_intent_graph.json
```

- Exit 0 → proceed
- Exit 1 → enter repair loop:
  1. Read validator error messages carefully.
  2. Go back to references and query the matching rules (`references/draft_builder_T180.md` or `references/enrichment_rules_T180.md`).
  3. Apply targeted JSON fixes only for reported issues.
  4. Run validator again.
  5. Repeat until Exit 0 or a blocking inconsistency is found (then stop and report clearly).
- Exit 2 → file not found

Validation repair constraints:

- Do NOT regenerate the whole JSON unless structure is fundamentally broken.
- Preserve Step 2 immutable fields (`ring_config`, `name`, `position`, `type`) during repair.
- Every fix must be traceable to an explicit validator error and a reference rule.
- If continuity/provider-count gates fail during repair, fix classification first, then device/pin labels.

### Step 6: Build Confirmed Config

```bash
python3 $SCRIPTS_PATH/build_confirmed_config.py \
  {output_dir}/io_ring_intent_graph.json \
  {output_dir}/io_ring_confirmed.json
```

Note: `build_confirmed_config.py` is hardcoded for T180 — no process node parameter needed.

### Step 7: Generate SKILL Scripts

```bash
python3 $SCRIPTS_PATH/generate_schematic.py \
  {output_dir}/io_ring_confirmed.json \
  {output_dir}/io_ring_schematic.il

python3 $SCRIPTS_PATH/generate_layout.py \
  {output_dir}/io_ring_confirmed.json \
  {output_dir}/io_ring_layout.il
```

Note: Both scripts are hardcoded for T180 — no process node parameter needed.

### Step 8: Check Virtuoso Connection

```bash
python3 $SCRIPTS_PATH/check_virtuoso_connection.py
```

- Exit 0 → proceed
- Exit 1 → **STOP**. Report all generated files so far and instruct user to start Virtuoso. Do NOT proceed.

### Step 9: Execute SKILL Scripts in Virtuoso

```bash
python3 $SCRIPTS_PATH/run_il_with_screenshot.py \
  {output_dir}/io_ring_schematic.il \
  {lib} {cell} \
  {output_dir}/schematic_screenshot.png \
  schematic

python3 $SCRIPTS_PATH/run_il_with_screenshot.py \
  {output_dir}/io_ring_layout.il \
  {lib} {cell} \
  {output_dir}/layout_screenshot.png \
  layout
```

### Step 10: Run DRC

```bash
python3 $SCRIPTS_PATH/run_drc.py {lib} {cell} layout T180
```

- Exit 0 -> proceed to Step 11
- Exit 1 -> enter DRC repair loop:
  1. Read DRC report and extract failing rule/check locations.
  2. Map each error to reference rules (classification, device mapping, pin configuration, corner placement).
  3. Fix the source intent JSON first (`io_ring_intent_graph.json`), then re-run Step 6-10 to regenerate and recheck.
  4. Repeat until DRC passes, but allow at most 2 repair attempts; if still failing, stop and report the unresolved DRC blockers.

### Step 11: Run LVS

```bash
python3 $SCRIPTS_PATH/run_lvs.py {lib} {cell} layout T180
```

- Exit 0 -> proceed to Step 12
- Exit 1 -> enter LVS repair loop:
  1. Read LVS report and identify mismatch class (net mismatch, missing device, pin mismatch, shorts/opens).
  2. Query matching reference rules and locate the root cause in intent JSON (check continuity/provider-count gates before pin-level edits).
  3. Fix intent JSON by returning to Step 3 checks/fixes first, then re-run Step 3-11 (enrich, gate-check, validate, build, generate, execute, DRC, LVS).
  4. Repeat until LVS passes, but allow at most 2 repair attempts; if still failing, stop and report the unresolved LVS blockers.

### Step 12: Final Report

Provide structured summary:
- Generated files (JSON, SKILL scripts, screenshots, reports) with paths
- Validation results (pass/fail)
- DRC/LVS results (if applicable)
- Ring statistics (total pads, analog/digital counts, voltage domains)
- Image analysis results (if layout analysis was performed)

## Global Rules & Constraints (HIGHEST PRIORITY)

These rules apply to every step of the process and cannot be overridden.

### User Intent & Signal Integrity
- **Immutable Order**: The user's signal list order is SACRED. Do NOT reorder, sort, or group signals.
- **Preserve Duplicates**: If the user lists a signal multiple times, you MUST generate multiple pads. Never deduplicate.
- **Simultaneous Placement**: Place signals and pads simultaneously to ensure the physical layout matches the logical list exactly.

### Critical Technical Constraints
- **Corner Insertion**: You MUST insert `PCORNER` instances at the exact transition points between sides (Top/Right/Bottom/Left) during placement. Do not append them at the end.
- **Domain Isolation**: Analog and Digital domains are strictly isolated. They never share pin configurations or connections.
- **Voltage Domains**: Priority 1 (Naming): If signal name matches conventions (e.g., `VIOH*`, `GIOH*`, `VPST`, `GPST`), use Voltage Domain devices (`PVDD2CDG`/`PVSS2CDG`). Priority 2 (Explicit): If user mentions "voltage domain". Otherwise, default to Regular Power/Ground (`PVDD1CDG`/`PVSS1CDG`).
- **Analog Ground**: Pure analog pads' VSS pins must connect to the analog common ground (default `GIOLA`) unless specific rules override.

### Forbidden Actions
- NO skipping steps in the workflow.
- NO relying on mental arithmetic for geometry (use Python code).
- NO creating files during the initial analysis phase (Step 0-1).
- NO calling `final_answer()` until all verification steps (DRC/LVS) are complete and successful.

### Strict Adherence & Inference Policy
- Strict Compliance: You MUST strictly follow the user's descriptions and the rules defined in this skill.
- Inference Restriction: Reasonable inference is ONLY allowed if the scenario is NOT covered by any existing rule or user instruction. Otherwise, self-inference is STRICTLY FORBIDDEN.

### Code Execution Efficiency (CRITICAL)
- Maximize Code Block Usage: Do NOT split a single logical task (like "JSON Generation") into multiple small code blocks. Write ONE comprehensive Python script.
- Silent Execution: Do NOT print intermediate variables to stdout. Only print the FINAL result or critical status updates.

## Task Completion Checklist

### Core Requirements
- [ ] All signals preserved (including duplicates), order strictly followed
- [ ] Step 2 draft JSON generated with only ring_config + name/position/type
- [ ] Step 3 enrichment completed (device/pin_connection/direction/domain/corners)

### Workflow
- [ ] Step 0: Timestamp directory created
- [ ] Step 2: Draft intent graph generated and saved
- [ ] Step 3: Final intent graph generated from draft and saved
- [ ] Step 4: Reference-guided gate check passed
- [ ] Step 5: Validation passed (exit 0)
- [ ] Step 6: Confirmed config built
- [ ] Step 7: SKILL scripts generated
- [ ] Step 8: Virtuoso connection verified before execution
- [ ] Step 9: Scripts executed, screenshots saved
- [ ] Step 10: DRC completed
- [ ] Step 11: LVS completed
- [ ] Step 12: Final report delivered

### Signal Integrity
- [ ] Is the signal order identical to user input?
- [ ] Are all duplicates preserved?
- [ ] Are `PCORNER` pads inserted at all 4 corners?

### Configuration Logic
- [ ] Are Analog/Digital domains isolated?
- [ ] Are Voltage Domain devices used ONLY when requested or name-matched?
- [ ] Do `pin_connection` labels match the Pin Configuration Matrix exactly?
- [ ] Do pure analog pads connect VSS to `GIOLA` (or equivalent)?

## Troubleshooting

| Problem | Solution |
|---------|---------|
| Scripts not found | Use absolute path; verify with `ls $SCRIPTS_PATH/validate_intent.py` |
| Virtuoso not connected | Start Virtuoso; do NOT retry SKILL execution |
| Domain isolation fails | Re-classify signals using ring-wrap continuity, ensure analog/digital domains are separated |
| Validation failure | Enter Step 5 repair loop: parse error -> query matching rule in references -> apply targeted JSON fix -> re-validate |
| DRC failure | Enter Step 10 repair loop: parse DRC report -> query matching reference rules -> fix intent JSON -> regenerate and rerun DRC |
| LVS failure | Enter Step 11 repair loop: parse LVS mismatch -> return to Step 3 to check/fix intent JSON -> rerun Step 3-11 |

Repair loop cap (applies to Step 10/11):

- Maximum 2 repair attempts per loop. If still failing after attempt 2, stop the loop and report unresolved blockers.

## Directory Structure

```
io-ring-orchestrator-T180/
├── SKILL.md                          # This file
├── structured_T180.md                # Source knowledge base
├── requirements.txt                  # Python requirements (minimal)
│
├── scripts/                          # CLI entry point scripts (each self-contained)
│   ├── validate_intent.py
│   ├── build_confirmed_config.py
│   ├── generate_schematic.py
│   ├── generate_layout.py
│   ├── check_virtuoso_connection.py
│   ├── run_il_with_screenshot.py
│   ├── run_drc.py
│   ├── run_lvs.py
│   └── README.md
│
├── references/                       # Documentation & templates
│   ├── draft_builder_T180.md
│   ├── enrichment_rules_T180.md
│   ├── T180_Technology.md
│   └── image_vision_instruction.md
│
└── assets/                          # All bundled code (self-contained)
    ├── core/                         # Core logic
    │   ├── layout/                   # Layout generation modules
    │   │   ├── config/lydevices_180.json
    │   │   ├── layout_generator_factory.py
    │   │   ├── process_node_config.py
    │   │   ├── device_classifier.py
    │   │   ├── position_calculator.py
    │   │   ├── layout_validator.py
    │   │   ├── filler_generator.py
    │   │   ├── voltage_domain.py
    │   │   ├── editor_confirm_merge.py
    │   │   └── editor_utils.py
    │   ├── schematic/
    │   │   └── devices/
    │   │       └── IO_decive_info_T180_parser.py
    │   └── intent_graph/
    │       └── json_validator.py
    │
    ├── device_info/                  # Device templates
    │   ├── IO_device_info_T180.json
    │   └── IO_decive_info_T180_parser.py
    │
    └── external_scripts/             # External executables
        └── calibre/
            └── T180/
```
