#!/bin/bash

# s3_info.sh - Display information about S3 paths and objects
# This script demonstrates how TFM environment variables work with S3 paths

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

echo "TFM S3 Information Tool"
echo "======================"
echo

# Display current directory information
echo "Current Directory: $TFM_THIS_DIR"

# Check if current directory is an S3 path
if [[ "$TFM_THIS_DIR" == s3://* ]]; then
    echo "Storage Type: AWS S3"
    
    # Extract bucket and prefix from S3 path
    S3_PATH="${TFM_THIS_DIR#s3://}"
    if [[ "$S3_PATH" == */* ]]; then
        BUCKET="${S3_PATH%%/*}"
        PREFIX="${S3_PATH#*/}"
    else
        BUCKET="$S3_PATH"
        PREFIX=""
    fi
    
    echo "S3 Bucket: $BUCKET"
    echo "S3 Prefix: ${PREFIX:-'(root)'}"
    echo
    
    # Check if AWS CLI is available
    if command -v aws >/dev/null 2>&1; then
        echo "AWS CLI Information:"
        echo "-------------------"
        
        # Get AWS identity
        echo "AWS Identity:"
        aws sts get-caller-identity --output table 2>/dev/null || echo "  Unable to get AWS identity"
        echo
        
        # Get bucket region
        echo "Bucket Region:"
        aws s3api get-bucket-location --bucket "$BUCKET" --output text 2>/dev/null || echo "  Unable to get bucket region"
        echo
        
        # Get bucket info
        echo "Bucket Objects Count:"
        aws s3 ls "s3://$BUCKET/$PREFIX" --recursive --summarize 2>/dev/null | tail -2 || echo "  Unable to list bucket contents"
        echo
    else
        echo "AWS CLI not available - install with: pip install awscli"
        echo
    fi
    
else
    echo "Storage Type: Local File System"
    echo
fi

# Display selected files information
if [ -n "$TFM_THIS_SELECTED" ]; then
    echo "Selected Files/Objects:"
    echo "----------------------"
    
    # Parse selected files (properly handle quoted filenames)
    eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
    
    for file in "${SELECTED_FILES[@]}"; do
        if [ -n "$file" ]; then
            FULL_PATH="$TFM_THIS_DIR$file"
            echo "  - $file"
            
            # If it's an S3 path, show additional S3 info
            if [[ "$TFM_THIS_DIR" == s3://* ]]; then
                echo "    Full S3 Path: $FULL_PATH"
                
                # Try to get object info with AWS CLI
                if command -v aws >/dev/null 2>&1; then
                    S3_OBJECT_PATH="${FULL_PATH#s3://}"
                    OBJECT_BUCKET="${S3_OBJECT_PATH%%/*}"
                    OBJECT_KEY="${S3_OBJECT_PATH#*/}"
                    
                    # Get object metadata
                    aws s3api head-object --bucket "$OBJECT_BUCKET" --key "$OBJECT_KEY" --output table 2>/dev/null || echo "    Unable to get object metadata"
                fi
            fi
        fi
    done
    echo
else
    echo "No files selected"
    echo
fi

# Display other pane information
if [ -n "$TFM_OTHER_DIR" ]; then
    echo "Other Pane Directory: $TFM_OTHER_DIR"
    
    if [[ "$TFM_OTHER_DIR" == s3://* ]]; then
        echo "Other Pane Type: AWS S3"
    else
        echo "Other Pane Type: Local File System"
    fi
    echo
fi

# Show environment variables for debugging
echo "TFM Environment Variables:"
echo "-------------------------"
echo "TFM_THIS_DIR: $TFM_THIS_DIR"
echo "TFM_OTHER_DIR: $TFM_OTHER_DIR"
echo "TFM_THIS_SELECTED: $TFM_THIS_SELECTED"
echo "TFM_OTHER_SELECTED: $TFM_OTHER_SELECTED"
echo "TFM_ACTIVE: $TFM_ACTIVE"
echo

echo "Press Enter to continue..."
read