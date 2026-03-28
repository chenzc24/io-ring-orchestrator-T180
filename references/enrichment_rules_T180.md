# Enrichment Rules - T180 (Phase 2)

## Purpose

Enrich the Phase 1 draft JSON with device types, pin connections, direction, domain, corners, and per-instance pad dimensions.

## Scope

This phase adds the following fields to each instance:
- `device`
- `pin_connection`
- `direction` (Digital IO only)
- `domain`
- `view_name`
- `pad_width` / `pad_height` (per-instance)

And inserts corner instances.

Mandatory inputs for Phase 2:
- Phase 1 draft JSON (primary source for structural fields)
- Original user prompt (source for explicit intent: voltage-domain assignment, provider naming, direction overrides)

Input precedence:
- Keep structural fields from Phase 1 draft immutable (`ring_config`, `name`, `position`, `type`) unless a hard inconsistency is reported.
- Apply constraints in this order when they do not conflict with immutable draft structure:
  1. Explicit user prompt constraints
  2. Default enrichment inference (rules below)

---

## Step 1: Signal Classification & Domain Assignment

### 1.1 Classification Priority (CRITICAL)

The priority for determining device type is:
1. **User Explicit Instruction** (e.g., "Signal X is Analog IO", "Domain is Analog"). **This overrides EVERYTHING.**
2. **Mandatory Dictionary** (Section 1.2 below).
3. **Naming Heuristics** (General Rule: if a device belongs to the analog domain, "V" in name implies `PVDD1ANA` and "G" in name implies `PVSS1ANA`).

### 1.2 Mandatory Signal Classification Dictionary

If the user does NOT explicitly specify the type, check this dictionary. If a signal name appears here, it MUST be classified as the specified type.

**Analog IO (Force Type: `PVDD1ANA` or `PVSS1ANA`):**

`MCLK`, `CDCKB`, `VDCKB`, `VDCK`, `GDCK`, `VDBS`, `GDBS`, `VNID`, `VPID`, `IPNI`, `IPPI`, `VINP`, `AVSC`, `AGSC`, `IINP`, `IINN`, `DVSC`, `DGSC`, `VCMSC`, `VNSC`, `VPSC`, `VPID`, `VNID`, `INPI`, `INNI`, `VDO`, `GDO`, `AVSF`, `AGSF`, `DGSF`, `DVSF`

**Digital IO (Force Type: `PDDW0412SCDG`):**

`FGCAL`, `DITM`, `CKTM`, `RSTM`, `DOTM`, `CKAZ`, `DOFG`, `CLKO`, `CONV`, `DA*` (e.g., DA0-DA14)

### 1.3 Domain Assignment Rules

- Signals in the Analog IO list → `domain: "analog"`
- Signals in the Digital IO list → `domain: "digital"`
- Signals with names matching power/ground patterns (e.g., `V*`, `G*`, `VIOLA`, `GIOLA`, `VIOLD`, `GIOLD`) → determine domain from context:
  - If surrounded by analog signals → `domain: "analog"`
  - If surrounded by digital signals → `domain: "digital"`
  - If user explicitly specifies domain → use user specification

**Domain Isolation**: Analog and Digital domains are strictly isolated. They never share pin configurations or connections.

---

## Step 2: Device Selection

### 2.1 Voltage Domain Logic

**Priority for determining Voltage Domain (VD) vs Regular devices:**

1. **Priority 1 (Naming)**: If signal name matches conventions (e.g., `VIOH*`, `GIOH*`, `VPST`, `GPST`), use Voltage Domain devices (`PVDD2CDG`/`PVSS2CDG`).
2. **Priority 2 (Explicit)**: If user mentions "voltage domain" for a signal.
3. **Default**: Use Regular Power/Ground devices (`PVDD1CDG`/`PVSS1CDG`).

### 2.2 Analog Domain Devices

