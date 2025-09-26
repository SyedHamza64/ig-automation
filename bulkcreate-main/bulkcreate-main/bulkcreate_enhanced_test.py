#!/usr/bin/env python3
"""
Enhanced backend script that combines bulkcreate-main manager.py with 
advanced anti-detection measures and configurable feature toggles.
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
import hashlib
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

# Phase 1 Anti-Detection Features Configuration
class AntiDetectionFeatures:
    """Configuration class for all anti-detection features"""
    
    def __init__(self, config_dict=None):
        # Default toggles - all disabled by default (current behavior)
        self.dynamic_user_agent = False
        self.enhanced_canvas_fingerprinting = False
        self.realistic_device_metrics = False
        self.hardware_randomization = False
        self.advanced_navigator_properties = False
        
        # Load from config if provided
        if config_dict:
            self.load_from_config(config_dict)
    
    def load_from_config(self, config_dict):
        """Load feature toggles from configuration"""
        anti_detection_config = config_dict.get('anti_detection', {})
        
        self.dynamic_user_agent = anti_detection_config.get('dynamic_user_agent', False)
        self.enhanced_canvas_fingerprinting = anti_detection_config.get('enhanced_canvas_fingerprinting', False)
        self.realistic_device_metrics = anti_detection_config.get('realistic_device_metrics', False)
        self.hardware_randomization = anti_detection_config.get('hardware_randomization', False)
        self.advanced_navigator_properties = anti_detection_config.get('advanced_navigator_properties', False)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'dynamic_user_agent': self.dynamic_user_agent,
            'enhanced_canvas_fingerprinting': self.enhanced_canvas_fingerprinting,
            'realistic_device_metrics': self.realistic_device_metrics,
            'hardware_randomization': self.hardware_randomization,
            'advanced_navigator_properties': self.advanced_navigator_properties
        }

# User Agent Generator
class UserAgentGenerator:
    """Generate realistic user agents based on device type and settings"""
    
    CHROME_VERSIONS = [
        "126.0.0.0", "125.0.0.0", "124.0.0.0", "123.0.0.0", "122.0.0.0"
    ]
    
    FIREFOX_VERSIONS = [
        "126.0", "125.0", "124.0", "123.0", "122.0"
    ]
    
    SAFARI_VERSIONS = [
        "17.0", "16.6", "16.5", "16.4", "16.3"
    ]
    
    @staticmethod
    def generate_chrome_windows(seed=None):
        """Generate Chrome Windows user agent"""
        if seed:
            random.seed(seed)
        
        version = random.choice(UserAgentGenerator.CHROME_VERSIONS)
        webkit_version = f"{int(version.split('.')[0]) + 100}.0.0.0"
        
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{version} Safari/{webkit_version.split('.')[0]}"
    
    @staticmethod
    def generate_chrome_macos(seed=None):
        """Generate Chrome macOS user agent"""
        if seed:
            random.seed(seed)
        
        version = random.choice(UserAgentGenerator.CHROME_VERSIONS)
        webkit_version = f"{int(version.split('.')[0]) + 100}.0.0.0"
        mac_version = random.choice(["14.0", "13.0", "12.0"])
        
        return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version.replace('.', '_')}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{version} Safari/{webkit_version.split('.')[0]}"
    
    @staticmethod
    def generate_chrome_linux(seed=None):
        """Generate Chrome Linux user agent"""
        if seed:
            random.seed(seed)
        
        version = random.choice(UserAgentGenerator.CHROME_VERSIONS)
        webkit_version = f"{int(version.split('.')[0]) + 100}.0.0.0"
        
        return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{version} Safari/{webkit_version.split('.')[0]}"
    
    @staticmethod
    def generate_firefox_windows(seed=None):
        """Generate Firefox Windows user agent"""
        if seed:
            random.seed(seed)
        
        version = random.choice(UserAgentGenerator.FIREFOX_VERSIONS)
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}"
    
    @staticmethod
    def generate_safari_macos(seed=None):
        """Generate Safari macOS user agent"""
        if seed:
            random.seed(seed)
        
        version = random.choice(UserAgentGenerator.SAFARI_VERSIONS)
        mac_version = random.choice(["14.0", "13.0", "12.0"])
        
        return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version.replace('.', '_')}) AppleWebKit/{version} (KHTML, like Gecko) Version/{version} Safari/{version}"

# Device Metrics Generator
class DeviceMetricsGenerator:
    """Generate realistic device metrics and hardware specifications"""
    
    DESKTOP_RESOLUTIONS = [
        {"width": 1920, "height": 1080, "scale": 1.0},
        {"width": 2560, "height": 1440, "scale": 1.0},
        {"width": 3840, "height": 2160, "scale": 1.0},
        {"width": 1366, "height": 768, "scale": 1.0},
        {"width": 1536, "height": 864, "scale": 1.0},
        {"width": 1440, "height": 900, "scale": 1.0},
        {"width": 1680, "height": 1050, "scale": 1.0},
        {"width": 1280, "height": 720, "scale": 1.0}
    ]
    
    LAPTOP_RESOLUTIONS = [
        {"width": 1366, "height": 768, "scale": 1.0},
        {"width": 1920, "height": 1080, "scale": 1.0},
        {"width": 2560, "height": 1440, "scale": 1.25},
        {"width": 2880, "height": 1800, "scale": 1.5},
        {"width": 1440, "height": 900, "scale": 1.0},
        {"width": 1680, "height": 1050, "scale": 1.0}
    ]
    
    MOBILE_RESOLUTIONS = [
        {"width": 375, "height": 667, "scale": 2.0},
        {"width": 414, "height": 896, "scale": 2.0},
        {"width": 375, "height": 812, "scale": 3.0},
        {"width": 414, "height": 736, "scale": 2.0},
        {"width": 360, "height": 640, "scale": 2.0},
        {"width": 393, "height": 851, "scale": 2.75}
    ]
    
    HARDWARE_CONFIGS = {
        "desktop": [
            {"cores": 8, "memory": 16, "platform": "Win32"},
            {"cores": 12, "memory": 32, "platform": "Win32"},
            {"cores": 16, "memory": 64, "platform": "Win32"},
            {"cores": 6, "memory": 8, "platform": "Win32"},
            {"cores": 4, "memory": 8, "platform": "Win32"}
        ],
        "laptop": [
            {"cores": 4, "memory": 8, "platform": "Win32"},
            {"cores": 8, "memory": 16, "platform": "Win32"},
            {"cores": 6, "memory": 12, "platform": "Win32"},
            {"cores": 2, "memory": 4, "platform": "Win32"}
        ],
        "mobile": [
            {"cores": 4, "memory": 4, "platform": "Linux armv7l"},
            {"cores": 6, "memory": 6, "platform": "Linux armv7l"},
            {"cores": 8, "memory": 8, "platform": "Linux armv7l"},
            {"cores": 2, "memory": 3, "platform": "Linux armv7l"}
        ]
    }
    
    @staticmethod
    def generate_device_metrics(device_type="desktop", seed=None):
        """Generate realistic device metrics"""
        if seed:
            random.seed(seed)
        
        if device_type == "desktop":
            resolution = random.choice(DeviceMetricsGenerator.DESKTOP_RESOLUTIONS)
            hardware = random.choice(DeviceMetricsGenerator.HARDWARE_CONFIGS["desktop"])
        elif device_type == "laptop":
            resolution = random.choice(DeviceMetricsGenerator.LAPTOP_RESOLUTIONS)
            hardware = random.choice(DeviceMetricsGenerator.HARDWARE_CONFIGS["laptop"])
        elif device_type == "mobile":
            resolution = random.choice(DeviceMetricsGenerator.MOBILE_RESOLUTIONS)
            hardware = random.choice(DeviceMetricsGenerator.HARDWARE_CONFIGS["mobile"])
        else:
            resolution = random.choice(DeviceMetricsGenerator.DESKTOP_RESOLUTIONS)
            hardware = random.choice(DeviceMetricsGenerator.HARDWARE_CONFIGS["desktop"])
        
        return {
            "width": resolution["width"],
            "height": resolution["height"],
            "deviceScaleFactor": resolution["scale"],
            "hardwareConcurrency": hardware["cores"],
            "deviceMemory": hardware["memory"],
            "platform": hardware["platform"]
        }

# Enhanced Canvas Fingerprinting
class CanvasFingerprintGenerator:
    """Generate advanced canvas fingerprinting variations"""
    
    @staticmethod
    def generate_canvas_noise_script(seed, features):
        """Generate advanced canvas noise script"""
        if not features.enhanced_canvas_fingerprinting:
            # Basic canvas noise (current behavior)
            return f'''
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function() {{
                    const data = origGetImageData.apply(this, arguments);
                    try {{
                        const idx = ({seed} % 100) * 4;
                        if (data && data.data && data.data.length > idx + 3) {{
                            data.data[idx] = (data.data[idx] + ({seed} % 7)) % 256;
                            data.data[idx+1] = (data.data[idx+1] + ({seed} % 5)) % 256;
                            data.data[idx+2] = (data.data[idx+2] + ({seed} % 3)) % 256;
                        }}
                    }} catch (e) {{}}
                    return data;
                }};
            '''
        else:
            # Advanced canvas fingerprinting
            return f'''
                const SEED = {seed};
                const NOISE_FACTOR = 0.1 + (SEED % 10) * 0.05;
                
                // Advanced canvas noise
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function() {{
                    const data = origGetImageData.apply(this, arguments);
                    if (!data || !data.data) return data;
                    
                    try {{
                        const pixels = data.data;
                        const noisePoints = Math.floor(pixels.length * NOISE_FACTOR);
                        
                        for (let i = 0; i < noisePoints; i++) {{
                            const idx = (SEED + i * 7) % pixels.length;
                            const channel = idx % 4;
                            const noise = (SEED + i) % 11 - 5;
                            
                            if (channel < 3) {{ // RGB channels only
                                pixels[idx] = Math.max(0, Math.min(255, pixels[idx] + noise));
                            }}
                        }}
                    }} catch (e) {{}}
                    return data;
                }};
                
                // WebGL noise
                if (window.WebGLRenderingContext) {{
                    const origGetParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        const result = origGetParameter.apply(this, arguments);
                        
                        if (parameter === this.RENDERER || parameter === this.VENDOR) {{
                            return result + String.fromCharCode(65 + (SEED % 26));
                        }}
                        return result;
                    }};
                }}
                
                // Font rendering variations
                const origFillText = CanvasRenderingContext2D.prototype.fillText;
                CanvasRenderingContext2D.prototype.fillText = function() {{
                    const originalFont = this.font;
                    this.font = originalFont + ` {{letterSpacing: {(SEED % 3) - 1}px}}`;
                    const result = origFillText.apply(this, arguments);
                    this.font = originalFont;
                    return result;
                }};
            '''

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

def launch_profile_enhanced(profile_name, profile_idx, config=None):
    """Launch profile with enhanced anti-detection measures"""
    
    # Get profile path from bulkcreate-main
    profile_path = BULKCREATE_PATH / "selenium_profiles" / profile_name
    
    # Initialize anti-detection features
    features = AntiDetectionFeatures(config)
    
    # Generate unique seed for this profile
    profile_seed = int(hashlib.md5(f"{profile_name}_{profile_idx}".encode()).hexdigest()[:8], 16)
    
    chrome_options = Options()
    
    # Profile and user agent settings
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # Dynamic User Agent Generation
    if features.dynamic_user_agent:
        # Determine device type from config
        device_type = config.get('deviceType', 'windows') if config else 'windows'
        
        if device_type == 'windows':
            user_agent = UserAgentGenerator.generate_chrome_windows(profile_seed)
        elif device_type == 'macos':
            user_agent = UserAgentGenerator.generate_chrome_macos(profile_seed)
        elif device_type == 'linux':
            user_agent = UserAgentGenerator.generate_chrome_linux(profile_seed)
        else:
            user_agent = UserAgentGenerator.generate_chrome_windows(profile_seed)
        
        logger.info(f"Profile {profile_idx}: Using dynamic user agent")
    else:
        user_agent = PROFILE_CONFIG['user_agent']
        logger.info(f"Profile {profile_idx}: Using static user agent")
    
    chrome_options.add_argument(f"--user-agent={user_agent}")
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
        
        # Device Metrics Generation
        if features.realistic_device_metrics:
            device_type = config.get('deviceType', 'desktop') if config else 'desktop'
            device_metrics = DeviceMetricsGenerator.generate_device_metrics(device_type, profile_seed)
            window_width = device_metrics["width"]
            window_height = device_metrics["height"]
            logger.info(f"Profile {profile_idx}: Using realistic device metrics {window_width}x{window_height}")
        else:
            window_width = 800
            window_height = 600
            logger.info(f"Profile {profile_idx}: Using default window size")
        
        # Calculate position in grid (2x3 grid)
        row = (profile_idx - 1) // 3
        col = (profile_idx - 1) % 3
        
        x_offset = col * window_width + 50
        y_offset = row * window_height + 50
        
        driver.set_window_size(window_width, window_height)
        driver.set_window_position(x_offset, y_offset)
        
        # Enhanced anti-detection script injection with configurable features
        seed = profile_seed
        
        # Generate hardware specs
        if features.hardware_randomization:
            device_type = config.get('deviceType', 'desktop') if config else 'desktop'
            device_metrics = DeviceMetricsGenerator.generate_device_metrics(device_type, profile_seed)
            hardware_concurrency = device_metrics["hardwareConcurrency"]
            device_memory = device_metrics["deviceMemory"]
            platform = device_metrics["platform"]
        else:
            hardware_concurrency = 8
            device_memory = 8
            platform = "Win32"
        
        # Generate canvas noise script
        canvas_script = CanvasFingerprintGenerator.generate_canvas_noise_script(seed, features)
        
        # Build the complete anti-detection script
        anti_detection_script = f'''
            (function() {{
                const SEED = {seed};
                try {{
                    // Basic navigator overrides
                    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                    Object.defineProperty(navigator, 'platform', {{ get: () => '{platform}' }});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hardware_concurrency} }});
                    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
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

                    // Canvas fingerprinting
                    {canvas_script}
                    
                    // Advanced Navigator Properties
                    {f'''
                    if (true) {{ // features.advanced_navigator_properties
                        // Connection simulation
                        Object.defineProperty(navigator, 'connection', {{
                            get: () => ({{
                                effectiveType: '4g',
                                rtt: 50 + (SEED % 100),
                                downlink: 10 + (SEED % 5),
                                saveData: false
                            }})
                        }});
                        
                        // Battery API simulation
                        if (navigator.getBattery) {{
                            const originalGetBattery = navigator.getBattery;
                            navigator.getBattery = function() {{
                                return Promise.resolve({{
                                    charging: true,
                                    chargingTime: 0,
                                    dischargingTime: Infinity,
                                    level: 0.8 + (SEED % 20) / 100
                                }});
                            }};
                        }}
                        
                        // Media devices simulation
                        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                            const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                            navigator.mediaDevices.enumerateDevices = function() {{
                                return Promise.resolve([
                                    {{ deviceId: 'default', groupId: 'group1', kind: 'audioinput', label: 'Default - Microphone' }},
                                    {{ deviceId: 'default', groupId: 'group1', kind: 'audiooutput', label: 'Default - Speaker' }},
                                    {{ deviceId: 'default', groupId: 'group1', kind: 'videoinput', label: 'Default - Camera' }}
                                ]);
                            }};
                        }}
                        
                        // Permissions API simulation
                        if (navigator.permissions && navigator.permissions.query) {{
                            const originalQuery = navigator.permissions.query;
                            navigator.permissions.query = function(permission) {{
                                return Promise.resolve({{ state: 'granted' }});
                            }};
                        }}
                        
                        // Screen properties
                        Object.defineProperty(screen, 'availHeight', {{ get: () => {window_height - 40} }});
                        Object.defineProperty(screen, 'availWidth', {{ get: () => {window_width} }});
                        Object.defineProperty(screen, 'colorDepth', {{ get: () => 24 }});
                        Object.defineProperty(screen, 'pixelDepth', {{ get: () => 24 }});
                    }}
                    ''' if features.advanced_navigator_properties else ''}
                    
                }} catch (e) {{ console.log('Anti-detection script error:', e); }}
            }})();
        '''
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': anti_detection_script
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
            if features.realistic_device_metrics:
                device_scale_factor = device_metrics["deviceScaleFactor"]
                logger.info(f"Profile {profile_idx}: Using realistic device scale factor {device_scale_factor}")
            else:
                device_scale_factor = 1.0
                logger.info(f"Profile {profile_idx}: Using default device scale factor")
                
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                "width": window_width,
                "height": window_height,
                "deviceScaleFactor": device_scale_factor,
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
    
    # Log anti-detection features if enabled
    if is_enhanced_mode:
        features = AntiDetectionFeatures(config)
        enabled_features = []
        if features.dynamic_user_agent:
            enabled_features.append("Dynamic User Agent")
        if features.enhanced_canvas_fingerprinting:
            enabled_features.append("Enhanced Canvas Fingerprinting")
        if features.realistic_device_metrics:
            enabled_features.append("Realistic Device Metrics")
        if features.hardware_randomization:
            enabled_features.append("Hardware Randomization")
        if features.advanced_navigator_properties:
            enabled_features.append("Advanced Navigator Properties")
        
        if enabled_features:
            logger.info(f"Enhanced profile '{profile_name}' with features: {', '.join(enabled_features)}")
        else:
            logger.info(f"Enhanced profile '{profile_name}' with basic anti-detection only")
    
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
                    
                    # Create metadata with enhanced mode and anti-detection features
                    anti_detection_config = config.get('anti_detection', {})
                    metadata = {
                        "enhancedMode": True,
                        "anti_detection": anti_detection_config
                    }
                    
                    with open(profile_metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    logger.info(f"✅ Enhanced mode metadata created for '{profile_name}' with anti-detection features")
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
    
    # Load config if provided
    config = None
    if args.config:
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON config: {e}")
            return False
    
    # Launch with enhanced anti-detection
    driver, idx = launch_profile_enhanced(profile_name, 1, config)
    
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
