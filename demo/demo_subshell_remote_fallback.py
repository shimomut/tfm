#!/usr/bin/env python3
"""
Demo: Subshell Remote Directory Fallback

This demo shows how TFM handles subshell and external program execution
when browsing remote directories (like S3). When the current pane is
browsing a remote directory, TFM falls back to using TFM's working
directory instead of failing.

Key Features Demonstrated:
1. Remote path detection using is_remote() method
2. Fallback to TFM's working directory for remote paths
3. Normal behavior for local paths
4. Consistent behavior for both subshell and external programs
"""

import os
import sys
from pathlib import Path as PathlibPath

# Add src directory to path for imports
src_dir = PathlibPath(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from tfm_path import Path


class MockRemotePath:
    """Mock remote path that simulates S3 or other remote storage"""
    
    def __init__(self, path_str):
        self.path_str = path_str
    
    def __str__(self):
        return self.path_str
    
    def is_remote(self):
        return True
    
    def get_scheme(self):
        return 's3'


class MockLocalPath:
    """Mock local path for comparison"""
    
    def __init__(self, path_str):
        self.path_str = path_str
    
    def __str__(self):
        return self.path_str
    
    def is_remote(self):
        return False
    
    def get_scheme(self):
        return 'file'


def demonstrate_working_directory_selection():
    """Demonstrate how working directory is selected based on path type"""
    
    print("=" * 60)
    print("TFM Subshell Remote Directory Fallback Demo")
    print("=" * 60)
    print()
    
    # Simulate TFM's current working directory
    tfm_working_dir = os.getcwd()
    print(f"TFM's working directory: {tfm_working_dir}")
    print()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Local Directory',
            'path': MockLocalPath('/home/user/documents'),
            'description': 'Normal local filesystem directory'
        },
        {
            'name': 'S3 Bucket Root',
            'path': MockRemotePath('s3://my-bucket/'),
            'description': 'S3 bucket root directory'
        },
        {
            'name': 'S3 Subdirectory',
            'path': MockRemotePath('s3://my-bucket/projects/data/'),
            'description': 'S3 subdirectory with multiple levels'
        },
        {
            'name': 'Local Home Directory',
            'path': MockLocalPath('/home/user'),
            'description': 'User home directory'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Current pane path: {scenario['path']}")
        print(f"   Is remote: {scenario['path'].is_remote()}")
        print(f"   Scheme: {scenario['path'].get_scheme()}")
        
        # Demonstrate the working directory selection logic
        if scenario['path'].is_remote():
            working_dir = tfm_working_dir
            print(f"   → Subshell working directory: {working_dir} (TFM fallback)")
            print(f"   → Reason: Remote directory cannot be used as shell working directory")
        else:
            working_dir = str(scenario['path'])
            print(f"   → Subshell working directory: {working_dir} (pane directory)")
            print(f"   → Reason: Local directory can be used directly")
        
        print()


def demonstrate_environment_variables():
    """Demonstrate how environment variables are set regardless of working directory"""
    
    print("=" * 60)
    print("Environment Variables (Always Set Regardless of Working Directory)")
    print("=" * 60)
    print()
    
    # Simulate pane configuration
    left_pane_path = MockLocalPath('/home/user/projects')
    right_pane_path = MockRemotePath('s3://my-bucket/data/')
    current_pane_path = right_pane_path  # Currently browsing S3
    
    print("Pane Configuration:")
    print(f"  Left pane:    {left_pane_path} (local)")
    print(f"  Right pane:   {right_pane_path} (remote)")
    print(f"  Current pane: {current_pane_path} (remote)")
    print()
    
    print("TFM Environment Variables (would be set in subshell):")
    print(f"  TFM_LEFT_DIR:   {left_pane_path}")
    print(f"  TFM_RIGHT_DIR:  {right_pane_path}")
    print(f"  TFM_THIS_DIR:   {current_pane_path}")
    print(f"  TFM_OTHER_DIR:  {left_pane_path}")
    print(f"  TFM_ACTIVE:     1")
    print()
    
    print("Working Directory Selection:")
    if current_pane_path.is_remote():
        working_dir = os.getcwd()
        print(f"  Shell working directory: {working_dir}")
        print(f"  Reason: Current pane is remote ({current_pane_path})")
        print(f"  Fallback: Use TFM's working directory")
    else:
        working_dir = str(current_pane_path)
        print(f"  Shell working directory: {working_dir}")
        print(f"  Reason: Current pane is local")
    
    print()
    print("Note: Environment variables still contain the actual pane paths,")
    print("      allowing external programs to access remote directory information")
    print("      even when the shell working directory is different.")


def demonstrate_use_cases():
    """Demonstrate practical use cases for this feature"""
    
    print("=" * 60)
    print("Practical Use Cases")
    print("=" * 60)
    print()
    
    use_cases = [
        {
            'title': 'S3 File Management',
            'scenario': 'Browsing S3 bucket with AWS CLI tools',
            'current_pane': 's3://my-bucket/logs/',
            'commands': [
                'aws s3 ls $TFM_THIS_DIR',
                'aws s3 cp $TFM_THIS_DIR/file.log .',
                'aws s3 sync $TFM_THIS_DIR ./local-backup/'
            ]
        },
        {
            'title': 'Remote Development',
            'scenario': 'Working with remote repositories and local tools',
            'current_pane': 's3://code-bucket/projects/',
            'commands': [
                'git clone https://github.com/user/repo.git',
                'aws s3 cp $TFM_THIS_DIR/config.json ./repo/',
                'cd repo && make build'
            ]
        },
        {
            'title': 'Data Processing',
            'scenario': 'Processing remote data with local scripts',
            'current_pane': 's3://data-bucket/datasets/',
            'commands': [
                'python process_data.py --input $TFM_THIS_DIR',
                'aws s3 cp results.csv $TFM_THIS_DIR/',
                './analyze.sh $TFM_THIS_DIR/results.csv'
            ]
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        print(f"{i}. {use_case['title']}")
        print(f"   Scenario: {use_case['scenario']}")
        print(f"   Current pane: {use_case['current_pane']} (remote)")
        print(f"   Shell working directory: {os.getcwd()} (TFM fallback)")
        print(f"   TFM_THIS_DIR: {use_case['current_pane']}")
        print()
        print("   Example commands in subshell:")
        for cmd in use_case['commands']:
            print(f"     $ {cmd}")
        print()


def main():
    """Run the complete demo"""
    demonstrate_working_directory_selection()
    demonstrate_environment_variables()
    demonstrate_use_cases()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("Benefits of Remote Directory Fallback:")
    print("• Subshell works reliably when browsing remote directories")
    print("• External programs can still access remote paths via TFM_* variables")
    print("• Local tools can be used alongside remote directory browsing")
    print("• No functionality is lost - only working directory changes")
    print("• Consistent behavior across all remote storage types")
    print()
    print("Implementation Details:")
    print("• Uses path.is_remote() to detect remote directories")
    print("• Falls back to os.getcwd() (TFM's working directory)")
    print("• Applies to both subshell and external program execution")
    print("• Environment variables always reflect actual pane paths")
    print("• User is informed when fallback occurs")


if __name__ == '__main__':
    main()