| Signal Category | Condition | Device | Naming Convention Examples |
|:---|:---|:---|:---|
| **Analog IO** | Priority 1: User explicitly says "Analog IO". Priority 2: Name in Mandatory Dictionary. | `PVDD1ANA` (if "V" in name) / `PVSS1ANA` (if "G" in name) | MCLK, CDCKB, VDCKB, VDCK, AVSC, AGSC, etc. |
| **Analog VD Power** | Priority 1: User says "Voltage Domain". Priority 2: Name matches `VIOHA`/`VDID`. | `PVDD2CDG` | VIOHA, VDID etc. |
| **Analog VD Ground** | Priority 1: User says "Voltage Domain". Priority 2: Name matches `GIOHA`/`GDID`. | `PVSS2CDG` | GIOHA, GDID etc. |
| **Analog Power** | Analog Domain Consumer (Regular) | `PVDD1CDG` | VIOLA, VDIB etc. |
| **Analog Ground** | Analog Domain Consumer (Regular) | `PVSS1CDG` | GIOLA, GDIB etc. |

### 2.3 Digital Domain Devices

| Signal Category | Condition | Device | Naming Convention Examples |
|:---|:---|:---|:---|
| **Digital IO** | Priority 1: User explicitly says "Digital IO". Priority 2: Name in Mandatory Dictionary. | `PDDW0412SCDG` | FGCAL, DITM, CKTM, RSTM, DOTM, DA0-DA14 etc. |
| **Digital VD Power** | Priority 1: User says "Voltage Domain". Priority 2: Name matches `VIOHD`/`VPST`. | `PVDD2CDG` | VIOHD, VPST etc. |
| **Digital VD Ground** | Priority 1: User says "Voltage Domain". Priority 2: Name matches `GIOHD`/`GPST`. | `PVSS2CDG` | GIOHD, GPST etc. |
| **Digital Power** | Digital Domain Consumer (Regular) | `PVDD1CDG` | VIOLD, VDIO etc. |
| **Digital Ground** | Digital Domain Consumer (Regular) | `PVSS1CDG` | GIOLD, GDIO etc. |

### 2.4 Corner Devices

| Signal Category | Condition | Device |
|:---|:---|:---|
| **Corner** | Corner Pad | `PCORNER` |

---

## Step 3: Pin Configuration

**CRITICAL**: Configure `pin_connection` exactly according to these matrices. **Strictly isolate domains.**

### 3.1 Analog Domain Pin Configuration

**Scope**: Devices with `domain: "analog"`.

**Label Sources (Analog Only)**:
- **ANA_REG_PWR**: Name of Analog Regular Power instance (e.g., `VIOLA`, `VDIB`).
- **ANA_REG_GND**: Name of Analog Regular Ground instance (e.g., `GIOLA`, `GDIB`).
- **ANA_VD_PWR**: Name of Analog Voltage Domain Power instance (e.g., `VIOHA`, `VDID`).
- **ANA_VD_GND**: Name of Analog Voltage Domain Ground instance (e.g., `GIOHA`, `GDID`).

| Device | VDD Pin Label | VSS Pin Label | VDDPST Pin Label | VSSPST Pin Label | Special Pins |
|:---|:---|:---|:---|:---|:---|
| **PVDD1ANA** | ANA_REG_PWR | ANA_REG_GND | ANA_VD_PWR | ANA_VD_GND | AVDD = **Self Name** |
| **PVSS1ANA** | ANA_REG_PWR | ANA_REG_GND | ANA_VD_PWR | ANA_VD_GND | AVSS = **Self Name** |
| **PVDD1CDG** | **Self Name** | ANA_REG_GND | ANA_VD_PWR | ANA_VD_GND | - |
| **PVSS1CDG** | ANA_REG_PWR | **Self Name** | ANA_VD_PWR | ANA_VD_GND | - |
| **PVDD2CDG** | ANA_REG_PWR | ANA_REG_GND | **Self Name** | ANA_VD_GND | - |
| **PVSS2CDG** | ANA_REG_PWR | ANA_REG_GND | ANA_VD_PWR | **Self Name** | - |

