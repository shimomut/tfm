#!/usr/bin/env python3
"""
Demonstration of the GeneralPurposeDialog width calculation fix

This script shows the difference between the old buggy calculation
and the new fixed calculation for input field width.
"""

def demonstrate_width_calculation():
    """Demonstrate the width calculation fix"""
    
    print("GeneralPurposeDialog Width Calculation Fix")
    print("=" * 50)
    print()
    print("The Bug:")
    print("--------")
    print("The original code calculated max_input_width as space for input text only,")
    print("but passed it to SingleLineTextEdit.draw() as max_width, which expects")
    print("the total width including the prompt text. This caused unnecessary truncation.")
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Rename dialog with help text",
            "width": 80,
            "prompt": "Rename 'oldfile.txt' to: ",
            "help_text": "ESC:cancel Enter:confirm"
        },
        {
            "name": "Filter dialog without help text", 
            "width": 80,
            "prompt": "Filter: ",
            "help_text": ""
        },
        {
            "name": "Create file dialog on wide terminal",
            "width": 120,
            "prompt": "Create file: ",
            "help_text": "ESC:cancel Enter:create"
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Terminal width: {scenario['width']} characters")
        print(f"Prompt: '{scenario['prompt']}' ({len(scenario['prompt'])} chars)")
        print(f"Help text: '{scenario['help_text']}' ({len(scenario['help_text'])} chars)")
        print()
        
        # Calculate help space
        help_space = len(scenario['help_text']) + 6 if scenario['help_text'] else 0
        
        # OLD (BUGGY) CALCULATION - calculated space for input only, but used as total width
        old_max_input_width = scenario['width'] - len(scenario['prompt']) - help_space - 4
        # But SingleLineTextEdit.draw() interpreted this as total width including prompt!
        # So actual available text width was: old_max_input_width - len(prompt)
        old_actual_text_width = old_max_input_width - len(scenario['prompt'])
        
        # NEW (FIXED) CALCULATION - calculate total field width correctly
        new_max_field_width = scenario['width'] - help_space - 4
        new_available_text_width = new_max_field_width - len(scenario['prompt'])
        
        print("OLD (BUGGY) CALCULATION:")
        print(f"  Calculated max_input_width = {scenario['width']} - {len(scenario['prompt'])} - {help_space} - 4 = {old_max_input_width}")
        print(f"  But SingleLineTextEdit.draw() used this as total width!")
        print(f"  Actual text width = {old_max_input_width} - {len(scenario['prompt'])} = {old_actual_text_width} chars")
        print()
        
        print("NEW (FIXED) CALCULATION:")
        print(f"  max_field_width = {scenario['width']} - {help_space} - 4 = {new_max_field_width}")
        print(f"  Available text width = {new_max_field_width} - {len(scenario['prompt'])} = {new_available_text_width} chars")
        print()
        
        improvement = new_available_text_width - old_actual_text_width
        print(f"IMPROVEMENT: +{improvement} characters for text input")
        
        # Show what this means for actual filenames
        if improvement > 0:
            print(f"✓ This allows for {improvement} more characters in filenames/input")
        elif improvement == 0:
            print("✓ Same available space (no regression)")
        else:
            print(f"⚠ This reduces space by {abs(improvement)} characters")
        
        print("-" * 50)
        print()

def demonstrate_real_world_impact():
    """Show real-world impact with example filenames"""
    
    print("Real-World Impact Examples")
    print("=" * 30)
    print()
    
    # Example with 80-character terminal
    width = 80
    prompt = "Rename 'document.txt' to: "
    help_text = "ESC:cancel Enter:confirm"
    help_space = len(help_text) + 6
    
    # Old (buggy) calculation - what was actually available for text
    old_max_input_width = width - len(prompt) - help_space - 4
    old_actual_available = old_max_input_width - len(prompt)  # Double subtraction!
    
    # New (fixed) calculation  
    new_max_field_width = width - help_space - 4
    new_available = new_max_field_width - len(prompt)
    
    print(f"Terminal width: {width} characters")
    print(f"Prompt: '{prompt}' ({len(prompt)} chars)")
    print(f"Help text: '{help_text}' ({len(help_text)} chars)")
    print()
    
    print("OLD (BUGGY) - Double subtraction of prompt length:")
    print(f"  max_input_width = {width} - {len(prompt)} - {help_space} - 4 = {old_max_input_width}")
    print(f"  Actual text width = {old_max_input_width} - {len(prompt)} = {old_actual_available} chars")
    print()
    
    print("NEW (FIXED) - Correct calculation:")
    print(f"  max_field_width = {width} - {help_space} - 4 = {new_max_field_width}")
    print(f"  Available text width = {new_max_field_width} - {len(prompt)} = {new_available} chars")
    print()
    
    improvement = new_available - old_actual_available
    print(f"IMPROVEMENT: +{improvement} characters for text input")
    print()
    
    # Example filenames
    filenames = [
        "my_document.txt",
        "very_long_filename_with_details.txt", 
        "project_specification_document_v2_final.docx"
    ]
    
    print("Example filenames and whether they fit:")
    print()
    
    for filename in filenames:
        old_fits = len(filename) <= old_actual_available
        new_fits = len(filename) <= new_available
        
        print(f"'{filename}' ({len(filename)} chars)")
        print(f"  Old calculation: {'✓ Fits' if old_fits else '✗ Truncated'}")
        print(f"  New calculation: {'✓ Fits' if new_fits else '✗ Truncated'}")
        
        if not old_fits and new_fits:
            print(f"  🎉 FIXED: Now fits with the new calculation!")
        
        print()

if __name__ == '__main__':
    demonstrate_width_calculation()
    demonstrate_real_world_impact()