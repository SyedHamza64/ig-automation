#!/usr/bin/env python3
"""
Modified version to launch 5 profiles with specific settings
and keep the browsers open for testing.
"""

import os
import time
import random
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deterministic_int_from_string(value: str) -> int:
    """Generate deterministic integer from string (from launch_profiles.py)"""
    h = 0
    for ch in value:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h or 1

def create_profile(profile_idx):
    """Create a Chrome profile with your specific settings"""
    
    # Your specific configuration for each profile
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles", f"test_profile_{profile_idx}")
    seed = deterministic_int_from_string(profile_path)  # Use same seed generation as launch_profiles.py
    
    profile_config = {
        "name": f"test_profile_{profile_idx}",
        "path": profile_path,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",  # Chrome Windows
        "languages": ["en-US", "en"],  # English
        "timezone": "Europe/Berlin",  # Germany timezone
        "viewport": {"width": 1920, "height": 1080, "deviceScaleFactor": 1.0},
        "platform": "Win32",
        "hardwareConcurrency": random.choice([4, 6, 8, 12]),  # Random hardware specs like launch_profiles.py
        "deviceMemory": random.choice([4, 8, 16]),  # Random memory specs like launch_profiles.py
        "geo": {"latitude": 52.5200, "longitude": 13.4050, "accuracy": 10000},  # Berlin coordinates
        "seed": seed  # Deterministic seed generation
    }
    
    # Ensure profile directory exists
    os.makedirs(profile_config["path"], exist_ok=True)
    
    chrome_options = Options()
    profile_path = profile_config["path"]
    user_agent = profile_config["userAgent"]
    languages = profile_config["languages"]
    tz = profile_config["timezone"]
    geo = profile_config["geo"]
    viewport = profile_config["viewport"]
    platform = profile_config["platform"]
    hwc = profile_config["hardwareConcurrency"]
    dev_mem = profile_config["deviceMemory"]
    seed = profile_config["seed"]

    # Profile and user agent settings
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument(f"--lang={languages[0]}")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    # Enhanced anti-detection measures (from launch_profiles.py)
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Additional stealth options (from launch_profiles.py)
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
    
    # Enhanced browser preferences (from launch_profiles.py)
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
        "profile.default_content_setting_values.geolocation": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Set up ChromeDriver service - use the ChromeDriver from bulkcreate-main
    chromedriver_path = "E:/work/IG-Automation/bulkcreate-main/bulkcreate-main/chromedriver.exe"
    service = Service(chromedriver_path)
    
    # Create the webdriver instance
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set window size and position with grid layout
    window_width = 800
    window_height = 600
    
    # Calculate position in grid (2x3 grid) with better spacing
    row = (profile_idx - 1) // 3
    col = (profile_idx - 1) % 3
    
    # Better positioning with more spacing and ensure positive coordinates
    x_offset = max(50, col * (window_width + 20) + 50)
    y_offset = max(50, row * (window_height + 20) + 50)
    
    # Set window size first, then position
    driver.set_window_size(window_width, window_height)
    time.sleep(0.5)  # Small delay to ensure size is set
    
    # Set position with fallback
    try:
        driver.set_window_position(x_offset, y_offset)
        time.sleep(0.5)  # Small delay to ensure position is set
    except Exception as e:
        logger.warning(f"Failed to set window position for profile {profile_idx}: {e}")
        # Fallback: just ensure window is visible
        driver.maximize_window()
    
    # Enhanced anti-detection script injection (from launch_profiles.py)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': f'''
            (function() {{
                const SEED = {seed};
                try {{
                    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                    Object.defineProperty(navigator, 'platform', {{ get: () => '{platform}' }});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hwc} }});
                    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {dev_mem} }});
                    Object.defineProperty(navigator, 'languages', {{ get: () => {json.dumps(languages)} }});

                    // Enhanced plugins shape (from launch_profiles.py)
                    const fakePlugins = [{{ name: 'Chrome PDF Plugin' }}, {{ name: 'Chrome PDF Viewer' }}, {{ name: 'Native Client' }}];
                    const pluginsProxy = new Proxy(fakePlugins, {{
                        get(target, prop) {{
                            if (prop === 'length') return target.length;
                            if (!isNaN(prop)) return target[prop];
                            return target[prop];
                        }}
                    }});
                    Object.defineProperty(navigator, 'plugins', {{ get: () => pluginsProxy }});

                    // Enhanced canvas noise for better fingerprint variation
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
                    
                    // Additional WebGL fingerprinting protection
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                            return 'Intel Inc.';
                        }}
                        if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                            return 'Intel(R) Iris(TM) Graphics 6100';
                        }}
                        return getParameter.call(this, parameter);
                    }};
                }} catch (e) {{}}
            }})();
        '''
    })
    
    # Enhanced network headers (from launch_profiles.py)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {"Accept-Language": ",".join(languages)}
    })

    # Enhanced CDP commands with better error handling (from launch_profiles.py)
    try:
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {"timezoneId": tz})
        logger.info(f"Set timezone to: {tz}")
    except Exception as e:
        logger.warning(f"Timezone override failed: {tz}")

    try:
        driver.execute_cdp_cmd('Emulation.setLocaleOverride', {"locale": languages[0]})
        logger.info(f"Set locale to: {languages[0]}")
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            "width": window_width,
            "height": window_height,
            "deviceScaleFactor": viewport.get("deviceScaleFactor", 1.0),
            "mobile": False,
        })
        logger.info(f"Set viewport to: {window_width}x{window_height}")
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "accuracy": geo.get("accuracy", 100)
        })
        logger.info(f"Set geolocation to: {geo['latitude']}, {geo['longitude']}")
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": platform,
        })
        logger.info(f"Set user agent to: {user_agent[:50]}...")
    except Exception:
        pass
    
    logger.info(f"Profile {profile_idx} created with path: {profile_path}")
    return driver, profile_config

def simulate_human_behavior(driver):
    """Simulate human-like behavior (from launch_profiles.py)"""
    driver.execute_script("""
        var x = Math.floor(Math.random() * window.innerWidth);
        var y = Math.floor(Math.random() * window.innerHeight);
        var elem = document.elementFromPoint(x, y);
        elem.scrollIntoView();
    """)
    time.sleep(random.uniform(2, 5))  # Random delay between 2 and 5 seconds

def launch_profile_worker(profile_idx):
    """Launch a single profile in a worker thread"""
    try:
        logger.info(f"Creating profile {profile_idx}...")
        driver, config = create_profile(profile_idx)
        
        # Start with a neutral page to warm up the profile (from launch_profiles.py)
        logger.info(f"Profile {profile_idx}: Warming up with example.com...")
        driver.get("https://example.com")
        time.sleep(random.uniform(2, 4))
        
        # Simulate some browsing behavior
        simulate_human_behavior(driver)
        
        # Navigate to your test URL
        test_url = "https://httpbin.org/ip"
        logger.info(f"Profile {profile_idx}: Navigating to {test_url}")
        driver.get(test_url)
        
        # Wait for page to load with human-like delays
        time.sleep(random.uniform(3, 7))
        simulate_human_behavior(driver)
        
        logger.info(f"✅ Profile {profile_idx} launched successfully!")
        return driver, profile_idx
        
    except Exception as e:
        logger.error(f"❌ Error launching profile {profile_idx}: {e}")
        return None, profile_idx

def main():
    """Main function to launch 5 profiles and keep them open"""
    print("=" * 70)
    print("🚀 LAUNCHING 5 PROFILES")
    print("   Settings: Chrome Windows, English, Germany timezone")
    print("=" * 70)
    
    # Create profile directories
    profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    
    drivers = []
    
    try:
        # Launch 5 profiles in parallel
        logger.info("Launching 5 profiles in parallel...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all profile launches
            futures = {
                executor.submit(launch_profile_worker, i): i 
                for i in range(1, 6)
            }
            
            # Collect results
            for future in as_completed(futures):
                profile_idx = futures[future]
                driver, idx = future.result()
                
                if driver:
                    drivers.append((driver, idx))
                    logger.info(f"Profile {idx} ready!")
                else:
                    logger.error(f"Profile {idx} failed to launch!")
        
        if not drivers:
            logger.error("No profiles launched successfully!")
            return False
        
        logger.info(f"✅ Successfully launched {len(drivers)}/5 profiles!")
        logger.info("🌐 Browsers are now open and ready for testing")
        logger.info("   - User Agent: Chrome Windows")
        logger.info("   - Language: English (en-US)")
        logger.info("   - Timezone: Europe/Berlin (Germany)")
        logger.info("   - URL: https://httpbin.org/ip")
        logger.info("   - WebRTC: Disabled")
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
    
    return True

if __name__ == "__main__":
    main()
