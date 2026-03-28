# Draft Builder - T180 (Phase 1)

## Purpose

Build a stable draft intent JSON from user-provided structural inputs only.
This phase MUST avoid device/pin/corner inference and produce a deterministic handoff file for Phase 2.

## Scope and Boundaries

### Allowed in Phase 1

- Parse user signal list and ring dimensions
- Compute `ring_config` (including pad dimensions, spacing, and counts)
- Assign `position` for outer pads
- Set `type` as `pad`
- Preserve signal order and duplicates

### Forbidden in Phase 1

- No `device` field
- No `pin_connection` field
- No `direction` field
- No `domain` field
- No `view_name` field
- No `pad_width`/`pad_height` per-instance overrides
- No corner insertion
- No voltage-domain classification

## Input Contract

Required inputs:

- signal list
- `top_count`, `bottom_count`, `left_count`, `right_count` (pad counts per side)
- `placement_order` (`clockwise` or `counterclockwise`)
- optional `chip_width`, `chip_height` (user-provided only; never auto-fill)

Optional inputs with defaults (use if user does not specify):

- `pad_width`: default `80`
- `pad_height`: default `120`
- `pad_spacing`: default `90`
- `corner_size`: default `130`

Input precedence for draft build:

1. Explicit user structural input
2. Default fallback values for `pad_width`/`pad_height`/`pad_spacing`/`corner_size`

## Ring Config

T180 uses dimensional ring config fields, unlike T28 which uses width/height counts.

```json
{
  "ring_config": {
    "process_node": "T180",
    "chip_width": null,
    "chip_height": null,
    "pad_spacing": 90,
    "pad_width": 80,
    "pad_height": 120,
    "corner_size": 130,
    "top_count": 4,
    "bottom_count": 4,
    "left_count": 4,
    "right_count": 4,
    "placement_order": "clockwise"
  }
}
```

### chip_width / chip_height Rules

- **NO self-assigned defaults**: The Agent is strictly forbidden from inventing or auto-filling default values for `chip_width`/`chip_height`.
- If the user does not provide explicit values, ask once; if still unspecified, keep both fields as `null`.
- `chip_width` and `chip_height` are in micrometers (μm).

### Default Values for Pad Parameters

If the user does not provide explicit values for `pad_width`, `pad_height`, `pad_spacing`, or `corner_size`, do not ask — just assign these defaults:

| Parameter | Default |
|-----------|---------|
| `pad_width` | 80 |
| `pad_height` | 120 |
| `pad_spacing` | 90 |
| `corner_size` | 130 |

### Pad Count Rules

- `top_count`, `bottom_count`, `left_count`, `right_count` refer to **Outer Ring Pads ONLY**.
- Do not include inner pads in these counts.
- The signal list must contain exactly `top_count + bottom_count + left_count + right_count` signals.

## Output Contract (Draft JSON)

```json
{
  "ring_config": {
    "process_node": "T180",
    "chip_width": null,
    "chip_height": null,
    "pad_spacing": 90,
    "pad_width": 80,
    "pad_height": 120,
    "corner_size": 130,
    "top_count": 4,
    "bottom_count": 4,
    "left_count": 4,
    "right_count": 4,
    "placement_order": "clockwise"
  },
  "instances": [
    {
      "name": "MCLK",
      "position": "left_0",
      "type": "pad"
    },
    {
      "name": "AVSC",
      "position": "left_1",
      "type": "pad"
    }
  ]
}
```

## Position Rules

### Outer Pad Position Format

- `{side}_{index}`
- examples: `left_0`, `top_1`, `right_2`, `bottom_3`

### Position Field Rules

- **Regular Pads**: Format is `side_index` (e.g., `left_0`, `top_1`, `right_2`, `bottom_3`).
- **Corners**: Must be one of `top_left`, `top_right`, `bottom_right`, `bottom_left`.
- **Indexing**: Must start from 0 and increment sequentially for each side (e.g., `left_0`, `left_1`, ...).

## Signal-to-Position Mapping

### Placement Order & Indexing Logic

The traversal order and direction of signal assignment is determined by `placement_order`:

**Clockwise**:

Signal list mapping:
- `[top_0..top_{top_count-1}]` — Top: `top_0` (Left) → `top_N` (Right)
- `[right_0..right_{right_count-1}]` — Right: `right_0` (Top) → `right_N` (Bottom)
- `[bottom_0..bottom_{bottom_count-1}]` — Bottom: `bottom_0` (Right) → `bottom_N` (Left)
- `[left_0..left_{left_count-1}]` — Left: `left_0` (Bottom) → `left_N` (Top)

