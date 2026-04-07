Role: Senior Analog IC Layout Engineer.

Task: Analyze the attached IO Ring image and generate a schematic configuration file.

**Step 1: Signal Extraction Rules (Strict Counter-Clockwise)**

You must extract signals in this specific physical order. Do not follow standard text reading direction for Right/Top sides.

1. **Left Side:** Read from **Top-Corner** down to **Bottom-Corner**.

2. **Bottom Side:** Read from **Left-Corner** across to **Right-Corner**.

3. **Right Side:** Read from **Bottom-Corner** up to **Top-Corner**. (CRITICAL: Read upwards!)

4. **Top Side:** Read from **Right-Corner** across to **Left-Corner**. (CRITICAL: Read right-to-left!)

**Step 2: Output Generation**

- Combine all signals from Step 1 into a single list under `Signal names`.

- Leave the "Additionally..." section empty or write "None". (T180 is always Single Ring)

- **neglect the devices named "PFILLER*"**.

**Output Template:**

Please strictly follow this format:

Task: Generate IO ring schematic and layout design for Cadence Virtuoso.

Design requirements:
[Insert pad count description]. [Single/Double] ring layout. Order: counterclockwise through left side, bottom side, right side, top side.

**Pad count description format:**
- If all sides have the same count: "[count] pads per side."
- If sides have different counts: "[count1] pads on left and right sides, [count2] pads on top and bottom sides."
  Example: "10 pads on left and right sides, 6 pads on top and bottom sides."

======================================================================
SIGNAL CONFIGURATION
======================================================================

Signal names: [Insert the list of Outer Ring signals here, separated by spaces]

