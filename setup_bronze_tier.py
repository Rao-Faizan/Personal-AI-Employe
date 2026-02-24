#!/usr/bin/env python3
"""
Setup script for Bronze Tier of Personal AI Employee
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"{title:^60}")
    print("="*60)

def check_prerequisites():
    """Check if required tools are available."""
    print_header("Checking Prerequisites")

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Check if pip is available
    try:
        import pip
        print("✅ pip is available")
    except ImportError:
        print("❌ pip is not available")
        return False

    return True

def install_dependencies():
    """Install required Python packages."""
    print_header("Installing Dependencies")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create required directory structure."""
    print_header("Creating Directory Structure")

    directories = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Plans",
        "Pending_Approval",
        "Logs",
        "Drop_Folder"
    ]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    print("\nDirectory structure created successfully!")

def create_config_files():
    """Create configuration files if they don't exist."""
    print_header("Verifying Configuration Files")

    # Check for required files
    required_files = [
        "Dashboard.md",
        "Company_Handbook.md",
        "Business_Goals.md",
        "filesystem_watcher.py",
        "orchestrator.py",
        "requirements.txt",
        "README.md"
    ]

    all_present = True
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing file: {file}")
            all_present = False
        else:
            print(f"✅ Found file: {file}")

    if all_present:
        print("\n✅ All required files are present")
    else:
        print("\n❌ Some required files are missing - please ensure Bronze Tier was set up correctly")

    return all_present

def test_setup():
    """Test the basic setup."""
    print_header("Testing Setup")

    # Create a test file in Drop_Folder to test the watcher
    test_file = Path("Drop_Folder") / "test_setup.txt"
    test_content = f"""Test file created at {time.strftime('%Y-%m-%d %H:%M:%S')}

This file tests that the file system watcher is working correctly.
When you run the filesystem_watcher.py, this file should trigger:
1. Creation of a file in Needs_Action folder
2. Copy of the file to Inbox folder
3. Update to the Dashboard
"""

    test_file.write_text(test_content)
    print(f"✅ Created test file: {test_file}")
    print("\n💡 To test the system:")
    print("   1. Run: python filesystem_watcher.py (in a separate terminal)")
    print("   2. Place files in the Drop_Folder directory")
    print("   3. Watch for action files created in Needs_Action")
    print("   4. Run: python orchestrator.py to process items")

def show_completion_message():
    """Show completion message with next steps."""
    print_header("Bronze Tier Setup Complete!")

    print("🎉 Congratulations! Your Bronze Tier AI Employee is ready!")
    print()
    print("📋 WHAT YOU HAVE:")
    print("   • Dashboard.md - Central monitoring dashboard")
    print("   • Company_Handbook.md - Rules for the AI employee")
    print("   • Folder structure: Inbox, Needs_Action, Done, etc.")
    print("   • File System Watcher - Monitors Drop_Folder for new files")
    print("   • Orchestrator - Manages the workflow")
    print("   • Complete documentation in README.md")
    print()
    print("🚀 NEXT STEPS:")
    print("   1. Review Company_Handbook.md and customize for your needs")
    print("   2. Test the file system watcher with sample files")
    print("   3. Customize Dashboard.md to show relevant metrics")
    print("   4. Consider upgrading to Silver Tier for more features")
    print()
    print("🔗 RESOURCES:")
    print("   • README.md - Complete documentation")
    print("   • Dashboard.md - Monitor your AI employee")
    print("   • Company_Handbook.md - Configure behavior rules")

def main():
    """Main setup function."""
    print("🌟 Personal AI Employee - Bronze Tier Setup")

    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required tools and try again.")
        return False

    if not install_dependencies():
        print("\n❌ Dependency installation failed. Please check requirements.txt and try again.")
        return False

    create_directories()

    if not create_config_files():
        return False

    test_setup()

    show_completion_message()

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n✅ Setup completed successfully!")
        print(f"📁 Current directory contents:")
        for item in Path(".").iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
            else:
                print(f"   📄 {item.name}")
    else:
        print(f"\n❌ Setup failed. Please address the issues above and try again.")