#!/usr/bin/env python3
"""
Test script to verify that enhanced mode profiles can be resized properly.
This script creates a test profile and launches it to check if window resizing works.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Paths
BULKCREATE_PATH = Path(__file__).parent
ENHANCED_SCRIPT = BULKCREATE_PATH / "bulkcreate_enhanced_test.py"

def test_window_resize():
    """Test that enhanced mode profiles can be resized"""
    
    test_profile_name = "test_resize_profile"
    
    print("🧪 Testing window resize functionality for enhanced mode profiles...")
    
    # Create test profile with enhanced mode
    enhanced_config = {
        "enhanced_mode": True,
        "profile_name": test_profile_name,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "language": "en-US,en;q=0.9",
        "timezone": "Europe/Berlin",
        "webrtc": "disabled",
        "window_size": [800, 600],  # Start with smaller window
        "startup_urls": [],
        "remark": "Test profile for window resize functionality",
        "deviceType": "windows",
        "anti_detection": {
            "dynamic_user_agent": False,
            "enhanced_canvas_fingerprinting": False,
            "realistic_device_metrics": False,
            "hardware_randomization": False,
            "advanced_navigator_properties": False
        }
    }
    
    print(f"📝 Creating test profile: {test_profile_name}")
    
    # Create the profile
    cmd = [
        sys.executable,
        str(ENHANCED_SCRIPT),
        "--create-only",
        "--name", test_profile_name,
        "--config", json.dumps(enhanced_config)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        
        if result.returncode == 0:
            print("✅ Test profile created successfully!")
        else:
            print(f"❌ Failed to create test profile: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating test profile: {e}")
        return False
    
    print(f"🚀 Launching test profile: {test_profile_name}")
    print("   - The browser window should open at 800x600")
    print("   - Try resizing the window by dragging the edges")
    print("   - Try maximizing the window")
    print("   - The window should resize properly without fixed aspect ratio")
    print("   - Press Ctrl+C to close the test")
    
    # Launch the profile
    launch_cmd = [
        sys.executable,
        str(ENHANCED_SCRIPT),
        "--launch-only",
        "--name", test_profile_name
    ]
    
    try:
        # Launch in background and monitor
        process = subprocess.Popen(launch_cmd, cwd=str(BULKCREATE_PATH))
        
        print("✅ Test profile launched! Check if you can resize the window.")
        print("   If the window resizes properly, the fix is working!")
        
        # Keep the process running
        try:
            while True:
                time.sleep(1)
                # Check if process is still running
                if process.poll() is not None:
                    print("🛑 Browser was closed")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Closing test browser...")
            process.terminate()
            process.wait()
        
        print("✅ Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error launching test profile: {e}")
        return False
    
    finally:
        # Clean up test profile
        print("🧹 Cleaning up test profile...")
        cleanup_cmd = [
            sys.executable,
            str(BULKCREATE_PATH / "manager.py"),
            "delete",
            "--name", test_profile_name
        ]
        
        try:
            subprocess.run(cleanup_cmd, capture_output=True, cwd=str(BULKCREATE_PATH))
            print("✅ Test profile cleaned up")
        except Exception as e:
            print(f"⚠️ Could not clean up test profile: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ENHANCED MODE WINDOW RESIZE TEST")
    print("   Testing if enhanced mode profiles can be resized properly")
    print("=" * 60)
    
    success = test_window_resize()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("   If you were able to resize the browser window, the fix is working!")
    else:
        print("\n❌ Test failed!")
        print("   Check the error messages above for details.")
