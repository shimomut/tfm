"""
Demo application for TTK command parsing functionality.

This demo shows how to:
1. Parse commands from dictionaries
2. Validate command structure
3. Handle parsing errors
4. Perform round-trip serialization (serialize -> parse -> serialize)
"""

import json
from ttk.serialization import (
    parse_command,
    serialize_command,
    DrawTextCommand,
    DrawRectCommand,
    InitColorPairCommand,
)


def demo_basic_parsing():
    """Demonstrate basic command parsing."""
    print("=" * 70)
    print("DEMO 1: Basic Command Parsing")
    print("=" * 70)
    
    # Parse a draw_text command
    data = {
        'command_type': 'draw_text',
        'row': 5,
        'col': 10,
        'text': 'Hello, World!',
        'color_pair': 1,
        'attributes': 3
    }
    
    print("\nInput dictionary:")
    print(json.dumps(data, indent=2))
    
    cmd = parse_command(data)
    
    print("\nParsed command:")
    print(f"  Type: {type(cmd).__name__}")
    print(f"  Row: {cmd.row}")
    print(f"  Col: {cmd.col}")
    print(f"  Text: {cmd.text}")
    print(f"  Color pair: {cmd.color_pair}")
    print(f"  Attributes: {cmd.attributes}")


def demo_parsing_all_types():
    """Demonstrate parsing all command types."""
    print("\n" + "=" * 70)
    print("DEMO 2: Parsing All Command Types")
    print("=" * 70)
    
    commands = [
        {'command_type': 'draw_text', 'row': 1, 'col': 2, 'text': 'test'},
        {'command_type': 'draw_hline', 'row': 3, 'col': 4, 'char': '-', 'length': 10},
        {'command_type': 'draw_vline', 'row': 5, 'col': 6, 'char': '|', 'length': 10},
        {'command_type': 'draw_rect', 'row': 7, 'col': 8, 'height': 5, 'width': 10},
        {'command_type': 'clear'},
        {'command_type': 'clear_region', 'row': 9, 'col': 10, 'height': 3, 'width': 5},
        {'command_type': 'refresh'},
        {'command_type': 'refresh_region', 'row': 11, 'col': 12, 'height': 3, 'width': 5},
        {'command_type': 'init_color_pair', 'pair_id': 1, 'fg_color': [255, 0, 0], 'bg_color': [0, 0, 0]},
        {'command_type': 'set_cursor_visibility', 'visible': True},
        {'command_type': 'move_cursor', 'row': 13, 'col': 14},
    ]
    
    for data in commands:
        cmd = parse_command(data)
        print(f"\n  {data['command_type']:25} -> {type(cmd).__name__}")


def demo_error_handling():
    """Demonstrate error handling during parsing."""
    print("\n" + "=" * 70)
    print("DEMO 3: Error Handling")
    print("=" * 70)
    
    # Test 1: Missing command_type
    print("\nTest 1: Missing command_type field")
    try:
        parse_command({'row': 5, 'col': 10})
    except ValueError as e:
        print(f"  ✓ Caught ValueError: {e}")
    
    # Test 2: Unknown command type
    print("\nTest 2: Unknown command type")
    try:
        parse_command({'command_type': 'unknown_command'})
    except ValueError as e:
        print(f"  ✓ Caught ValueError: {e}")
    
    # Test 3: Missing required field
    print("\nTest 3: Missing required field")
    try:
        parse_command({
            'command_type': 'draw_text',
            'row': 5,
            # Missing 'col' and 'text'
        })
    except ValueError as e:
        print(f"  ✓ Caught ValueError: {e}")
    
    # Test 4: Wrong field type
    print("\nTest 4: Wrong field type")
    try:
        parse_command({
            'command_type': 'draw_text',
            'row': '5',  # Should be int
            'col': 10,
            'text': 'Hello'
        })
    except TypeError as e:
        print(f"  ✓ Caught TypeError: {e}")
    
    # Test 5: Invalid color tuple
    print("\nTest 5: Invalid color tuple")
    try:
        parse_command({
            'command_type': 'init_color_pair',
            'pair_id': 1,
            'fg_color': (255, 0),  # Only 2 elements
            'bg_color': (0, 0, 0)
        })
    except ValueError as e:
        print(f"  ✓ Caught ValueError: {e}")


