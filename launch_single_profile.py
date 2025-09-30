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

def create_profile(profile_idx):
    """Create a Chrome profile with your specific settings"""
    
    # Your specific configuration for each profile
    profile_config = {
        "name": f"test_profile_{profile_idx}",
        "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles", f"test_profile_{profile_idx}"),
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",  # Chrome Windows
        "languages": ["en-US", "en"],  # English
        "timezone": "Europe/Berlin",  # Germany timezone
        "viewport": {"width": 1920, "height": 1080, "deviceScaleFactor": 1.0},
        "platform": "Win32",
        "hardwareConcurrency": 8,
        "deviceMemory": 8,
        "geo": {"latitude": 52.5200, "longitude": 13.4050, "accuracy": 10000},  # Berlin coordinates
        "seed": 12345 + profile_idx  # Unique seed for each profile
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
    
    # Anti-detection measures
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Set up ChromeDriver service - use the ChromeDriver from bulkcreate-main
    chromedriver_path = "E:/work/IG-Automation/bulkcreate-main/bulkcreate-main/chromedriver.exe"
    service = Service(chromedriver_path)
    
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
    
    # Anti-detection script injection
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
        "headers": {"Accept-Language": ",".join(languages)}
    })

    # Set timezone, locale, and other overrides
    try:
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {"timezoneId": tz})
        logger.info(f"Set timezone to: {tz}")
    except Exception as e:
        logger.warning(f"Timezone override failed: {e}")

    try:
        driver.execute_cdp_cmd('Emulation.setLocaleOverride', {"locale": languages[0]})
        logger.info(f"Set locale to: {languages[0]}")
    except Exception as e:
        logger.warning(f"Locale override failed: {e}")

    try:
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            "width": viewport["width"],
            "height": viewport["height"],
            "deviceScaleFactor": viewport["deviceScaleFactor"],
            "mobile": False,
        })
        logger.info(f"Set viewport to: {viewport['width']}x{viewport['height']}")
    except Exception as e:
        logger.warning(f"Viewport override failed: {e}")

    try:
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "accuracy": geo["accuracy"]
        })
        logger.info(f"Set geolocation to: {geo['latitude']}, {geo['longitude']}")
    except Exception as e:
        logger.warning(f"Geolocation override failed: {e}")

    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": platform,
        })
        logger.info(f"Set user agent to: {user_agent[:50]}...")
    except Exception as e:
        logger.warning(f"User agent override failed: {e}")
    
    logger.info(f"Profile {profile_idx} created with path: {profile_path}")
    return driver, profile_config

def launch_profile_worker(profile_idx):
    """Launch a single profile in a worker thread"""
    try:
        logger.info(f"Creating profile {profile_idx}...")
        driver, config = create_profile(profile_idx)
        
        # Navigate to your test URL
        test_url = "https://httpbin.org/ip"
        logger.info(f"Profile {profile_idx}: Navigating to {test_url}")
        driver.get(test_url)
        
        # Wait for page to load
        time.sleep(random.uniform(2, 4))
        
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