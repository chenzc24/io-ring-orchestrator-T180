---
name: io-ring-orchestrator-T180
description: Master coordinator for complete T180 (180nm) IO Ring generation. Handles signal classification, device mapping, pin configuration, JSON generation, and complete workflow through DRC/LVS verification. Use this skill for any T180 IO Ring generation task. Trigger when user mentions T180, 180nm, 180nm IO ring, or any IO ring task targeting the 180nm process node.
---

# IO Ring Orchestrator - T180

Master coordinator for T180 IO Ring generation — entire workflow from requirements through DRC/LVS.

## Scripts Path Verification

Auto-detect `SCRIPTS_PATH` from this file's location. Do NOT hard-code:

```bash
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SCRIPTS_PATH="${SKILL_ROOT}/scripts"
ls "$SCRIPTS_PATH/validate_intent.py" || echo "ERROR: SCRIPTS_PATH not found"
```

## Entry Points

- **Text requirements only** → Step 0 → Step 2 (Draft) → [Step 2b if enabled] → Step 3 (Enrichment)
- **Image input (with or without text)** → Step 0 → Step 1 (Image) → Step 2 → [Step 2b if enabled] → Step 3
- **Draft intent graph file provided** → Skip to Step 3
- **Final intent graph file provided** → Skip to Step 5
- Determine entry path automatically. Do NOT run any pre-step wizard eligibility/opt-in flow.

## Draft Editor vs Confirmation Editor

| | Draft Editor (Step 2b) | Confirmation Editor (Step 6) |
|---|---|---|
| **Input** | Minimal: name, position, type (optional device) | Full enriched intent graph |
| **Pin connections** | Hidden / not generated | Visible and editable |
| **Fillers** | Not shown (added in Step 3) | Visible and editable |
| **Corners** | Placeholder "+ Corner" slots | All 4 must be filled |
| **Validation** | Ring closure check | Full layout validation |
| **Output** | Draft JSON → Step 3 | Confirmed JSON → Step 7 |
| **Confirm button** | "Confirm Draft" | "Confirm & Continue" |
| **Banner** | "Draft mode — fillers and pins added automatically later" | None |

## Output Path Contract (Mandatory)

- Single workspace output root per run; create `output_dir` once and reuse for Steps 2-12.
- Do NOT regenerate `timestamp` after Step 0. Export `AMS_OUTPUT_ROOT` once in Step 0.
- `AMS_OUTPUT_ROOT`: workspace-level output root
- `output_dir`: `${AMS_OUTPUT_ROOT}/generated/${timestamp}`
- DRC/LVS reports: `${AMS_OUTPUT_ROOT}/drc` and `${AMS_OUTPUT_ROOT}/lvs`

## Complete Workflow

### Step 0: Directory Setup & Parse Input

```bash
# Workspace root (prefer AMS_IO_AGENT_PATH, fallback to current dir)
if [ -n "${AMS_IO_AGENT_PATH:-}" ]; then WORK_ROOT="${AMS_IO_AGENT_PATH}"; else WORK_ROOT="$(pwd)"; fi

export AMS_OUTPUT_ROOT="${WORK_ROOT}/output"
mkdir -p "${AMS_OUTPUT_ROOT}/generated"

# Per-run dir: reuse if set, else create
if [ -n "${output_dir:-}" ] && [ -d "${output_dir}" ]; then
  echo "Reusing existing output_dir: ${output_dir}"
else
  timestamp="${timestamp:-$(date +%Y%m%d_%H%M%S)}"
  output_dir="${AMS_OUTPUT_ROOT}/generated/${timestamp}"
fi
mkdir -p "$output_dir"
echo "AMS_OUTPUT_ROOT=${AMS_OUTPUT_ROOT}"; echo "output_dir=${output_dir}"

# Resolve Python — project-root .venv preferred (shared with bridge), then skill .venv, then system.
PROJECT_ROOT="$(cd "${WORK_ROOT}" && while [ ! -d .venv ] && [ "$(pwd)" != "/" ]; do cd ..; done; pwd)"
if   [ -f "${PROJECT_ROOT}/.venv/Scripts/python.exe" ]; then export AMS_PYTHON="${PROJECT_ROOT}/.venv/Scripts/python.exe"
elif [ -f "${PROJECT_ROOT}/.venv/bin/python" ];         then export AMS_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
elif [ -f "${SKILL_ROOT}/.venv/Scripts/python.exe" ];   then export AMS_PYTHON="${SKILL_ROOT}/.venv/Scripts/python.exe"
elif [ -f "${SKILL_ROOT}/.venv/bin/python" ];           then export AMS_PYTHON="${SKILL_ROOT}/.venv/bin/python"
elif command -v python3 &>/dev/null;                    then export AMS_PYTHON="python3"
elif command -v python  &>/dev/null;                    then export AMS_PYTHON="python"
else echo "ERROR: No Python 3.9+ found. Create .venv at project root."; return 1; fi
echo "AMS_PYTHON=${AMS_PYTHON}"

	# Editor modes (default off)
	[ "${AMS_DRAFT_EDITOR:-}"  = "on" ] || export AMS_DRAFT_EDITOR="off"
	[ "${AMS_LAYOUT_EDITOR:-}" = "on" ] || export AMS_LAYOUT_EDITOR="off"
	echo "AMS_DRAFT_EDITOR=${AMS_DRAFT_EDITOR}  AMS_LAYOUT_EDITOR=${AMS_LAYOUT_EDITOR}"
```

