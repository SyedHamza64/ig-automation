#!/usr/bin/env python3
"""
Backend script to create and launch a profile with the exact same settings
as the bulkcreate-main UI would create. This replicates the UI process exactly.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Configuration - same as your UI settings
PROFILE_NAME = "test_backend_profile"
PROFILE_CONFIG = {
    "name": PROFILE_NAME,
    "remark": "Created from backend script",
    "proxy": "",  # No proxy
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",  # Chrome Windows
    "language": "en-US,en;q=0.9",  # English
    "timezone": "Europe/Berlin",  # Germany timezone
    "window_size": [1920, 1080],  # Desktop resolution
    "webrtc": "disabled",  # WebRTC disabled
    "startup_urls": ["https://httpbin.org/ip"],  # Your test URL
    "groupId": ""  # No group
}

# Paths
BULKCREATE_PATH = Path(__file__).parent / "bulkcreate-main" / "bulkcreate-main"
MANAGER_PY = BULKCREATE_PATH / "manager.py"

def create_profile_backend():
    """Create a profile using the backend manager.py (same as UI does)"""
    print("🔧 Creating profile using backend manager.py...")
    print(f"   Profile name: {PROFILE_NAME}")
    print(f"   User Agent: Chrome Windows")
    print(f"   Language: {PROFILE_CONFIG['language']}")
    print(f"   Timezone: {PROFILE_CONFIG['timezone']}")
    print(f"   Startup URL: {PROFILE_CONFIG['startup_urls'][0]}")
    print(f"   WebRTC: {PROFILE_CONFIG['webrtc']}")
    
    # Build the command exactly like the server.js does
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "create",
        "--name", PROFILE_NAME,
        "--config", json.dumps(PROFILE_CONFIG)
    ]
    
    try:
        print(f"🚀 Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        
        if result.returncode == 0:
            print("✅ Profile created successfully!")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed to create profile:")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def launch_profile_backend():
    """Launch the profile using the backend manager.py (same as UI does)"""
    print("🌐 Launching profile using backend manager.py...")
    
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "launch",
        "--name", PROFILE_NAME
    ]
    
    try:
        print(f"🚀 Running command: {' '.join(cmd)}")
        print("   The browser will open and stay open for testing.")
        print("   Press Ctrl+C to close the browser and clean up.")
        
        # Launch the profile (this will block until browser is closed)
        result = subprocess.run(cmd, cwd=str(BULKCREATE_PATH))
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n🛑 Browser closed by user")
        return True
    except Exception as e:
        print(f"❌ Error launching profile: {e}")
        return False

def list_profiles():
    """List existing profiles"""
    print("📋 Current profiles:")
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "list"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        if result.returncode == 0:
            profiles = json.loads(result.stdout)
            if profiles:
                for name, config in profiles.items():
                    print(f"  - {name}: {config.get('user_agent', 'Unknown')[:50]}...")
            else:
                print("  No profiles found")
        else:
            print(f"❌ Failed to list profiles: {result.stderr}")
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")

def cleanup_profile():
    """Clean up the test profile"""
    print("🧹 Cleaning up test profile...")
    
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "delete",
        "--name", PROFILE_NAME
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        if result.returncode == 0:
            print("✅ Test profile cleaned up successfully!")
            return True
        else:
            print(f"⚠️  Warning: Could not clean up profile: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Warning: Error cleaning up profile: {e}")
        return False

def main():
    """Main test function - replicates exact UI process"""
    print("=" * 70)
    print("🧪 BULKCREATE-MAIN BACKEND PROFILE TEST")
    print("   (Replicating exact UI process)")
    print("=" * 70)
    
    # Check if bulkcreate-main exists
    if not BULKCREATE_PATH.exists():
        print(f"❌ bulkcreate-main directory not found at: {BULKCREATE_PATH}")
        return False
    
    if not MANAGER_PY.exists():
        print(f"❌ manager.py not found at: {MANAGER_PY}")
        return False
    
    print(f"✅ Found bulkcreate-main at: {BULKCREATE_PATH}")
    
    # List existing profiles
    list_profiles()
    print()
    
    try:
        # Step 1: Create profile (same as UI)
        if not create_profile_backend():
            return False
        
        print()
        print("🌐 Browser will open in 3 seconds...")
        time.sleep(3)
        
        # Step 2: Launch profile (same as UI)
        success = launch_profile_backend()
        
        if success:
            print("✅ Test completed successfully!")
        else:
            print("❌ Test failed!")
        
        return success
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Always try to clean up
        print()
        cleanup_profile()

if __name__ == "__main__":
    main()

