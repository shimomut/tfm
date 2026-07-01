#!/usr/bin/env python3
"""
Demo: Command Serialization

This demo shows how to use TTK's command serialization functionality to
record, serialize, and inspect rendering commands.
"""

import json
from ttk.serialization import (
    serialize_clear,
    serialize_draw_text,
    serialize_draw_rect,
    serialize_draw_hline,
    serialize_draw_vline,
    serialize_init_color_pair,
    serialize_refresh,
)


def demo_basic_serialization():
    """Demonstrate basic command serialization."""
    print("=" * 60)
    print("Demo: Basic Command Serialization")
    print("=" * 60)
    
    # Serialize a simple text drawing command
    cmd = serialize_draw_text(row=5, col=10, text="Hello, World!", color_pair=1, attributes=3)
    
    print("\nSerialized draw_text command:")
    print(json.dumps(cmd, indent=2))
    
    # Serialize a rectangle command
    cmd = serialize_draw_rect(row=0, col=0, height=10, width=40, color_pair=2, filled=True)
    
    print("\nSerialized draw_rect command:")
    print(json.dumps(cmd, indent=2))


def demo_command_sequence():
    """Demonstrate recording a sequence of commands."""
    print("\n" + "=" * 60)
    print("Demo: Recording Command Sequence")
    print("=" * 60)
    
    # Record a sequence of commands that would draw a simple UI
    commands = []
    
    # Initialize color pairs
    commands.append(serialize_init_color_pair(1, (255, 255, 255), (0, 0, 255)))  # White on blue
    commands.append(serialize_init_color_pair(2, (255, 255, 0), (0, 0, 0)))      # Yellow on black
    
    # Clear screen
    commands.append(serialize_clear())
    
    # Draw title bar
    commands.append(serialize_draw_rect(row=0, col=0, height=1, width=80, color_pair=1, filled=True))
    commands.append(serialize_draw_text(row=0, col=30, text="TTK Demo", color_pair=1))
    
    # Draw border
    commands.append(serialize_draw_hline(row=2, col=0, char="-", length=80, color_pair=2))
    commands.append(serialize_draw_vline(row=3, col=0, char="|", length=20, color_pair=2))
    commands.append(serialize_draw_vline(row=3, col=79, char="|", length=20, color_pair=2))
    commands.append(serialize_draw_hline(row=23, col=0, char="-", length=80, color_pair=2))
    
    # Draw content
    commands.append(serialize_draw_text(row=5, col=10, text="Welcome to TTK!", color_pair=2))
    commands.append(serialize_draw_text(row=7, col=10, text="This is a demo of command serialization.", color_pair=0))
    
    # Refresh display
    commands.append(serialize_refresh())
    
    print(f"\nRecorded {len(commands)} commands")
    print("\nCommand sequence (JSON format):")
    print(json.dumps(commands, indent=2))


def demo_command_analysis():
    """Demonstrate analyzing serialized commands."""
    print("\n" + "=" * 60)
    print("Demo: Command Analysis")
    print("=" * 60)
    
    # Create a sequence of commands
    commands = [
        serialize_clear(),
        serialize_draw_text(row=0, col=0, text="Line 1", color_pair=1),
        serialize_draw_text(row=1, col=0, text="Line 2", color_pair=1),
        serialize_draw_text(row=2, col=0, text="Line 3", color_pair=2),
        serialize_draw_rect(row=5, col=5, height=10, width=20, color_pair=3, filled=True),
        serialize_draw_hline(row=10, col=0, char="-", length=40, color_pair=1),
        serialize_refresh(),
    ]
    
    # Analyze the command sequence
    print(f"\nTotal commands: {len(commands)}")
    
    # Count command types
    command_types = {}
    for cmd in commands:
        cmd_type = cmd['command_type']
        command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
    
    print("\nCommand type distribution:")
    for cmd_type, count in sorted(command_types.items()):
        print(f"  {cmd_type}: {count}")
    
    # Find all text drawing commands
    text_commands = [cmd for cmd in commands if cmd['command_type'] == 'draw_text']
    print(f"\nText drawing commands: {len(text_commands)}")
    for i, cmd in enumerate(text_commands, 1):
        print(f"  {i}. Position ({cmd['row']}, {cmd['col']}): \"{cmd['text']}\"")
    
    # Find all color pairs used
    color_pairs = set()
    for cmd in commands:
        if 'color_pair' in cmd:
            color_pairs.add(cmd['color_pair'])
    
    print(f"\nColor pairs used: {sorted(color_pairs)}")


def demo_json_export():
    """Demonstrate exporting commands to JSON file."""
    print("\n" + "=" * 60)
    print("Demo: JSON Export")
    print("=" * 60)
    
    # Create a simple command sequence
    commands = [
        serialize_init_color_pair(1, (255, 0, 0), (0, 0, 0)),
        serialize_clear(),
        serialize_draw_text(row=10, col=20, text="Exported to JSON!", color_pair=1),
        serialize_refresh(),
    ]
    
    # Convert to JSON
    json_output = json.dumps(commands, indent=2)
    
    print("\nJSON output:")
    print(json_output)
    
    print("\nThis JSON can be:")
    print("  - Saved to a file for later replay")
    print("  - Transmitted over a network")
    print("  - Used for testing and validation")
    print("  - Analyzed for performance optimization")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("TTK Command Serialization Demo")
    print("=" * 60)
    
    demo_basic_serialization()
    demo_command_sequence()
    demo_command_analysis()
    demo_json_export()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