**Analog Ground Rule**: Pure analog pads' VSS pins must connect to the analog common ground (default `GIOLA`) unless specific rules override.

### 3.2 Digital Domain Pin Configuration

**Scope**: Devices with `domain: "digital"`.

**Label Sources (Digital Only)**:
- **DIG_REG_PWR**: Name of Digital Regular Power instance (e.g., `VIOLD`, `VDIO`).
- **DIG_REG_GND**: Name of Digital Regular Ground instance (e.g., `GIOLD`, `GDIO`).
- **DIG_VD_PWR**: Name of Digital Voltage Domain Power instance (e.g., `VIOHD`, `VPST`).
- **DIG_VD_GND**: Name of Digital Voltage Domain Ground instance (e.g., `GIOHD`, `GPST`).

| Device | VDD Pin Label | VSS Pin Label | VDDPST Pin Label | VSSPST Pin Label | Special Pins |
|:---|:---|:---|:---|:---|:---|
| **PDDW0412SCDG** | DIG_REG_PWR | DIG_REG_GND | DIG_VD_PWR | DIG_VD_GND | - |
| **PVDD1CDG** | **Self Name** | DIG_REG_GND | DIG_VD_PWR | DIG_VD_GND | - |
| **PVSS1CDG** | DIG_REG_PWR | **Self Name** | DIG_VD_PWR | DIG_VD_GND | - |
| **PVDD2CDG** | DIG_REG_PWR | DIG_REG_GND | **Self Name** | DIG_VD_GND | - |
| **PVSS2CDG** | DIG_REG_PWR | DIG_REG_GND | DIG_VD_PWR | **Self Name** | - |

### 3.3 Corner Pin Configuration

| Device | Configuration |
|:---|:---|
| **PCORNER** | No `pin_connection` required. |

### 3.4 Label Source Resolution

**ANA_REG_PWR / ANA_REG_GND / ANA_VD_PWR / ANA_VD_GND**:
- Identify from signal names in the user's signal list within the analog domain section.
- Look for power signals (names starting with V) and ground signals (names starting with G).
- Regular power/ground: Names like `VIOLA`, `GIOLA`, `VDIB`, `GDIB` → use as `ANA_REG_PWR`/`ANA_REG_GND`.
- Voltage domain power/ground: Names like `VIOHA`, `GIOHA`, `VDID`, `GDID` → use as `ANA_VD_PWR`/`ANA_VD_GND`.

**DIG_REG_PWR / DIG_REG_GND / DIG_VD_PWR / DIG_VD_GND**:
- Same logic but within the digital domain section.
- Regular: `VIOLD`, `GIOLD`, `VDIO`, `GDIO`.
- Voltage domain: `VIOHD`, `GIOHD`, `VPST`, `GPST`.

---

## Step 4: Direction Determination (Digital IO Only)

### 4.1 Direction Rules

**Pre-Rule**: `direction` only has two valid values: `input` and `output`.

**Priority for determining `direction`:**

1. **User Explicit Instruction** (e.g., "`CKAZ` is Input", "`DA0-DA7` are Output"). **This overrides everything.**
2. **Signal-Direction Dictionary / Bus Annotation** (if provided by the user in text/image extraction result).
3. **Example** (only if no user instruction or dictionary info):
   - Input: `CKAZ`, `CONV`, `FGCAL`, `DITM`, `CKTM`, `RSTM`
   - Output: `DOTM`, `DOFG`, `CLKO`, `DA0-DA14`
4. **No Fallback**: If still unknown, keep `direction` unspecified and require explicit user confirmation.

### 4.2 Scope Constraints

- `direction` is required for Digital IO signal pads (e.g., `PDDW0412SCDG`).
- `direction` must NOT be added to analog-only pads, power/ground pads, or corner pads.

### 4.3 Conflict Handling

