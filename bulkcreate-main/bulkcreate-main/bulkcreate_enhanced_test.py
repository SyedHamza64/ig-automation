#!/usr/bin/env python3
"""
Enhanced backend script that combines bulkcreate-main manager.py with 
launch_single_profile.py anti-detection measures to avoid CAPTCHA issues.
"""

import os
import sys
import json
import subprocess
import time
import random
import logging
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Enhanced Profile Manager")
parser.add_argument('--create-only', action='store_true', help='Only create profile, do not launch')
parser.add_argument('--launch-only', action='store_true', help='Only launch profile, do not create')
parser.add_argument('--name', type=str, help='Profile name to create/launch')
parser.add_argument('--config', type=str, help='Profile configuration JSON')
args = parser.parse_args()

# Configuration - same as your UI settings but for 5 profiles
PROFILE_NAMES = [f"test_enhanced_profile_{i}" for i in range(1, 6)]
PROFILE_CONFIG = {
    "name": "test_enhanced_profile",
    "remark": "Created from enhanced backend script",
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
BULKCREATE_PATH = Path(__file__).parent
MANAGER_PY = BULKCREATE_PATH / "manager.py"

def create_profile_with_enhanced_detection(profile_idx):
    """Create a profile using bulkcreate-main but with enhanced anti-detection"""
    
    profile_name = PROFILE_NAMES[profile_idx - 1]
    
    # Create profile using bulkcreate-main manager.py
    print(f"🔧 Creating profile {profile_idx} using bulkcreate-main...")
    
    # Build the command exactly like the server.js does
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "create",
        "--name", profile_name,
        "--config", json.dumps(PROFILE_CONFIG)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        
        if result.returncode == 0:
            logger.info(f"✅ Profile {profile_idx} created successfully!")
        else:
            logger.error(f"❌ Failed to create profile {profile_idx}: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"❌ Error creating profile {profile_idx}: {e}")
        return None
    
    # Now launch with enhanced anti-detection (like launch_single_profile.py)
    return launch_profile_enhanced(profile_name, profile_idx)

def launch_profile_enhanced(profile_name, profile_idx):
    """Launch profile with enhanced anti-detection measures"""
    
    # Get profile path from bulkcreate-main
    profile_path = BULKCREATE_PATH / "selenium_profiles" / profile_name
    
    chrome_options = Options()
    
    # Profile and user agent settings
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument(f"--user-agent={PROFILE_CONFIG['user_agent']}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument(f"--lang=en-US")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    # Enhanced anti-detection measures (from launch_single_profile.py)
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Additional stealth options
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Prefs to make browser look more natural
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
            "media_stream": 2,
        },
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.media_stream_mic": 2,
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Set up ChromeDriver service
    chromedriver_path = "E:/work/IG-Automation/bulkcreate-main/bulkcreate-main/chromedriver.exe"
    service = Service(chromedriver_path)
    
    try:
        # Create the webdriver instance
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set window size and position with grid layout
        window_width = 800
        window_height = 600
        
        # Calculate position in grid (2x3 grid)
        row = (profile_idx - 1) // 3
        col = (profile_idx - 1) % 3
        
        x_offset = col * window_width + 50
        y_offset = row * window_height + 50
        
        driver.set_window_size(window_width, window_height)
        driver.set_window_position(x_offset, y_offset)
        
        # Enhanced anti-detection script injection (from launch_single_profile.py)
        seed = 12345 + profile_idx
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': f'''
                (function() {{
                    const SEED = {seed};
                    try {{
                        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                        Object.defineProperty(navigator, 'platform', {{ get: () => 'Win32' }});
                        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => 8 }});
                        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => 8 }});
                        Object.defineProperty(navigator, 'languages', {{ get: () => ['en-US', 'en'] }});

                        // Plugins shape
                        const fakePlugins = [{{ name: 'Chrome PDF Plugin' }}, {{ name: 'Chrome PDF Viewer' }}, {{ name: 'Native Client' }}];
                        const pluginsProxy = new Proxy(fakePlugins, {{
                            get(target, prop) {{
                                if (prop === 'length') return target.length;
                                if (!isNaN(prop)) return target[prop];
                                return target[prop];
                            }}
                        }});
                        Object.defineProperty(navigator, 'plugins', {{ get: () => pluginsProxy }});

                        // Canvas noise for fingerprint variation
                        const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                        CanvasRenderingContext2D.prototype.getImageData = function() {{
                            const data = origGetImageData.apply(this, arguments);
                            try {{
                                const idx = (SEED % 100) * 4;
                                if (data && data.data && data.data.length > idx + 3) {{
                                    data.data[idx] = (data.data[idx] + (SEED % 7)) % 256;
                                    data.data[idx+1] = (data.data[idx+1] + (SEED % 5)) % 256;
                                    data.data[idx+2] = (data.data[idx+2] + (SEED % 3)) % 256;
                                }}
                            }} catch (e) {{}}
                            return data;
                        }};
                    }} catch (e) {{}}
                }})();
            '''
        })
        
        # Set up network headers
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
            "headers": {"Accept-Language": "en-US,en;q=0.9"}
        })

        # Set timezone, locale, and other overrides
        try:
            driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {"timezoneId": "Europe/Berlin"})
            logger.info(f"Profile {profile_idx}: Set timezone to Europe/Berlin")
        except Exception as e:
            logger.warning(f"Profile {profile_idx}: Timezone override failed: {e}")

        try:
            driver.execute_cdp_cmd('Emulation.setLocaleOverride', {"locale": "en-US"})
            logger.info(f"Profile {profile_idx}: Set locale to en-US")
        except Exception as e:
            logger.warning(f"Profile {profile_idx}: Locale override failed: {e}")

        try:
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                "width": window_width,
                "height": window_height,
                "deviceScaleFactor": 1.0,
                "mobile": False,
            })
            logger.info(f"Profile {profile_idx}: Set viewport to {window_width}x{window_height}")
        except Exception as e:
            logger.warning(f"Profile {profile_idx}: Viewport override failed: {e}")

        try:
            driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                "latitude": 52.5200,
                "longitude": 13.4050,
                "accuracy": 10000
            })
            logger.info(f"Profile {profile_idx}: Set geolocation to Berlin")
        except Exception as e:
            logger.warning(f"Profile {profile_idx}: Geolocation override failed: {e}")

        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": PROFILE_CONFIG['user_agent'],
                "platform": "Win32",
            })
            logger.info(f"Profile {profile_idx}: Set user agent")
        except Exception as e:
            logger.warning(f"Profile {profile_idx}: User agent override failed: {e}")
        
        # Navigate to startup URL with human-like behavior
        test_url = PROFILE_CONFIG['startup_urls'][0]
        logger.info(f"Profile {profile_idx}: Navigating to {test_url}")
        
        # Start with a neutral page to warm up
        driver.get("https://example.com")
        time.sleep(random.uniform(2, 4))
        
        # Then go to the target URL
        driver.get(test_url)
        time.sleep(random.uniform(3, 5))
        
        logger.info(f"✅ Profile {profile_idx} launched successfully!")
        return driver, profile_idx
        
    except Exception as e:
        logger.error(f"❌ Error launching profile {profile_idx}: {e}")
        return None, profile_idx

def launch_profile_worker(profile_idx):
    """Launch a single profile in a worker thread"""
    return create_profile_with_enhanced_detection(profile_idx)

def cleanup_profiles():
    """Clean up all test profiles"""
    logger.info("🧹 Cleaning up test profiles...")
    
    for profile_name in PROFILE_NAMES:
        cmd = [
            sys.executable,
            str(MANAGER_PY),
            "delete",
            "--name", profile_name
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
            if result.returncode == 0:
                logger.info(f"✅ Profile {profile_name} cleaned up")
            else:
                logger.warning(f"⚠️ Could not clean up {profile_name}: {result.stderr}")
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up {profile_name}: {e}")

def create_single_profile_ui_mode():
    """Create a single profile for UI mode"""
    if not args.name:
        logger.error("Profile name is required for UI mode")
        return False
    
    profile_name = args.name
    config = PROFILE_CONFIG.copy()
    config["name"] = profile_name
    
    # Parse config from command line if provided
    if args.config:
        try:
            user_config = json.loads(args.config)
            config.update(user_config)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON config: {e}")
            return False
    
    # Check if this is actually an enhanced mode profile
    is_enhanced_mode = config.get('enhanced_mode', False)
    
    # Check if profile already exists and handle conflicts
    profile_path = BULKCREATE_PATH / "selenium_profiles" / profile_name
    enhanced_metadata_path = profile_path / "enhanced_mode.json"
    
    if profile_path.exists():
        # Profile exists, check if it's enhanced or standard
        existing_is_enhanced = enhanced_metadata_path.exists()
        
        if existing_is_enhanced and not is_enhanced_mode:
            # Existing profile is enhanced, trying to create standard with same name
            logger.error(f"❌ Profile '{profile_name}' already exists as ENHANCED profile!")
            logger.error(f"❌ Cannot create standard profile with same name.")
            logger.error(f"❌ Please use a different name for your standard profile.")
            sys.exit(1)  # Exit with error code
        elif not existing_is_enhanced and is_enhanced_mode:
            # Existing profile is standard, trying to create enhanced with same name
            logger.error(f"❌ Profile '{profile_name}' already exists as STANDARD profile!")
            logger.error(f"❌ Cannot create enhanced profile with same name.")
            logger.error(f"❌ Please use a different name for your enhanced profile.")
            sys.exit(1)  # Exit with error code
        elif existing_is_enhanced and is_enhanced_mode:
            # Both are enhanced - this is a duplicate
            logger.error(f"❌ Enhanced profile '{profile_name}' already exists!")
            logger.error(f"❌ Please use a different name.")
            sys.exit(1)  # Exit with error code
        elif not existing_is_enhanced and not is_enhanced_mode:
            # Both are standard - this is a duplicate
            logger.error(f"❌ Standard profile '{profile_name}' already exists!")
            logger.error(f"❌ Please use a different name.")
            sys.exit(1)  # Exit with error code
    
    # Create profile using bulkcreate-main
    cmd = [
        sys.executable,
        str(MANAGER_PY),
        "create",
        "--name", profile_name,
        "--config", json.dumps(config)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BULKCREATE_PATH))
        
        if result.returncode == 0:
            logger.info(f"✅ Profile '{profile_name}' created successfully!")
            
            # Only create enhanced mode metadata file if this is actually an enhanced mode profile
            if is_enhanced_mode:
                profile_metadata_path = BULKCREATE_PATH / "selenium_profiles" / profile_name / "enhanced_mode.json"
                try:
                    profile_metadata_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(profile_metadata_path, 'w') as f:
                        json.dump({"enhancedMode": True}, f)
                    logger.info(f"✅ Enhanced mode metadata created for '{profile_name}'")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create enhanced mode metadata: {e}")
            else:
                logger.info(f"ℹ️ Standard mode profile '{profile_name}' - no enhanced metadata needed")
            
            return True
        else:
            logger.error(f"❌ Failed to create profile: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Error creating profile: {e}")
        return False

def launch_single_profile_ui_mode():
    """Launch a single profile for UI mode"""
    if not args.name:
        logger.error("Profile name is required for UI mode")
        return False
    
    profile_name = args.name
    profile_path = BULKCREATE_PATH / "selenium_profiles" / profile_name
    
    if not profile_path.exists():
        logger.error(f"Profile '{profile_name}' not found. Create it first.")
        return False
    
    # Launch with enhanced anti-detection
    driver, idx = launch_profile_enhanced(profile_name, 1)
    
    if driver:
        logger.info(f"✅ Profile '{profile_name}' launched successfully!")
        
        # Keep the browser open
        try:
            while True:
                time.sleep(1)
                try:
                    current_url = driver.current_url
                except:
                    logger.info("🛑 Browser was closed")
                    break
        except KeyboardInterrupt:
            logger.info("🛑 Closing browser...")
        
        driver.quit()
        return True
    else:
        logger.error(f"❌ Failed to launch profile '{profile_name}'")
        return False

def main():
    """Main function with UI mode support"""
    
    # UI Mode: Single profile operations
    if args.create_only:
        return create_single_profile_ui_mode()
    elif args.launch_only:
        return launch_single_profile_ui_mode()
    
    # Default Mode: Launch 5 profiles
    print("=" * 70)
    print("🚀 LAUNCHING 5 ENHANCED PROFILES")
    print("   Using bulkcreate-main + launch_single_profile.py anti-detection")
    print("=" * 70)
    
    # Check if bulkcreate-main exists
    if not BULKCREATE_PATH.exists():
        print(f"❌ bulkcreate-main directory not found at: {BULKCREATE_PATH}")
        return False
    
    if not MANAGER_PY.exists():
        print(f"❌ manager.py not found at: {MANAGER_PY}")
        return False
    
    print(f"✅ Found bulkcreate-main at: {BULKCREATE_PATH}")
    
    drivers = []
    
    try:
        # Launch 5 profiles in parallel
        logger.info("Launching 5 enhanced profiles in parallel...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all profile launches
            futures = {
                executor.submit(launch_profile_worker, i): i 
                for i in range(1, 6)
            }
            
            # Collect results
            for future in as_completed(futures):
                profile_idx = futures[future]
                result = future.result()
                
                if result and result[0]:  # driver exists
                    drivers.append(result)
                    logger.info(f"Profile {profile_idx} ready!")
                else:
                    logger.error(f"Profile {profile_idx} failed to launch!")
        
        if not drivers:
            logger.error("No profiles launched successfully!")
            return False
        
        logger.info(f"✅ Successfully launched {len(drivers)}/5 enhanced profiles!")
        logger.info("🌐 Browsers are now open and ready for testing")
        logger.info("   - User Agent: Chrome Windows")
        logger.info("   - Language: English (en-US)")
        logger.info("   - Timezone: Europe/Berlin (Germany)")
        logger.info("   - URL: https://httpbin.org/ip")
        logger.info("   - WebRTC: Disabled")
        logger.info("   - Enhanced Anti-Detection: Enabled")
        logger.info("")
        logger.info("🔄 Browsers will stay open for testing...")
        logger.info("   Press Ctrl+C to close all browsers")
        
        # Keep the browsers open
        try:
            while True:
                time.sleep(1)
                # Check if any browser is still alive
                active_drivers = []
                for driver, idx in drivers:
                    try:
                        current_url = driver.current_url
                        active_drivers.append((driver, idx))
                    except:
                        logger.info(f"🛑 Profile {idx} browser was closed")
                
                drivers = active_drivers
                
                if not drivers:
                    logger.info("🛑 All browsers were closed")
                    break
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Closing all browsers...")
        
        # Close all browsers
        logger.info("Closing all browsers...")
        for driver, idx in drivers:
            try:
                driver.quit()
                logger.info(f"✅ Profile {idx} browser closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing profile {idx}: {e}")
        
        logger.info("✅ All browsers closed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error launching profiles: {e}")
        return False
    finally:
        # Always try to clean up
        cleanup_profiles()
    
    return True

if __name__ == "__main__":
    main()