def demo_round_trip():
    """Demonstrate round-trip serialization."""
    print("\n" + "=" * 70)
    print("DEMO 4: Round-Trip Serialization")
    print("=" * 70)
    
    # Create original command
    original = DrawTextCommand(
        row=5,
        col=10,
        text='Hello, World!',
        color_pair=3,
        attributes=7
    )
    
    print("\nOriginal command:")
    print(f"  {original}")
    
    # Serialize
    serialized = serialize_command(original)
    print("\nSerialized to dictionary:")
    print(f"  {json.dumps(serialized, indent=2)}")
    
    # Parse back
    parsed = parse_command(serialized)
    print("\nParsed back to command:")
    print(f"  {parsed}")
    
    # Verify equality
    print("\nVerification:")
    print(f"  Original == Parsed: {original == parsed}")
    
    # Serialize again
    reserialized = serialize_command(parsed)
    print(f"  Serialized == Reserialized: {serialized == reserialized}")


def demo_json_compatibility():
    """Demonstrate JSON compatibility."""
    print("\n" + "=" * 70)
    print("DEMO 5: JSON Compatibility")
    print("=" * 70)
    
    # Create a command
    cmd = DrawRectCommand(
        row=10,
        col=20,
        height=5,
        width=15,
        color_pair=2,
        filled=True
    )
    
    print("\nOriginal command:")
    print(f"  {cmd}")
    
    # Serialize to dictionary
    data = serialize_command(cmd)
    
    # Convert to JSON string
    json_str = json.dumps(data, indent=2)
    print("\nJSON representation:")
    print(json_str)
    
    # Parse from JSON string
    parsed_data = json.loads(json_str)
    parsed_cmd = parse_command(parsed_data)
    
    print("\nParsed from JSON:")
    print(f"  {parsed_cmd}")
    
    print("\nVerification:")
    print(f"  Original == Parsed: {cmd == parsed_cmd}")


def demo_color_tuple_handling():
    """Demonstrate color tuple handling (list vs tuple)."""
    print("\n" + "=" * 70)
    print("DEMO 6: Color Tuple Handling")
    print("=" * 70)
    
    # Test with tuple
    print("\nTest 1: Using tuples")
    data_tuple = {
        'command_type': 'init_color_pair',
        'pair_id': 1,
        'fg_color': (255, 128, 64),
        'bg_color': (0, 0, 0)
    }
    cmd_tuple = parse_command(data_tuple)
    print(f"  Input: fg_color={data_tuple['fg_color']} (type: {type(data_tuple['fg_color']).__name__})")
    print(f"  Output: fg_color={cmd_tuple.fg_color} (type: {type(cmd_tuple.fg_color).__name__})")
    
    # Test with list (JSON arrays become lists)
    print("\nTest 2: Using lists (from JSON)")
    data_list = {
        'command_type': 'init_color_pair',
        'pair_id': 1,
        'fg_color': [255, 128, 64],
        'bg_color': [0, 0, 0]
    }
    cmd_list = parse_command(data_list)
    print(f"  Input: fg_color={data_list['fg_color']} (type: {type(data_list['fg_color']).__name__})")
    print(f"  Output: fg_color={cmd_list.fg_color} (type: {type(cmd_list.fg_color).__name__})")
    
    print("\nNote: Lists are automatically converted to tuples for consistency")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("TTK Command Parsing Demo")
    print("=" * 70)
    print("\nThis demo shows how to parse rendering commands from dictionaries")
    print("and validate their structure.")
    
    demo_basic_parsing()
    demo_parsing_all_types()
    demo_error_handling()
    demo_round_trip()
    demo_json_compatibility()
    demo_color_tuple_handling()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
