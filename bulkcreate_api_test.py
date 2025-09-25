#!/usr/bin/env python3
"""
Backend script that uses the same API calls as the bulkcreate-main UI.
This replicates the exact HTTP requests the UI makes.
"""

import requests
import json
import time

# API Configuration
BACKEND_URL = "http://localhost:4000"
API_BASE = f"{BACKEND_URL}/api"

# Profile configuration - exact same as UI
PROFILE_NAME = "test_api_profile"
PROFILE_CONFIG = {
    "name": PROFILE_NAME,
    "remark": "Created from backend API test",
    "proxy": "",  # No proxy
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",  # Chrome Windows
    "language": "en-US,en;q=0.9",  # English
    "timezone": "Europe/Berlin",  # Germany timezone
    "window_size": [1920, 1080],  # Desktop resolution
    "webrtc": "disabled",  # WebRTC disabled
    "startup_urls": ["https://httpbin.org/ip"],  # Your test URL
    "groupId": ""  # No group
}

def check_backend_status():
    """Check if the backend server is running"""
    try:
        response = requests.get(f"{API_BASE}/profiles", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def create_profile_api():
    """Create profile using the same API call as the UI"""
    print("🔧 Creating profile using API (same as UI)...")
    print(f"   Profile name: {PROFILE_NAME}")
    print(f"   User Agent: Chrome Windows")
    print(f"   Language: {PROFILE_CONFIG['language']}")
    print(f"   Timezone: {PROFILE_CONFIG['timezone']}")
    print(f"   Startup URL: {PROFILE_CONFIG['startup_urls'][0]}")
    print(f"   WebRTC: {PROFILE_CONFIG['webrtc']}")
    
    # Same payload structure as the UI sends
    payload = {
        "name": PROFILE_NAME,
        "config": PROFILE_CONFIG
    }
    
    try:
        response = requests.post(f"{API_BASE}/profiles", json=payload)
        
        if response.status_code == 201:
            print("✅ Profile created successfully!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to create profile:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        return False

def launch_profile_api():
    """Launch profile using the same API call as the UI"""
    print("🌐 Launching profile using API (same as UI)...")
    
    payload = {
        "name": PROFILE_NAME
    }
    
    try:
        response = requests.post(f"{API_BASE}/profiles/launch", json=payload)
        
        if response.status_code == 200:
            print("✅ Profile launch command sent!")
            print(f"   Response: {response.json()}")
            print("   The browser should open now...")
            print("   Press Ctrl+C to close the browser and clean up.")
            
            # Keep the script running to monitor the browser
            try:
                while True:
                    time.sleep(1)
                    # Check if profile is still running
                    status_response = requests.get(f"{API_BASE}/status")
                    if status_response.status_code == 200:
                        running_profiles = status_response.json()
                        if PROFILE_NAME not in running_profiles:
                            print("🛑 Browser was closed")
                            break
            except KeyboardInterrupt:
                print("\n🛑 Closing browser...")
                close_profile_api()
            
            return True
        else:
            print(f"❌ Failed to launch profile:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error launching profile: {e}")
        return False

def close_profile_api():
    """Close profile using the same API call as the UI"""
    print("🛑 Closing profile using API...")
    
    payload = {
        "name": PROFILE_NAME
    }
    
    try:
        response = requests.post(f"{API_BASE}/profiles/close", json=payload)
        
        if response.status_code == 200:
            print("✅ Profile close command sent!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Warning: Could not close profile:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Warning: Error closing profile: {e}")
        return False

def delete_profile_api():
    """Delete profile using the same API call as the UI"""
    print("🗑️  Deleting profile using API...")
    
    payload = {
        "name": PROFILE_NAME
    }
    
    try:
        response = requests.post(f"{API_BASE}/profiles/delete", json=payload)
        
        if response.status_code == 200:
            print("✅ Profile deleted successfully!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Warning: Could not delete profile:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Warning: Error deleting profile: {e}")
        return False

def list_profiles_api():
    """List profiles using the same API call as the UI"""
    print("📋 Current profiles:")
    
    try:
        response = requests.get(f"{API_BASE}/profiles")
        
        if response.status_code == 200:
            profiles = response.json()
            if profiles:
                for name, config in profiles.items():
                    print(f"  - {name}: {config.get('user_agent', 'Unknown')[:50]}...")
            else:
                print("  No profiles found")
        else:
            print(f"❌ Failed to list profiles: {response.text}")
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")

def main():
    """Main test function - replicates exact UI API calls"""
    print("=" * 70)
    print("🧪 BULKCREATE-MAIN API TEST")
    print("   (Replicating exact UI API calls)")
    print("=" * 70)
    
    # Check if backend is running
    print("🔍 Checking backend server status...")
    if not check_backend_status():
        print(f"❌ Backend server not running at {BACKEND_URL}")
        print("   Please start the backend server first:")
        print("   cd bulkcreate-main/bulkcreate-main/server")
        print("   npm run dev")
        return False
    
    print(f"✅ Backend server is running at {BACKEND_URL}")
    
    # List existing profiles
    list_profiles_api()
    print()
    
    try:
        # Step 1: Create profile (same API call as UI)
        if not create_profile_api():
            return False
        
        print()
        print("🌐 Browser will open in 3 seconds...")
        time.sleep(3)
        
        # Step 2: Launch profile (same API call as UI)
        success = launch_profile_api()
        
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
        close_profile_api()
        delete_profile_api()

if __name__ == "__main__":
    main()

