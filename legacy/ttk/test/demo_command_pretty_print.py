"""
Demo script for command pretty-printing functionality.

This script demonstrates the pretty_print_command function by creating
various commands and displaying their formatted output.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from the command_serializer module file
# We need to import the module file directly to avoid the __init__.py import issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "command_serializer",
    Path(__file__).parent.parent / "serialization" / "command_serializer.py"
)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

# Extract the classes and functions we need
DrawTextCommand = cs.DrawTextCommand
DrawHLineCommand = cs.DrawHLineCommand
DrawVLineCommand = cs.DrawVLineCommand
DrawRectCommand = cs.DrawRectCommand
ClearCommand = cs.ClearCommand
ClearRegionCommand = cs.ClearRegionCommand
RefreshCommand = cs.RefreshCommand
RefreshRegionCommand = cs.RefreshRegionCommand
InitColorPairCommand = cs.InitColorPairCommand
SetCursorVisibilityCommand = cs.SetCursorVisibilityCommand
MoveCursorCommand = cs.MoveCursorCommand
pretty_print_command = cs.pretty_print_command
serialize_command = cs.serialize_command


def demo_basic_commands():
    """Demonstrate pretty printing of basic commands."""
    print("\n" + "=" * 60)
    print("BASIC COMMANDS")
    print("=" * 60)
    
    # Draw text command
    print("\n1. Draw Text Command:")
    print("-" * 40)
    cmd = DrawTextCommand(
        row=5,
        col=10,
        text="Hello, World!",
        color_pair=1,
        attributes=3
    )
    print(pretty_print_command(cmd))
    
    # Draw rectangle command
    print("\n2. Draw Rectangle Command:")
    print("-" * 40)
    cmd = DrawRectCommand(
        row=0,
        col=0,
        height=10,
        width=20,
        color_pair=2,
        filled=True
    )
    print(pretty_print_command(cmd))
    
    # Clear command (no parameters)
    print("\n3. Clear Command:")
    print("-" * 40)
    cmd = ClearCommand()
    print(pretty_print_command(cmd))


def demo_line_commands():
    """Demonstrate pretty printing of line drawing commands."""
    print("\n" + "=" * 60)
    print("LINE DRAWING COMMANDS")
    print("=" * 60)
    
    # Horizontal line
    print("\n1. Horizontal Line:")
    print("-" * 40)
    cmd = DrawHLineCommand(
        row=3,
        col=5,
        char='-',
        length=15,
        color_pair=1
    )
    print(pretty_print_command(cmd))
    
    # Vertical line
    print("\n2. Vertical Line:")
    print("-" * 40)
    cmd = DrawVLineCommand(
        row=5,
        col=10,
        char='|',
        length=8,
        color_pair=1
    )
    print(pretty_print_command(cmd))


def demo_color_commands():
    """Demonstrate pretty printing of color-related commands."""
    print("\n" + "=" * 60)
    print("COLOR COMMANDS")
    print("=" * 60)
    
    print("\n1. Initialize Color Pair:")
    print("-" * 40)
    cmd = InitColorPairCommand(
        pair_id=5,
        fg_color=(255, 128, 0),
        bg_color=(0, 0, 0)
    )
    print(pretty_print_command(cmd))
    
    print("\n2. Another Color Pair (Blue on White):")
    print("-" * 40)
    cmd = InitColorPairCommand(
        pair_id=10,
        fg_color=(0, 0, 255),
        bg_color=(255, 255, 255)
    )
    print(pretty_print_command(cmd))


def demo_cursor_commands():
    """Demonstrate pretty printing of cursor-related commands."""
    print("\n" + "=" * 60)
    print("CURSOR COMMANDS")
    print("=" * 60)
    
    print("\n1. Set Cursor Visibility:")
    print("-" * 40)
    cmd = SetCursorVisibilityCommand(visible=True)
    print(pretty_print_command(cmd))
    
    print("\n2. Move Cursor:")
    print("-" * 40)
    cmd = MoveCursorCommand(row=10, col=20)
    print(pretty_print_command(cmd))


def demo_region_commands():
    """Demonstrate pretty printing of region-based commands."""
    print("\n" + "=" * 60)
    print("REGION COMMANDS")
    print("=" * 60)
    
    print("\n1. Clear Region:")
    print("-" * 40)
    cmd = ClearRegionCommand(
        row=5,
        col=10,
        height=8,
        width=15
    )
    print(pretty_print_command(cmd))
    
    print("\n2. Refresh Region:")
    print("-" * 40)
    cmd = RefreshRegionCommand(
        row=0,
        col=0,
        height=24,
        width=80
    )
    print(pretty_print_command(cmd))


def demo_indentation():
    """Demonstrate pretty printing with custom indentation."""
    print("\n" + "=" * 60)
    print("CUSTOM INDENTATION")
    print("=" * 60)
    
    cmd = DrawTextCommand(
        row=1,
        col=2,
        text="Indented command",
        color_pair=0,
        attributes=0
    )
    
    print("\n1. No indentation (default):")
    print("-" * 40)
    print(pretty_print_command(cmd, indent=0))
    
    print("\n2. Indented by 4 spaces:")
    print("-" * 40)
    print(pretty_print_command(cmd, indent=4))
    
    print("\n3. Indented by 8 spaces:")
    print("-" * 40)
    print(pretty_print_command(cmd, indent=8))


def demo_from_dictionary():
    """Demonstrate pretty printing from serialized dictionaries."""
    print("\n" + "=" * 60)
    print("PRETTY PRINTING FROM DICTIONARIES")
    print("=" * 60)
    
    print("\n1. From command dataclass:")
    print("-" * 40)
    cmd = DrawRectCommand(
        row=5,
        col=10,
        height=15,
        width=20,
        color_pair=3,
        filled=False
    )
    print(pretty_print_command(cmd))
    
    print("\n2. From serialized dictionary:")
    print("-" * 40)
    serialized = serialize_command(cmd)
    print(pretty_print_command(serialized))
    
    print("\n3. Both produce identical output:")
    print("-" * 40)
    result1 = pretty_print_command(cmd)
    result2 = pretty_print_command(serialized)
    if result1 == result2:
        print("✓ Outputs are identical")
    else:
        print("✗ Outputs differ")


def demo_command_sequence():
    """Demonstrate pretty printing a sequence of commands."""
    print("\n" + "=" * 60)
    print("COMMAND SEQUENCE")
    print("=" * 60)
    
    commands = [
        ClearCommand(),
        InitColorPairCommand(pair_id=1, fg_color=(255, 255, 255), bg_color=(0, 0, 0)),
        DrawTextCommand(row=0, col=0, text="Title", color_pair=1, attributes=1),
        DrawHLineCommand(row=1, col=0, char='-', length=40, color_pair=1),
        DrawTextCommand(row=2, col=0, text="Content line 1", color_pair=0, attributes=0),
        DrawTextCommand(row=3, col=0, text="Content line 2", color_pair=0, attributes=0),
        RefreshCommand(),
    ]
    
    print("\nRendering sequence:")
    print("-" * 40)
    for i, cmd in enumerate(commands, 1):
        print(f"\nCommand {i}:")
        print(pretty_print_command(cmd, indent=2))


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("TTK COMMAND PRETTY-PRINTING DEMONSTRATION")
    print("=" * 60)
    
    demo_basic_commands()
    demo_line_commands()
    demo_color_commands()
    demo_cursor_commands()
    demo_region_commands()
    demo_indentation()
    demo_from_dictionary()
    demo_command_sequence()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
