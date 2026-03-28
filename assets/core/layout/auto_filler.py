#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Filler Component Generation Module for T180
Supports blank type for domain mismatch cases
"""

from typing import List, Optional
from .device_classifier import DeviceClassifier
from .position_calculator import PositionCalculator
from .inner_pad_handler import InnerPadHandler
from .process_node_config import get_process_node_config

def get_corner_domain(oriented_pads, corner_orientation, placement_order: str = "clockwise") -> str:
    """Get corner domain based on the two pads around the corner.

    If the two adjacent pads share the same domain, return that domain;
    otherwise, default to "analog". If either pad is missing, also
    default to "analog".
    """
    pad1 = None
    pad2 = None
    is_clockwise = str(placement_order).lower() == "clockwise"

    if is_clockwise:
        # Start-corner mapping for clockwise indices:
        # top->TL, right->TR, bottom->BR, left->BL
        if corner_orientation == "R180":  # Top edge
            left_pads = oriented_pads.get("R270", [])
            top_pads = oriented_pads.get("R180", [])
            pad1 = left_pads[-1] if left_pads else None
            pad2 = top_pads[0] if top_pads else None
        elif corner_orientation == "R90":  # Right edge
            top_pads = oriented_pads.get("R180", [])
            right_pads = oriented_pads.get("R90", [])
            pad1 = top_pads[-1] if top_pads else None
            pad2 = right_pads[0] if right_pads else None
        elif corner_orientation == "R0":  # Bottom edge
            right_pads = oriented_pads.get("R90", [])
            bottom_pads = oriented_pads.get("R0", [])
            pad1 = right_pads[-1] if right_pads else None
            pad2 = bottom_pads[0] if bottom_pads else None
        elif corner_orientation == "R270":  # Left edge
            bottom_pads = oriented_pads.get("R0", [])
            left_pads = oriented_pads.get("R270", [])
            pad1 = bottom_pads[-1] if bottom_pads else None
            pad2 = left_pads[0] if left_pads else None
    else:
        # Start-corner mapping for counterclockwise indices:
        # top->TR, right->BR, bottom->BL, left->TL
        if corner_orientation == "R180":  # Top edge
            top_pads = oriented_pads.get("R180", [])
            right_pads = oriented_pads.get("R90", [])
            pad1 = top_pads[0] if top_pads else None
            pad2 = right_pads[-1] if right_pads else None
        elif corner_orientation == "R90":  # Right edge
            right_pads = oriented_pads.get("R90", [])
            bottom_pads = oriented_pads.get("R0", [])
            pad1 = right_pads[0] if right_pads else None
            pad2 = bottom_pads[-1] if bottom_pads else None
        elif corner_orientation == "R0":  # Bottom edge
            bottom_pads = oriented_pads.get("R0", [])
            left_pads = oriented_pads.get("R270", [])
            pad1 = bottom_pads[0] if bottom_pads else None
            pad2 = left_pads[-1] if left_pads else None
        elif corner_orientation == "R270":  # Left edge
            left_pads = oriented_pads.get("R270", [])
            top_pads = oriented_pads.get("R180", [])
            pad1 = left_pads[0] if left_pads else None
            pad2 = top_pads[-1] if top_pads else None

    if not pad1 or not pad2:
        return "analog"

    domain1 = pad1.get("domain")
    domain2 = pad2.get("domain")

    if domain1 and domain1 == domain2:
        return domain1
    else:
        if is_clockwise:
            return domain1
        else:
            return domain2


class AutoFillerGeneratorT180:
    """Auto Filler Component Generator for T180 process node"""
    
    def __init__(self, config: dict):
        self.config = config
        self.position_calculator = PositionCalculator(config)
        self.inner_pad_handler = InnerPadHandler(config)
        self.classifier = DeviceClassifier(process_node="T180")
        
        # Get corner filler device from config
        process_config = get_process_node_config("T180")
        device_masters = process_config.get("device_masters", {})
        self.corner_filler = device_masters.get("corner_filler", "PFILLER10")
        filler_components = process_config.get("filler_components", {})
        self.default_filler = filler_components.get("digital_10", "PFILLER10")

    def auto_insert_default_fillers(self, layout_components: List[dict], inner_pads: List[dict]) -> List[dict]:
        """Auto-insert fillers using relative positions only (no absolute coordinate calculation)."""
        _ = inner_pads
        # Check if filler components are already included
        existing_fillers = [comp for comp in layout_components if comp.get("type") == "filler" or DeviceClassifier.is_filler_device(comp.get("device", ""), "T180")]
        
        if existing_fillers:
            print(f"🔍 Detected filler components in intent graph: {len(existing_fillers)} fillers")
            print("📝 Skipping auto-filler generation, using components defined in intent graph")
            return layout_components
        
        pad_width_default = self.config.get("pad_width", 80)
        pad_height_default = self.config.get("pad_height", 120)
        placement_order = str(self.config.get("placement_order", "counterclockwise")).lower()

        def normalize_domain(value: str) -> str:
            if value in (None, "null", ""):
                return "analog"
            return value

        def get_component_width(component: dict) -> float:
            if component.get("type") == "corner":
                return float(self.config.get("corner_size", 130))
            if component.get("type") in {"filler", "blank"}:
                width = component.get("pad_width")
                if isinstance(width, (int, float)):
                    return float(width)
                return 10.0
            pad_width = component.get("pad_width")
            if isinstance(pad_width, (int, float)):
                return float(pad_width)
            return float(pad_width_default)

        def filler_record(name: str, device: str, record_type: str, position: str) -> dict:
            ref = global_ref_filler
            return {
                "name": name,
                "device": device,
                "type": record_type,
                "pad_width": ref.get("pad_width"),
                "pad_height": ref.get("pad_height", pad_height_default),
                "position": position,
            }

        def side_from_orientation(orientation: str) -> str:
            return {
                "R0": "bottom",
                "R90": "right",
                "R180": "top",
                "R270": "left",
            }.get(orientation, "")

        def orientation_from_side(side: str) -> str:
            return {
                "bottom": "R0",
                "right": "R90",
                "top": "R180",
                "left": "R270",
            }.get(side, "")

        def parse_relative_position(value):
            if not isinstance(value, str):
                return None, None
            if value in ("top_left", "top_right", "bottom_left", "bottom_right"):
                return "corner", None
            parts = value.split("_")
            if len(parts) == 2 and parts[0] in {"top", "right", "bottom", "left"} and parts[1].isdigit():
                return parts[0], int(parts[1])
            return None, None

        def target_span_for_side(side: str) -> Optional[float]:
            corner_size = float(self.config.get("corner_size", 130))
            chip_width = self.config.get("chip_width")
            chip_height = self.config.get("chip_height")

            if side in {"top", "bottom"} and isinstance(chip_width, (int, float)):
                return max(0.0, float(chip_width) - 2 * corner_size)
            if side in {"left", "right"} and isinstance(chip_height, (int, float)):
                return max(0.0, float(chip_height) - 2 * corner_size)
            return None

        pads = [comp for comp in layout_components if comp.get("type") == "pad"]

        global_ref_filler = {
            "pad_width": 10,
            "pad_height": pads[0].get("pad_height", pad_height_default) if pads else pad_height_default,
        }

        oriented_pads = {"R0": [], "R90": [], "R180": [], "R270": []}
        for pad in pads:
            rel_side, rel_index = parse_relative_position(pad.get("position"))
            if rel_side in {"top", "right", "bottom", "left"} and rel_index is not None:
                orientation = orientation_from_side(rel_side)
            else:
                orientation = pad.get("orientation", "")

            if orientation in oriented_pads:
                oriented_pads[orientation].append(pad)

        for orientation, pad_list in oriented_pads.items():
            if not pad_list:
                continue

            oriented_pads[orientation] = sorted(
                pad_list,
                key=lambda p: (
                    parse_relative_position(p.get("position"))[1]
                ),
            )

        fillers = []

        for orientation, pad_list in oriented_pads.items():
            if not pad_list:
                continue

            side = side_from_orientation(orientation)
            if not side:
                continue

            corner_domain = normalize_domain(get_corner_domain(oriented_pads, orientation, placement_order))
            first_pad = pad_list[0]
            first_domain = normalize_domain(first_pad.get("domain"))

            # Create side components list to manage order and re-indexing
            side_components = []


            # Helper for creating fillers/blanks
            def create_filler(name_suffix, device_type, rec_type="filler"):
                return filler_record(
                    name=f"{rec_type}_{side}_{name_suffix}",
                    device=device_type,
                    record_type=rec_type,
                    position="", # Will be set during re-indexing
                )

            # Start filler/blank (before first pad)
            if corner_domain == first_domain:
                start_filler = create_filler("start", self.corner_filler, "filler")
            else:
                start_filler = create_filler("start", "BLANK", "blank")
            
            fillers.append(start_filler)
            side_components.append(start_filler)

            # Process pads and intermediate fillers
            for idx in range(len(pad_list)):
                curr_pad = pad_list[idx]
                side_components.append(curr_pad)
                
                # Check for intermediate filler if not the last pad
                if idx < len(pad_list) - 1:
                    next_pad = pad_list[idx + 1]
                    curr_domain = normalize_domain(curr_pad.get("domain"))
                    next_domain = normalize_domain(next_pad.get("domain"))
                    
                    if curr_domain == next_domain:
                        mid_filler = create_filler(f"{idx}_mid", self.default_filler, "filler")
                    else:
                         mid_filler = create_filler(f"{idx}_mid", "BLANK", "blank")
                        
                    fillers.append(mid_filler)
                    side_components.append(mid_filler)

            # End filler (after last pad)
            # if corner_domain == end_domain:
            #     end_filler = create_filler("end", self.corner_filler, "filler")
            # else:
            #     end_filler = create_filler("end", "BLANK", "blank")
            end_filler = create_filler("end", self.corner_filler, "filler")
            fillers.append(end_filler)
            side_components.append(end_filler)

            # Fill to target side span using chip dimensions (works for relative-only inputs).
            target_span = target_span_for_side(side)
            if target_span is not None:
                current_span = sum(get_component_width(comp) for comp in side_components)
                filler_unit_width = float(global_ref_filler.get("pad_width", 10) or 10)
                tail_fill_index = 0
                while current_span + filler_unit_width <= target_span + 0.001:
                    tail_filler = filler_record(
                        name=f"auto_fill_{side}_tail_{tail_fill_index}",
                        device=self.default_filler,
                        record_type="filler",
                        position="",
                    )
                    insert_at = max(len(side_components) - 1, 0)
                    side_components.insert(insert_at, tail_filler)
                    fillers.append(tail_filler)
                    current_span += filler_unit_width
                    tail_fill_index += 1

            # Re-index all components in the side sequence
            for i, component in enumerate(side_components):
                # Update position to be sequential: side_0, side_1, side_2...
                new_pos = f"{side}_{i}"
                component["position"] = new_pos 

        return layout_components + fillers

