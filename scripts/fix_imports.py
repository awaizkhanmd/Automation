"""
Fix import issues and set up the project for development.

This script helps resolve Python import path issues and sets up
the project structure correctly.
"""

import sys
import os
from pathlib import Path

def fix_project_setup():
    """Fix project setup for development."""
    project_root = Path(__file__).parent.parent
    
    print("🔧 Fixing Job Automation Project Setup...")
    print(f"📁 Project root: {project_root}")
    
    # Check if we're in the right directory
    required_dirs = ['src', 'config', 'database', 'scripts']
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            print(f"❌ Missing directory: {dir_name}")
        else:
            print(f"✅ Found directory: {dir_name}")
    
    if missing_dirs:
        print(f"\n⚠️  Missing directories: {', '.join(missing_dirs)}")
        print("Please ensure you're running this from the project root directory.")
        return False
    
    # Check Python path
    src_path = str(project_root)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"✅ Added to Python path: {src_path}")
    
    # Test imports
    print("\n🔍 Testing imports...")
    
    try:
        # Test config imports
        from config.settings import get_settings
        print("✅ Config import successful")
        
        # Test database imports
        from database.connection import get_database_manager
        print("✅ Database import successful")
        
        # Test utils imports
        from src.utils.logger import configure_logging
        print("✅ Utils import successful")
        
        # Test core imports (Phase 1.2)
        try:
            from src.core.browser_manager import BrowserManager
            from src.core.profile_manager import ProfileManager
            print("✅ Core imports successful")
        except ImportError as e:
            print(f"⚠️  Core imports failed (Phase 1.2 not complete): {e}")
        
        print("\n🎉 Import setup successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you're in the project root directory")
        print("2. Check that all files from Phase 1.1 and 1.2 are created")
        print("3. Verify virtual environment is activated")
        return False

def install_in_development_mode():
    """Install the package in development mode."""
    project_root = Path(__file__).parent.parent
    setup_py = project_root / "setup.py"
    
    if not setup_py.exists():
        print("❌ setup.py not found")
        return False
    
    print("📦 Installing package in development mode...")
    
    # This would normally run: pip install -e .
    print("Run this command from the project root:")
    print("pip install -e .")
    
    return True

if __name__ == "__main__":
    print("🚀 Job Automation Project Setup Fixer")
    print("=" * 50)
    
    if fix_project_setup():
        print("\n✅ Project setup is working correctly!")
        print("\n📝 To permanently fix import issues, you can:")
        print("1. Run: pip install -e . (from project root)")
        print("2. Or use the fixed scripts provided")
    else:
        print("\n❌ Project setup needs attention")
        print("Please review the errors above and ensure all files are in place")