- If a user explicit instruction conflicts with any heuristic/example, follow the user explicit instruction.
- The template value `"direction": "input"` is an example only; do NOT treat it as a global fixed value.

---

## Step 5: Corner Insertion

### 5.1 Corner Rules

- Only one corner type in T180: `PCORNER`.
- Insert `PCORNER` instances at the exact transition points between sides during placement.
- Do not append corners at the end of the instances list.

### 5.2 Corner Identification

Corner positions are fixed regardless of placement order:
- `top_left`: Between Left-Last and Top-First.
- `top_right`: Between Top-Last and Right-First.
- `bottom_right`: Between Right-Last and Bottom-First.
- `bottom_left`: Between Bottom-Last and Left-First.

### 5.3 Corner Instance Template

```json
{
  "name": "CORNER_TL",
  "device": "PCORNER",
  "view_name": "layout",
  "domain": "null",
  "pad_width": 130,
  "pad_height": 130,
  "position": "top_left",
  "type": "corner"
}
```

Corner instance pad dimensions always use `corner_size` value from `ring_config`.

---

## Step 6: Per-Instance Fields

Each enriched instance must include these additional fields:

| Field | Value |
|-------|-------|
| `view_name` | `"layout"` |
| `domain` | `"analog"` or `"digital"` or `"null"` (for corners) |
| `pad_width` | From `ring_config.pad_width` (or `ring_config.corner_size` for corners) |
| `pad_height` | From `ring_config.pad_height` (or `ring_config.corner_size` for corners) |

---

## Pre-Save Rule Gates

Before saving the final JSON, verify these gates pass:

### Continuity Gate
- Signals assigned to the same domain must form contiguous blocks.
- Ring structure continuity applies (start and end of list are adjacent).

### Position-Identity Gate
- Every instance has a unique position.
- Position format matches the expected pattern (`side_index` or corner positions).

### Pin-Family Gate
- Analog devices use analog pin labels only (ANA_REG_PWR, ANA_REG_GND, ANA_VD_PWR, ANA_VD_GND).
- Digital devices use digital pin labels only (DIG_REG_PWR, DIG_REG_GND, DIG_VD_PWR, DIG_VD_GND).
- Domains never share pin label sources.

### VSS-Consistency Gate
- All analog pads within the same domain must connect VSS to the same analog ground signal (default `GIOLA`).

### Provider-Count Gate
- Each domain must have at least one power provider and one ground provider.
- Voltage domain providers (`PVDD2CDG`/`PVSS2CDG`) must be identified correctly based on naming or explicit user specification.

---

## Final JSON Templates

### Analog Instance (No `direction`)

```json
{
  "name": "ANA_SIG_NAME",
  "device": "PVDD1ANA",
  "view_name": "layout",
  "domain": "analog",
  "pad_width": 80,
  "pad_height": 120,
  "position": "top_0",
  "type": "pad",
  "pin_connection": {
    "VDD": {"label": "VIOLA"},
    "VSS": {"label": "GIOLA"},
    "VDDPST": {"label": "VIOHA"},
    "VSSPST": {"label": "GIOHA"},
    "AVDD": {"label": "ANA_SIG_NAME"}
  }
}
```

### Digital Instance (Requires `direction`)

```json
{
  "name": "DIG_SIG_NAME",
  "device": "PDDW0412SCDG",
  "view_name": "layout",
  "domain": "digital",
  "pad_width": 80,
  "pad_height": 120,
  "position": "top_1",
  "type": "pad",
  "direction": "input",
  "pin_connection": {
    "VDD": {"label": "VIOLD"},
    "VSS": {"label": "GIOLD"},
    "VDDPST": {"label": "VIOHD"},
    "VSSPST": {"label": "GIOHD"}
  }
}
```

### Corner Instance

```json
{
  "name": "CORNER_TL",
  "device": "PCORNER",
  "view_name": "layout",
  "domain": "null",
  "pad_width": 130,
  "pad_height": 130,
  "position": "top_left",
  "type": "corner"
}
```