**IMPORTANT:** All subsequent steps MUST use `$AMS_PYTHON` instead of `python3`.

Parse user input: signal list, ring dimensions (width x height), placement order, voltage domain specs.

**Draft Editor override:** If user explicitly requests the visual/draft editor ("I want to use the editor", etc.), set `AMS_DRAFT_EDITOR=on` for this run regardless of `.env`.

### Step 1: Image Input Processing (only if image provided)

1. Load instruction from `references/image_vision_instruction.md` first.
2. Extract structured requirements from image(s):
   - topology (Single/Double ring)
   - counter-clockwise outer-ring signal order
   - pad count description
3. Treat extracted structure as Step 2 input. If user text and image conflict, prefer explicit user text; keep unresolved conflicts in the report.
4. Conventions (unchanged): right side read bottom-to-top; top side read right-to-left; ignore `PFILLER*` devices.

### Step 2: Build Draft JSON (Structural Only)

Reference: `references/draft_builder_T180.md`

1. Parse structural inputs (signal list, width, height, placement_order). If `placement_order`/dimensions/counts cannot be uniquely resolved, ask the user directly, then continue.
2. Compute `ring_config`.
3. Generate `instances` for `pad` with ONLY: `name`, `position`, `type`.
4. Save to `{output_dir}/io_ring_intent_graph_draft.json`.

**Strict boundary:** Do NOT add `device`, `pin_connection`, `direction`, or any `corner` instance in Step 2.

### Step 2b: Draft Editor (Optional)

**Open when:** `AMS_DRAFT_EDITOR=on` OR user explicitly requested the editor.

```bash
$AMS_PYTHON $SKILL_ROOT/assets/layout_editor/layout_editor_launcher.py \
  {output_dir}/io_ring_intent_graph_draft.json \
  {output_dir}/io_ring_intent_graph_draft_confirmed.json \
  --mode draft
```

Draft Editor lets users drag pads between sides, add/remove pads and corners, set `device` (e.g. PVDD1CDG, PDDW0412SCDG), set `domain` (digital/analog), and see live ring validation (closure, corners).

After user confirms, merge editor output back into the draft JSON before Step 3. Editor overrides take precedence for: `name`, `position`, `type`, `device`, `domain`, `direction`.

**Skip when:** `AMS_DRAFT_EDITOR=off` AND user did not request the editor.

### Step 3: Enrich Draft JSON to Final Intent Graph

Reference: `references/enrichment_rules_T180.md`

**Mandatory inputs:**
- Step 2 draft JSON (primary structural source)
- Step 2b draft editor output (if opened — contains device hints and structural changes)
- Original user prompt (explicit intent: voltage-domain assignment, provider naming, direction overrides)

**Input precedence** (apply in order, never violate immutable draft structure):
1. Explicit user prompt constraints
2. Step 2b draft editor overrides (device, domain, direction)
3. Enrichment default inference