Example (top_count=3, left_count=3, bottom_count=3, right_count=3):

- signal list: `MCLK AVSC VIOLA GIOLA VIOHA GIOHA FGCAL DITM CKTM DOTM DOFG CLKO`
- top (3): `MCLK, AVSC, VIOLA` → `top_0, top_1, top_2`
- right (3): `GIOLA, VIOHA, GIOHA` → `right_0, right_1, right_2`
- bottom (3): `FGCAL, DITM, CKTM` → `bottom_0, bottom_1, bottom_2`
- left (3): `DOTM, DOFG, CLKO` → `left_0, left_1, left_2`

**Counter-Clockwise**:

Signal list mapping:
- `[left_0..left_{left_count-1}]` — Left: `left_0` (Top) → `left_N` (Bottom)
- `[bottom_0..bottom_{bottom_count-1}]` — Bottom: `bottom_0` (Left) → `bottom_N` (Right)
- `[right_0..right_{right_count-1}]` — Right: `right_0` (Bottom) → `right_N` (Top)
- `[top_0..top_{top_count-1}]` — Top: `top_0` (Right) → `top_N` (Left)

Example (top_count=3, left_count=3, bottom_count=3, right_count=3):

- signal list: `MCLK AVSC VIOLA GIOLA VIOHA GIOHA FGCAL DITM CKTM DOTM DOFG CLKO`
- left (3): `MCLK, AVSC, VIOLA` → `left_0, left_1, left_2`
- bottom (3): `GIOLA, VIOHA, GIOHA` → `bottom_0, bottom_1, bottom_2`
- right (3): `FGCAL, DITM, CKTM` → `right_0, right_1, right_2`
- top (3): `DOTM, DOFG, CLKO` → `top_0, top_1, top_2`

### Corner Identification

Corner positions are fixed regardless of placement order:
- `top_left`: Between Left-Last and Top-First
- `top_right`: Between Top-Last and Right-First
- `bottom_right`: Between Right-Last and Bottom-First
- `bottom_left`: Between Bottom-Last and Left-First

## Duplicate Signal Rule

When duplicate signals (same signal name appearing multiple times) are encountered:
- DO NOT delete or remove duplicates
- Preserve all instances of duplicate signals exactly as provided
- Each duplicate occurrence is a valid, separate signal instance
- The draft must contain the exact same number of signal instances as the input signal list

## Position-Indexed Identity Rule

Use position index as the unique identity during this phase.
Do not use global name lookup for repeated names.

## Draft Validation Checklist

- `ring_config` contains all required fields (`process_node`, `chip_width`, `chip_height`, `pad_spacing`, `pad_width`, `pad_height`, `corner_size`, `top_count`, `bottom_count`, `left_count`, `right_count`, `placement_order`)
- `process_node` is `"T180"`
- `placement_order` is valid (`clockwise` or `counterclockwise`)
- `chip_width` and `chip_height` are numbers or `null` (never invented)
- every instance has `name`, `position`, `type`
- `type` is only `pad`
- no `corner` instances exist in draft
- no `device`/`pin_connection`/`direction`/`domain`/`view_name` fields exist
- total instance count equals `top_count + bottom_count + left_count + right_count`
- position uniqueness is maintained for physical placement
- signal order matches user input exactly (including duplicates)

## Preflight Checklist

- confirm `top_count`, `bottom_count`, `left_count`, `right_count` are positive integers
- confirm `placement_order` is `clockwise` or `counterclockwise`
- parse signal list and verify signal count equals `top_count + bottom_count + left_count + right_count`
  **CRITICAL: If the counts are not equal, check whether any signals were omitted (especially for the signals with duplicate names) and re-read the signal list in the user primary prompt. If the missing signals still cannot be identified, ask the user. Do not add fillers or any other signals subjectively.**
- confirm `chip_width`/`chip_height` are provided or set to `null`

## Handoff Invariants to Phase 2

Phase 2 MUST treat the following fields as immutable unless reporting hard input inconsistency:

- `ring_config.process_node`
- `ring_config.chip_width`
- `ring_config.chip_height`
- `ring_config.pad_spacing`
- `ring_config.pad_width`
- `ring_config.pad_height`
- `ring_config.corner_size`
- `ring_config.top_count`
- `ring_config.bottom_count`
- `ring_config.left_count`
- `ring_config.right_count`
- `ring_config.placement_order`
- `instances[].name`
- `instances[].position`
- `instances[].type`
