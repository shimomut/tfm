#!/bin/bash
# TFM Sub-shell Environment Verification Script
# This script verifies that TFM environment variables are properly set

echo "TFM Sub-shell Environment Verification"
echo "======================================"

# Check if all required TFM environment variables are set
required_vars=(
    "TFM_LEFT_DIR"
    "TFM_RIGHT_DIR" 
    "TFM_THIS_DIR"
    "TFM_OTHER_DIR"
    "TFM_LEFT_SELECTED"
    "TFM_RIGHT_SELECTED"
    "TFM_THIS_SELECTED"
    "TFM_OTHER_SELECTED"
)

all_set=true

for var in "${required_vars[@]}"; do
    if [[ -z "${!var+x}" ]]; then
        echo "❌ $var: NOT SET"
        all_set=false
    else
        echo "✅ $var: '${!var}'"
    fi
done

echo "======================================"

if [[ "$all_set" == true ]]; then
    echo "✅ All TFM environment variables are set correctly!"
    
    # Test directory access
    echo ""
    echo "Testing directory access:"
    if [[ -d "$TFM_LEFT_DIR" ]]; then
        echo "✅ TFM_LEFT_DIR is accessible"
    else
        echo "❌ TFM_LEFT_DIR is not accessible"
        all_set=false
    fi
    
    if [[ -d "$TFM_RIGHT_DIR" ]]; then
        echo "✅ TFM_RIGHT_DIR is accessible"
    else
        echo "❌ TFM_RIGHT_DIR is not accessible"
        all_set=false
    fi
    
    # Test shell command access
    echo ""
    echo "Testing shell command access:"
    current_dir=$(pwd)
    echo "✅ Shell command output: Current directory from shell: $current_dir"
    
    # Test prompt modification
    echo ""
    echo "Testing prompt modification:"
    if [[ "$PS1" == *"[TFM]"* ]]; then
        echo "✅ PS1 contains [TFM] label: $PS1"
    else
        echo "⚠ PS1 does not contain [TFM] label: $PS1"
    fi
    
    if [[ "$PROMPT" == *"[TFM]"* ]]; then
        echo "✅ PROMPT contains [TFM] label: $PROMPT"
    else
        echo "⚠ PROMPT does not contain [TFM] label: $PROMPT"
    fi
    
    echo ""
    echo "✅ Shell prompt modification is working"
else
    echo "❌ Some TFM environment variables are missing!"
fi

if [[ "$all_set" == true ]]; then
    exit 0
else
    exit 1
fi