**Process:**
1. Read `ring_config` + draft instances + user prompt constraints.
2. Classify each signal's domain (analog/digital) using the Mandatory Signal Classification Dictionary.
3. Add per-instance `device` based on device selection tables.
4. Add per-instance `direction` for digital IO (`PDDW0412SCDG` only).
5. Add per-instance `pin_connection` according to the Pin Configuration Matrix.
6. Add per-instance `domain`, `view_name`.
7. Insert 4 corners (`PCORNER`) at correct transition positions.
8. Pre-save rule gates (per `enrichment_rules_T180.md`): Continuity, Provider-count, Position-identity, Pin-family, VSS-consistency.
9. Save to `{output_dir}/io_ring_intent_graph.json`.

**Handoff rule:** Treat draft structural fields (`ring_config`, `name`, `position`, `type`) as immutable unless a hard inconsistency must be reported.

### Step 4: Reference-Guided Gate Check (Mandatory)

Verify Step 3 output against `references/enrichment_rules_T180.md`:
- Priority, Domain Continuity, Position-Based Identity, Provider Count
- Analog Pins, Digital Pins, Universal VSS Rule, Direction Rules
- Corner Rules

Also verify: Step 3 output preserves explicit user-prompt constraints (voltage-domain ranges, provider names, direction overrides).

If any gate fails → repair JSON, repeat Step 4. Do not proceed to Step 5.

### Step 5: Validate JSON

```bash
$AMS_PYTHON $SCRIPTS_PATH/validate_intent.py {output_dir}/io_ring_intent_graph.json
```

- Exit 0 → proceed
- Exit 1 → repair loop: read error → query matching rule (`draft_builder_T180.md` / `enrichment_rules_T180.md`) → apply targeted fix → re-validate → repeat until Exit 0 or hard blocker (stop and report clearly).
- Exit 2 → file not found

**Repair constraints:** do NOT regenerate whole JSON unless fundamentally broken; preserve Step 2 immutable fields (`ring_config`, `name`, `position`, `type`); every fix must trace to a validator error + reference rule; if continuity/provider-count gates fail, fix classification first, then device/pin labels.

### Step 6: Build Confirmed Config (Confirmation Editor)

Check `AMS_LAYOUT_EDITOR`:
- `on` → Ask user via `AskUserQuestion`: *"The layout is ready for confirmation. Would you like to open the visual Layout Editor to review and adjust pad placement, fillers, and pin connections before proceeding?"*
  - **Open Layout Editor** — browser editor in confirmation mode (fillers, pins, corners); click "Confirm & Continue" when done.
  - **Skip Editor** — build confirmed config directly (recommended for batch runs).
- `off` → skip automatically, no question.

**Open editor:**
```bash
$AMS_PYTHON $SCRIPTS_PATH/build_confirmed_config.py \
  {output_dir}/io_ring_intent_graph.json \
  {output_dir}/io_ring_confirmed.json
```
This inserts fillers, generates intermediate JSON, opens browser editor, waits for confirm, merges changes back.

**Skip editor:**
```bash
$AMS_PYTHON $SCRIPTS_PATH/build_confirmed_config.py \
  {output_dir}/io_ring_intent_graph.json \
  {output_dir}/io_ring_confirmed.json \
  --skip-editor
```

Note: `build_confirmed_config.py` is hardcoded for T180 — no process node parameter needed.

### Step 7: Generate SKILL Scripts

```bash
$AMS_PYTHON $SCRIPTS_PATH/generate_schematic.py \
  {output_dir}/io_ring_confirmed.json \
  {output_dir}/io_ring_schematic.il

$AMS_PYTHON $SCRIPTS_PATH/generate_layout.py \
  {output_dir}/io_ring_confirmed.json \
  {output_dir}/io_ring_layout.il
```

Note: Both scripts are hardcoded for T180 — no process node parameter needed.

### Step 8: Check Virtuoso Connection

```bash
$AMS_PYTHON $SCRIPTS_PATH/check_virtuoso_connection.py
```

- Exit 0 → proceed
- Exit 1 → **STOP**. Report generated files so far; instruct user to start Virtuoso. Do NOT proceed.

### Step 9: Execute SKILL Scripts in Virtuoso

```bash
$AMS_PYTHON $SCRIPTS_PATH/run_il_with_screenshot.py \
  {output_dir}/io_ring_schematic.il \
  {lib} {cell} \
  {output_dir}/schematic_screenshot.png \
  schematic

$AMS_PYTHON $SCRIPTS_PATH/run_il_with_screenshot.py \
  {output_dir}/io_ring_layout.il \
  {lib} {cell} \
  {output_dir}/layout_screenshot.png \
  layout
```

