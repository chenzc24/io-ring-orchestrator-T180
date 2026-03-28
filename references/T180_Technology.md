# T180 Technology - Physical Parameters

Process-specific parameters for 180nm (T180) technology node.

## Physical Dimensions

| Parameter | Value | Unit |
|-----------|-------|------|
| Pad Width | 80 | μm |
| Pad Height | 120 | μm |
| Pad Spacing | 90 | μm |
| Corner Size | 130 | μm |

## Process Node

- **Process**: 180nm
- **Process Node Identifier**: `T180`
- **Library**: `tpd018bcdnv5`

## Device Types

T180 uses the following IO device types (no `_H_G`/`_V_G` suffixes):

| Device Type | Category | Description |
|-------------|----------|-------------|
| `PVDD1ANA` | Analog IO | Analog IO signal pad (V-prefix) |
| `PVSS1ANA` | Analog IO | Analog IO signal pad (G-prefix) |
| `PVDD1CDG` | Power (Regular) | Regular power provider/consumer |
| `PVSS1CDG` | Ground (Regular) | Regular ground provider/consumer |
| `PVDD2CDG` | Power (Voltage Domain) | Voltage domain power provider/consumer |
| `PVSS2CDG` | Ground (Voltage Domain) | Voltage domain ground provider/consumer |
| `PDDW0412SCDG` | Digital IO | Digital IO signal pad |
| `PCORNER` | Corner | Corner pad (no pin connections) |

## Metal Layers

- **Allowed layers**: M1, M2, M3, M4, M5, M6, M7
- **Naming convention**: Use "M" prefix (e.g., M1, M2, M7)

## Parameter Precision

- **Parameters**: Integer values for dimensions (e.g., 80, 90, 120, 130)
- **Coordinates**: Use appropriate precision for geometric calculations

## Usage

These parameters apply to all IO ring designs targeting the 180nm process node. Always validate designs against these physical dimensions before finalizing layouts.
