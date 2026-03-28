#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Intent Graph Validator

This script provides basic validation for IO Ring intent graph JSON files.
It checks required fields, structure, and basic constraints without requiring
external dependencies.

Usage:
    python validate_intent.py <config_file_path>

Exit Codes:
    0 - Validation passed
    1 - Validation failed
    2 - File or JSON error
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple


def validate_ring_config(ring_config: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate ring_config section."""

    # Check process_node (defaults to T180)
    process_node = ring_config.get('process_node', 'T180')

    # Normalize common formats
    if process_node in ['180nm', '180', 'T180']:
        process_node = 'T180'

    if process_node not in ['T180']:
        return False, f"Invalid process_node '{process_node}'. Must be 'T180'"

    # Check dimensions
    has_width_height = 'width' in ring_config and 'height' in ring_config
    has_count_fields = all(key in ring_config for key in [
        'top_count', 'bottom_count', 'left_count', 'right_count'
    ])

    if not has_width_height and not has_count_fields:
        return False, "ring_config missing width/height or top_count/bottom_count/left_count/right_count"

    # Validate dimensions are positive
    if has_width_height:
        width = ring_config.get('width', 0)
        height = ring_config.get('height', 0)
        try:
            width = int(float(width))
            height = int(float(height))
        except (TypeError, ValueError):
            return False, "width and height must be numeric"

        if width <= 0 or height <= 0:
            return False, f"width ({width}) and height ({height}) must be positive"

    if has_count_fields:
        for side in ['top_count', 'bottom_count', 'left_count', 'right_count']:
            count = ring_config.get(side, 0)
            try:
                count = int(float(count))
            except (TypeError, ValueError):
                return False, f"{side} must be numeric"

            if count <= 0:
                return False, f"{side} ({count}) must be positive"

    # Check placement_order
    if 'placement_order' not in ring_config:
        return False, "Missing ring_config.placement_order field"

    placement_order = ring_config['placement_order']
    if placement_order not in ['clockwise', 'counterclockwise']:
        return False, f"placement_order must be 'clockwise' or 'counterclockwise', got '{placement_order}'"

    return True, "ring_config valid"


def validate_instances(instances: list) -> Tuple[bool, str]:
    """Validate instances section."""

    if not isinstance(instances, list):
        return False, "instances must be a list"

    if len(instances) == 0:
        return False, "instances list cannot be empty"

    # Validate each instance
    for i, instance in enumerate(instances):
        if not isinstance(instance, dict):
            return False, f"Instance {i} must be a dictionary"

        # Check required fields (accept both 'signal' and 'name' for backward compatibility)
        has_signal = 'signal' in instance
        has_name = 'name' in instance

        if not has_signal and not has_name:
            return False, f"Instance {i} missing required field 'signal' or 'name'"

        other_required_fields = ['device', 'position']
        for field in other_required_fields:
            if field not in instance:
                return False, f"Instance {i} missing required field '{field}'"

        # Validate signal/name is non-empty string
        signal = instance.get('signal') or instance.get('name')
        if not isinstance(signal, str) or not signal:
            return False, f"Instance {i}: signal/name must be a non-empty string"

        # Validate device is non-empty string
        if not isinstance(instance['device'], str) or not instance['device']:
            return False, f"Instance {i}: device must be a non-empty string"

        # Validate position format (should be like "top_0", "left_1", etc.)
        position = instance['position']
        if not isinstance(position, str):
            return False, f"Instance {i}: position must be a string"

        # Basic position format check
        valid_position_prefixes = ['top_', 'bottom_', 'left_', 'right_', 'corner_']
        if not any(position.startswith(prefix) for prefix in valid_position_prefixes):
            return False, f"Instance {i}: position '{position}' has invalid format (should start with top_, bottom_, left_, right_, or corner_)"

        # Validate pin_connection if present
        if 'pin_connection' in instance:
            pin_conn = instance['pin_connection']
            if not isinstance(pin_conn, dict):
                return False, f"Instance {i}: pin_connection must be a dictionary"

    return True, f"{len(instances)} instances valid"


def validate_intent_graph(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate complete intent graph configuration.

    Returns:
        (is_valid, message) tuple
    """

    if not config:
        return False, "Configuration is empty"

    # Validate ring_config
    if 'ring_config' not in config:
        return False, "Missing top-level 'ring_config' field"

    is_valid, msg = validate_ring_config(config['ring_config'])
    if not is_valid:
        return False, f"ring_config validation failed: {msg}"

    # Validate instances
    if 'instances' not in config:
        return False, "Missing top-level 'instances' field"

    is_valid, msg = validate_instances(config['instances'])
    if not is_valid:
        return False, f"instances validation failed: {msg}"

    # Count statistics
    total_instances = len(config['instances'])
    corner_instances = sum(1 for inst in config['instances'] if inst['position'].startswith('corner_'))
    pad_instances = total_instances - corner_instances

    return True, f"Validation passed: {pad_instances} pads, {corner_instances} corners"


def main():
    """Main entry point."""

    if len(sys.argv) < 2:
        print("Usage: python validate_intent.py <config_file_path>")
        print("\nValidates IO Ring intent graph JSON files.")
        print("\nExit codes:")
        print("  0 - Validation passed")
        print("  1 - Validation failed")
        print("  2 - File or JSON error")
        sys.exit(2)

    config_file_path = sys.argv[1]
    config_path = Path(config_file_path)

    # Check file exists
    if not config_path.exists():
        print(f"❌ Error: File not found: {config_file_path}")
        sys.exit(2)

    # Load JSON
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format")
        print(f"   {e}")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Error: Failed to load file")
        print(f"   {e}")
        sys.exit(2)

    # Validate
    is_valid, message = validate_intent_graph(config)

    if is_valid:
        print(f"✅ Intent graph validation passed!")
        print(f"   {message}")
        sys.exit(0)
    else:
        print(f"❌ Intent graph validation failed:")
        print(f"   {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
