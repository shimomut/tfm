# TFM Installation Guide

## System Requirements

### Minimum Requirements
- **Python 3.6+**: Core language requirement
- **Terminal**: Any terminal with curses support
- **Operating System**: macOS, Linux, or Windows with compatible terminal

### Recommended Setup
- **Python 3.8+**: For best performance and compatibility
- **Modern Terminal**: Terminal.app (macOS), GNOME Terminal (Linux), Windows Terminal (Windows)
- **UTF-8 Support**: For proper character display

## Installation Methods

### Method 1: Direct Run (Recommended for Testing)
```bash
# Clone or download TFM
git clone https://github.com/shimomut/tfm.git
cd tfm

# Run directly
python3 tfm.py
```

### Method 2: Package Installation
```bash
# Install from source directory
cd tfm
python3 setup.py install

# Run installed version
tfm
```

### Method 3: Development Installation
```bash
# Install in development mode (changes reflected immediately)
cd tfm
pip install -e .

# Run from anywhere
tfm
```

## Optional Dependencies

### Enhanced Syntax Highlighting
```bash
pip install pygments
```
**Benefits**: 
- Syntax highlighting for 20+ file formats
- Better code viewing experience
- Automatic file type detection

**Without pygments**: Text files display as plain text

### AWS S3 Support
```bash
pip install boto3
```
**Benefits**:
- Navigate S3 buckets with s3:// URIs
- Full file operations on S3 objects
- Seamless local/cloud integration

**Setup AWS Credentials**:
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# Option 3: IAM roles (for EC2 instances)
# No additional setup required
```

### Windows Support
```bash
# Windows-specific curses library
pip install windows-curses
```
**Note**: Automatically installed via setup.py on Windows systems

## Platform-Specific Setup

### macOS
```bash
# Ensure Python 3 is installed
python3 --version

# Install optional dependencies
pip3 install pygments boto3

# Run TFM
python3 tfm.py
```

**Terminal Recommendations**:
- **Terminal.app**: Built-in, works well
- **iTerm2**: Enhanced features and customization
- **Alacritty**: High performance, GPU-accelerated

### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL/Fedora
sudo yum install python3 python3-pip
# or
sudo dnf install python3 python3-pip

# Install optional dependencies
pip3 install pygments boto3

# Run TFM
python3 tfm.py
```

**Terminal Recommendations**:
- **GNOME Terminal**: Standard, reliable
- **Konsole**: KDE terminal with good features
- **Alacritty**: Cross-platform, high performance

### Windows
```bash
# Install Python from python.org or Microsoft Store
python --version

# Install dependencies (including windows-curses)
pip install pygments boto3 windows-curses

# Run TFM
python tfm.py
```

**Terminal Recommendations**:
- **Windows Terminal**: Modern, feature-rich (recommended)
- **PowerShell**: Built-in, basic support
- **WSL**: Linux subsystem for full compatibility

## Verification

### Test Basic Functionality
```bash
# Run TFM
python3 tfm.py

# Test basic navigation
# - Use arrow keys to navigate
# - Press Tab to switch panes
# - Press ? for help
# - Press q to quit
```

### Test Color Support
```bash
# Test color capabilities
python3 tfm.py --color-test info

# Test color schemes
python3 tfm.py --color-test schemes

# Interactive color testing
python3 tfm.py --color-test interactive
```

### Test S3 Support (if installed)
```bash
# Navigate to S3 bucket (requires AWS credentials)
# In TFM, navigate to: s3://your-bucket-name/
```

## Configuration

### First Run Setup
On first run, TFM automatically creates:
- **Configuration directory**: `~/.tfm/`
- **Configuration file**: `~/.tfm/config.py`
- **Default settings**: Copied from template

### Access Configuration
```bash
# Method 1: From within TFM
# Press Z → Settings Menu → Edit Configuration

# Method 2: Direct edit
vim ~/.tfm/config.py
code ~/.tfm/config.py
nano ~/.tfm/config.py
```

### Basic Configuration
```python
# ~/.tfm/config.py
class Config:
    # Color scheme
    COLOR_SCHEME = 'dark'  # or 'light'
    
    # Text editor
    TEXT_EDITOR = 'vim'  # or 'nano', 'code', etc.
    
    # Startup directories
    STARTUP_LEFT_PATH = "~"
    STARTUP_RIGHT_PATH = "~/Documents"
    
    # Favorite directories
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Projects', 'path': '~/projects'},
    ]
```

## Troubleshooting

### Common Issues

#### Python Not Found
```bash
# Try different Python commands
python3 tfm.py
python tfm.py
py tfm.py  # Windows
```

#### Import Errors
```bash
# Ensure you're in the TFM directory
cd /path/to/tfm
python3 tfm.py

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### Color Issues
```bash
# Test terminal color support
python3 tfm.py --color-test diagnose

# Try fallback mode
python3 tfm.py --color-test fallback-test

# Set environment variable
export TERM=xterm-256color
```

#### Permission Errors
```bash
# Check file permissions
ls -la tfm.py

# Make executable if needed
chmod +x tfm.py

# Check Python permissions
python3 --version
```

#### S3 Access Issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Check boto3 installation
python3 -c "import boto3; print(boto3.__version__)"

# Test S3 access
aws s3 ls
```

### Performance Issues

#### Slow Startup
- Check for large directories in startup paths
- Reduce MAX_JUMP_DIRECTORIES in config
- Disable S3 support if not needed

#### Memory Usage
- Reduce MAX_SEARCH_RESULTS in config
- Clear directory history periodically
- Limit MAX_LOG_MESSAGES

#### Terminal Responsiveness
- Set ESCDELAY environment variable: `export ESCDELAY=100`
- Use faster terminal emulator
- Reduce PROGRESS_ANIMATION_SPEED

## Advanced Installation

### Virtual Environment
```bash
# Create virtual environment
python3 -m venv tfm-env
source tfm-env/bin/activate  # Linux/macOS
# or
tfm-env\Scripts\activate  # Windows

# Install dependencies
pip install pygments boto3

# Run TFM
python3 tfm.py
```

### System-wide Installation
```bash
# Install for all users (requires sudo)
sudo python3 setup.py install

# Create system-wide launcher
sudo ln -s /usr/local/bin/tfm /usr/bin/tfm
```

### Docker Installation
```dockerfile
FROM python:3.9-slim

RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/shimomut/tfm.git /tfm
WORKDIR /tfm
RUN pip install pygments boto3

CMD ["python3", "tfm.py"]
```

## Uninstallation

### Remove Installed Package
```bash
pip uninstall tfm
```

### Remove Configuration
```bash
# Remove user configuration
rm -rf ~/.tfm/

# Remove any custom scripts or shortcuts
```

### Clean Virtual Environment
```bash
# Deactivate and remove virtual environment
deactivate
rm -rf tfm-env/
```

This installation guide covers all common scenarios for setting up TFM on different platforms and configurations.