### Step 10: Run DRC

```bash
$AMS_PYTHON $SCRIPTS_PATH/run_drc.py {lib} {cell} layout T180
```

- Exit 0 → Step 11
- Exit 1 → DRC repair loop: read report → map errors to reference rules (continuity/classification, device mapping, pin config, corner typing/order) → fix intent JSON → re-run Steps 6-10. Max 2 attempts; if still failing, stop and report blockers.

### Step 11: Run LVS

```bash
$AMS_PYTHON $SCRIPTS_PATH/run_lvs.py {lib} {cell} layout T180
```

- Exit 0 → Step 12
- Exit 1 → LVS repair loop: identify mismatch class (net/missing device/pin/shorts/opens) → query reference rules → fix intent JSON (check continuity/provider-count gates before pin-level edits) → re-run Steps 3-12. Max 2 attempts; if still failing, stop and report blockers.

### Step 12: Final Report

Structured summary:
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
- **Multi-Voltage Domain Support**: T180 supports multiple voltage domains within both analog and digital domains. Different VDDPST/VSSPST label pairs define different voltage domains. Each voltage domain block MUST have its own provider pair (PVDD2CDG + PVSS2CDG) and consumer pair (PVDD1CDG + PVSS1CDG). A domain can have multiple PVSS2CDG (same signal name) but only ONE PVDD2CDG.
- **Analog Ground**: Pure analog pads' VSS pins must connect to the analog common ground (default `GIOLA`) unless specific rules override.
- **Voltage Domain Continuity**: Signals in the same voltage domain should form contiguous blocks. Ring structure continuity applies (start and end of signal list are adjacent).

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

**Core Requirements**
- [ ] All signals preserved (including duplicates), order strictly followed
- [ ] Step 2 draft JSON: only `ring_config` + name/position/type
- [ ] Step 3 enrichment: device/pin_connection/direction/domain/corners

**Workflow**
- [ ] Step 0: Timestamp dir created; `AMS_PYTHON` resolved; `AMS_DRAFT_EDITOR`/`AMS_LAYOUT_EDITOR` resolved from .env
- [ ] Step 2: Draft intent graph generated/saved
- [ ] Step 2b: Draft Editor opened if `AMS_DRAFT_EDITOR=on` or user requested; skipped otherwise
- [ ] Step 2b: Draft editor output merged back into draft JSON before Step 3
- [ ] Step 3: Final intent graph generated from draft/saved
- [ ] Step 4: Gate check passed
- [ ] Step 5: Validation Exit 0
- [ ] Step 6: Confirmed config built (AMS_LAYOUT_EDITOR=on → ask user; off → skip)
- [ ] Step 7: SKILL scripts generated
- [ ] Step 8: Virtuoso connection verified
- [ ] Step 9: Scripts executed, screenshots saved
- [ ] Step 10: DRC completed
- [ ] Step 11: LVS completed
- [ ] Step 12: Final report delivered

**Signal Integrity**
- [ ] Is the signal order identical to user input?
- [ ] Are all duplicates preserved?
- [ ] Are `PCORNER` pads inserted at all 4 corners?

**Configuration Logic**
- [ ] Are Analog/Digital domains isolated?
- [ ] Are Voltage Domain devices used ONLY when requested or name-matched?
- [ ] Do `pin_connection` labels match the Pin Configuration Matrix exactly?
- [ ] Do pure analog pads connect VSS to `GIOLA` (or equivalent)?
- [ ] Are BLANK components inserted between different voltage domains (different VDDPST/VSSPST labels)?
- [ ] Does each voltage domain block have its own provider pair (PVDD2CDG + PVSS2CDG) and consumer pair (PVDD1CDG + PVSS1CDG)?
- [ ] Does each voltage domain block have exactly one PVDD2CDG (multiple PVSS2CDG with same name allowed)?
- [ ] Are voltage domain continuity rules satisfied (contiguous blocks, ring wrap)?

## Troubleshooting

