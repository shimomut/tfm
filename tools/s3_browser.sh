#!/bin/bash

# s3_browser.sh - Simple S3 browser using AWS CLI
# This script provides basic S3 browsing functionality

# Check if TFM environment variables are set
if [ -z "$TFM_THIS_DIR" ]; then
    echo "Error: TFM environment variables not set"
    echo "This script should be run from within TFM"
    exit 1
fi

# Check if AWS CLI is available
if ! command -v aws >/dev/null 2>&1; then
    echo "Error: AWS CLI not found"
    echo "Install with: pip install awscli"
    echo "Configure with: aws configure"
    exit 1
fi

echo "TFM S3 Browser"
echo "=============="
echo

# Function to list S3 buckets
list_buckets() {
    echo "Available S3 Buckets:"
    echo "--------------------"
    aws s3 ls 2>/dev/null | while read -r line; do
        bucket_name=$(echo "$line" | awk '{print $3}')
        echo "  s3://$bucket_name/"
    done
    echo
}

# Function to list objects in a bucket/prefix
list_objects() {
    local s3_path="$1"
    echo "Contents of $s3_path:"
    echo "$(printf '%*s' ${#s3_path} '' | tr ' ' '-')"
    
    # List with human-readable sizes
    aws s3 ls "$s3_path" --human-readable --summarize 2>/dev/null || {
        echo "Error: Unable to list contents of $s3_path"
        echo "Check permissions and bucket existence"
        return 1
    }
    echo
}

# Function to show object details
show_object_details() {
    local s3_path="$1"
    local s3_object_path="${s3_path#s3://}"
    local bucket="${s3_object_path%%/*}"
    local key="${s3_object_path#*/}"
    
    echo "Object Details: $s3_path"
    echo "$(printf '%*s' $((${#s3_path} + 16)) '' | tr ' ' '-')"
    
    aws s3api head-object --bucket "$bucket" --key "$key" --output table 2>/dev/null || {
        echo "Error: Unable to get object details"
        echo "Object may not exist or you may lack permissions"
        return 1
    }
    echo
}

# Main logic
if [[ "$TFM_THIS_DIR" == s3://* ]]; then
    echo "Current S3 Location: $TFM_THIS_DIR"
    echo
    
    # List current location
    list_objects "$TFM_THIS_DIR"
    
    # If files are selected, show details
    if [ -n "$TFM_THIS_SELECTED" ]; then
        echo "Selected Object Details:"
        echo "======================="
        
        eval "SELECTED_FILES=($TFM_THIS_SELECTED)"
        for file in "${SELECTED_FILES[@]}"; do
            if [ -n "$file" ]; then
                full_path="$TFM_THIS_DIR$file"
                show_object_details "$full_path"
            fi
        done
    fi
    
else
    echo "Current location is not an S3 path: $TFM_THIS_DIR"
    echo "Showing available S3 buckets instead:"
    echo
    list_buckets
    
    echo "To browse S3 in TFM:"
    echo "1. Navigate to an S3 path: s3://bucket-name/"
    echo "2. Use this tool to explore S3 contents"
    echo "3. Select objects and run this tool for details"
fi

echo
echo "AWS CLI Commands for S3:"
echo "------------------------"
echo "List buckets:           aws s3 ls"
echo "List bucket contents:   aws s3 ls s3://bucket-name/"
echo "Copy to S3:            aws s3 cp file.txt s3://bucket/file.txt"
echo "Copy from S3:          aws s3 cp s3://bucket/file.txt file.txt"
echo "Sync directories:      aws s3 sync ./local-dir s3://bucket/remote-dir"
echo

echo "Press Enter to continue..."
read