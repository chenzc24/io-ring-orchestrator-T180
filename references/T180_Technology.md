# T180 Technology - DRC Rules

Process-specific design rule check (DRC) parameters for 180nm technology node.

## DRC Rules

### Minimum Dimensions
- **Minimum spacing**: ≥ 0.28 µm
  - Applies to spacing between metal features, routing wires, and structures
- **Minimum width**: ≥ 0.28 µm
  - Applies to all metal line widths

## Metal Layers

- **Allowed layers**: METAL1, METAL2, METAL3, METAL4, METAL5
- **Naming convention**: Use "METAL" prefix (e.g., METAL1, METAL2, METAL5)

## Parameter Precision

- **Parameters**: Two decimal places (e.g., 0.28, 2.00)
- **Coordinates**: Five decimal places for geometric calculations (e.g., 1.23456)

## Usage

These DRC rules apply to all IO ring designs targeting the 180nm process node. Always validate designs against these minimum dimensions before finalizing layouts.