| Problem | Solution |
|---------|---------|
| Scripts not found | Use auto-detection from SKILL_ROOT; verify with `ls $SCRIPTS_PATH/validate_intent.py` |
| Virtuoso not connected | Start Virtuoso; do NOT retry SKILL execution. Run `virtuoso-bridge status` |
| .il execution error | Fix `.il` file, re-run Step 9 |
| Domain continuity fails | Re-classify signals using ring-wrap continuity first, then re-check provider count |
| Validation failure | Enter Step 5 repair loop: parse error → query matching rule → apply targeted JSON fix → re-validate |
| DRC failure | Enter Step 10 repair loop: parse DRC report → query reference rules → fix intent JSON → regenerate and rerun DRC |
| LVS failure | Enter Step 11 repair loop: parse LVS mismatch → return to Step 3 to check/fix intent JSON → rerun Steps 3-12 |
| Voltage domain continuity fails | Check VDDPST/VSSPST labels — pads with different labels belong to different voltage domains; ensure BLANK is inserted between them and each domain block has its own provider pair |
| Missing BLANK between domains | Adjacent pads with different VDDPST/VSSPST labels need BLANK separator; check auto_filler logic |
| Draft Editor not opening | Check `AMS_DRAFT_EDITOR` in `.env` or verify user requested it; ensure port is not blocked |
| Draft Editor shows pin connections | Should not happen in draft mode — verify `window.__EDITOR_MODE__` is set to `draft` in server response |
| Confirmation Editor not opening | Check `AMS_LAYOUT_EDITOR` in `.env`; ensure `--skip-editor` flag is not passed |

**Repair loop cap (Steps 10/11):** Max 2 attempts. If still failing, stop and report unresolved blockers.

## Directory Structure

```
io-ring-orchestrator-T180/
├── SKILL.md                          # This file
├── .env                              # Skill configuration (edit per deployment)
├── requirements.txt                  # Python requirements (minimal)
│
├── scripts/                          # CLI entry points (each self-contained)
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
├── references/                       # Docs & templates
│   ├── draft_builder_T180.md
│   ├── enrichment_rules_T180.md
│   ├── T180_Technology.md
│   └── image_vision_instruction.md
│
└── assets/                           # Bundled code (self-contained)
    ├── core/
    │   ├── layout/                     # Layout generation modules
    │   │   ├── config/lydevices_180.json
    │   │   ├── layout_generator.py
    │   │   ├── layout_generator_factory.py
    │   │   ├── process_node_config.py
    │   │   ├── device_classifier.py
    │   │   ├── position_calculator.py
    │   │   ├── layout_validator.py
    │   │   ├── filler_generator.py
    │   │   ├── auto_filler.py
    │   │   ├── voltage_domain.py
    │   │   ├── editor_confirm_merge.py
    │   │   ├── editor_utils.py
    │   │   ├── layout_visualizer.py
    │   │   ├── confirmed_config_builder.py
    │   │   └── skill_generator.py
    │   ├── schematic/
    │   │   └── schematic_generator_T180.py
    │   └── intent_graph/
    │       └── json_validator.py
    │
    ├── layout_editor/                     # Browser-based layout editor
    │   ├── layout_editor_launcher.py      # Python HTTP server + launcher
    │   ├── layout_editor.html             # Draft mode editor (React SPA)
    │   ├── confirmation_editor.html       # Confirmation mode editor (React SPA)
    │   └── vendor/
    │       ├── react.min.js
    │       └── react-dom.min.js
    │
    ├── device_info/                    # Device templates
    │   ├── IO_device_info_T180.json
    │   └── IO_decive_info_T180_parser.py
    │
    ├── skill_code/                     # Virtuoso .il files
    │   ├── screenshot.il
    │   ├── get_cellview_info.il
    │   ├── helper_based_device_T28.il
    │   ├── create_io_ring_lib_full.il
    │   └── create_schematic_cv.il
    │
    ├── utils/                          # bridge_utils.py (Virtuoso bridge), visualization.py
    │   ├── bridge_utils.py
    │   └── visualization.py
    │
    └── external_scripts/               # External executables
        └── calibre/
            ├── env_common.csh
            ├── run_drc.csh
            ├── run_lvs.csh
            ├── run_pex.csh
            └── T180/
# Virtuoso TCP bridge + SSH transfer: virtuoso-bridge-lite (installed separately; see requirements.txt).
```
