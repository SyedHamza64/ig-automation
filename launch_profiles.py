import os
import time
import random
import json
import glob
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_document_ready(driver, timeout_seconds=10):
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            state = driver.execute_script('return document.readyState')
            if state == 'complete':
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False

# Helper function for simulating random mouse movement and delay
def simulate_human_behavior(driver):
    driver.execute_script("""
        var x = Math.floor(Math.random() * window.innerWidth);
        var y = Math.floor(Math.random() * window.innerHeight);
        var elem = document.elementFromPoint(x, y);
        elem.scrollIntoView();
    """)
    time.sleep(random.uniform(2, 5))  # Random delay between 2 and 5 seconds

def _default_user_agents():
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]

def _default_locale_presets():
    return [
        {"languages": ["en-US", "en"], "timezone": "America/New_York", "geo": {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 10000}},
        {"languages": ["en-GB", "en"], "timezone": "Europe/London", "geo": {"latitude": 51.5074, "longitude": -0.1278, "accuracy": 10000}},
        {"languages": ["fr-FR", "fr", "en"], "timezone": "Europe/Paris", "geo": {"latitude": 48.8566, "longitude": 2.3522, "accuracy": 10000}},
        {"languages": ["de-DE", "de", "en"], "timezone": "Europe/Berlin", "geo": {"latitude": 52.5200, "longitude": 13.4050, "accuracy": 10000}},
        {"languages": ["en-IN", "en"], "timezone": "Asia/Kolkata", "geo": {"latitude": 19.0760, "longitude": 72.8777, "accuracy": 10000}},
    ]

def load_presets():
    """Load UA list and locale presets from JSON or env, with sane defaults.

    Sources (by priority):
    1) Combined JSON at profiles/presets.json (override with PRESETS_PATH)
    2) Separate JSON via UA_LIST_PATH and LOCALE_PRESETS_PATH
    3) Env UA_LIST (comma-separated)
    4) Built-in defaults
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(base_dir, "profiles")

    # Defaults
    user_agents = _default_user_agents()
    locale_presets = _default_locale_presets()

    # 1) Combined presets file
    combined_path = os.environ.get("PRESETS_PATH", os.path.join(profiles_dir, "presets.json"))
    if os.path.isfile(combined_path):
        try:
            with open(combined_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if isinstance(data.get("userAgents"), list) and data.get("userAgents"):
                    user_agents = data["userAgents"]
                if isinstance(data.get("localePresets"), list) and data.get("localePresets"):
                    locale_presets = data["localePresets"]
        except Exception as e:
            logger.warning(f"Failed to load combined presets at {combined_path}: {e}")

    # 2) Separate files
    ua_list_path = os.environ.get("UA_LIST_PATH")
    if ua_list_path and os.path.isfile(ua_list_path):
        try:
            with open(ua_list_path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            if isinstance(arr, list) and arr:
                user_agents = arr
        except Exception as e:
            logger.warning(f"Failed to load UA list at {ua_list_path}: {e}")

    locale_path = os.environ.get("LOCALE_PRESETS_PATH")
    if locale_path and os.path.isfile(locale_path):
        try:
            with open(locale_path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            if isinstance(arr, list) and arr:
                locale_presets = arr
        except Exception as e:
            logger.warning(f"Failed to load locale presets at {locale_path}: {e}")

    # 3) Env UA_LIST (comma separated)
    ua_env = os.environ.get("UA_LIST")
    if ua_env:
        parts = [p.strip() for p in ua_env.split(",") if p.strip()]
        if parts:
            user_agents = parts

    return user_agents, locale_presets

# Load dynamic presets (with fallbacks)
DEFAULT_USER_AGENTS, LOCALE_PRESETS = load_presets()

def deterministic_int_from_string(value: str) -> int:
    h = 0
    for ch in value:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h or 1

def load_profile_configs() -> list:
    """Load profile configs from JSON if present, else auto-generate from folders.

    - Set PROFILE_CONFIG_PATH to use a custom JSON path.
    - Set NUM_PROFILES to cap how many profiles to launch.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(base_dir, "profiles")
    config_path = os.environ.get("PROFILE_CONFIG_PATH", os.path.join(profiles_dir, "config.json"))
    num_cap_env = os.environ.get("NUM_PROFILES", "").strip()
    num_cap = int(num_cap_env) if num_cap_env.isdigit() else None

    # 1) JSON-driven configuration
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("config.json must be a list of profile configs")
            configs = []
            for idx, c in enumerate(data, start=1):
                path = c.get("path") or os.path.join(profiles_dir, f"profile{idx}")
                seed = c.get("seed") or deterministic_int_from_string(path)
                ua = c.get("userAgent") or random.choice(DEFAULT_USER_AGENTS)
                languages = c.get("languages") or ["en-US", "en"]
                timezone = c.get("timezone") or "America/New_York"
                geo = c.get("geo") or {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 10000}
                viewport = c.get("viewport") or {"width": 1536, "height": 960, "deviceScaleFactor": 1.0}
                platform = c.get("platform") or "Win32"
                hwc = c.get("hardwareConcurrency") or random.choice([4, 6, 8, 12])
                devmem = c.get("deviceMemory") or random.choice([4, 8, 16])
                configs.append({
                    "path": path,
                    "userAgent": ua,
                    "languages": languages,
                    "timezone": timezone,
                    "geo": geo,
                    "viewport": viewport,
                    "platform": platform,
                "hardwareConcurrency": hwc,
                "deviceMemory": devmem,
                "seed": seed,
                })
            if num_cap:
                configs = configs[:num_cap]
            return configs
        except Exception as e:
            logger.warning(f"Failed to load profile config JSON at {config_path}: {e}")

    # 2) Auto-generate from existing profile folders
    paths = sorted([p for p in glob.glob(os.path.join(profiles_dir, "profile*")) if os.path.isdir(p)])
    if num_cap:
        paths = paths[:num_cap]

    if not paths:
        logger.warning(f"No profiles found under {profiles_dir}. Create folders like 'profile1', 'profile2', ... or provide a config.json.")

    configs = []
    for i, path in enumerate(paths):
        seed = deterministic_int_from_string(path)
        preset = LOCALE_PRESETS[i % len(LOCALE_PRESETS)]
        ua = DEFAULT_USER_AGENTS[i % len(DEFAULT_USER_AGENTS)]
        viewport = [
            {"width": 1366, "height": 768, "deviceScaleFactor": 1.0},
            {"width": 1536, "height": 864, "deviceScaleFactor": 1.0},
            {"width": 1600, "height": 900, "deviceScaleFactor": 1.0},
            {"width": 1920, "height": 1080, "deviceScaleFactor": 1.0},
            {"width": 1440, "height": 900, "deviceScaleFactor": 1.25},
        ][i % 5]
        configs.append({
            "path": path,
            "userAgent": ua,
            "languages": preset["languages"],
            "timezone": preset["timezone"],
            "geo": preset["geo"],
            "viewport": viewport,
            "platform": "Win32",
            "hardwareConcurrency": random.choice([4, 6, 8, 12]),
            "deviceMemory": random.choice([4, 8, 16]),
            "seed": seed,
        })
    return configs

# Setup for Selenium WebDriver with Proxy and Anti-Detection Measures
def create_chrome_profile(config):
    chrome_options = Options()
    profile_path = config["path"]
    user_agent = config["userAgent"]
    languages = config["languages"]
    tz = config["timezone"]
    geo = config["geo"]
    viewport = config["viewport"]
    platform = config["platform"]
    hwc = config["hardwareConcurrency"]
    dev_mem = config["deviceMemory"]
    seed = int(config.get("seed", random.randint(1000, 9999)))

    chrome_options.add_argument(f"--user-data-dir={profile_path}")  # Set unique profile folder
    chrome_options.add_argument("--profile-directory=Default")  # Use the default profile folder
    chrome_options.add_argument(f"user-agent={user_agent}")  # Set unique user-agent
    chrome_options.add_argument("--no-sandbox")  # Avoid sandboxing issues in some environments
    chrome_options.add_argument("--disable-infobars")  # Hide automation infobar
    chrome_options.add_argument(f"--lang={languages[0]}")  # Match UI language
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--log-level=3")  # Set log level to 3 (suppress warnings)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # Disable automation banner and devtools logging
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation-controlled flag
    chrome_options.add_experimental_option("useAutomationExtension", False)  # Disable automation extension
    
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
    
    
    # Set up the ChromeDriver service - use the ChromeDriver from bulkcreate-main
    chromedriver_path = "E:/work/IG-Automation/bulkcreate-main/bulkcreate-main/chromedriver.exe"
    service = Service(chromedriver_path)
    
    # Create the webdriver instance
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Calculate grid layout based on screen size
    profile_index = int(os.path.basename(profile_path).replace('profile', '')) if 'profile' in os.path.basename(profile_path) else 1
    
    # Get screen dimensions (try to detect, fallback to 1920x1080)
    try:
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        screen_width = 1920
        screen_height = 1080
    
    # Calculate optimal grid layout
    total_profiles = len(profile_configs)
    cols = min(5, total_profiles)  # Max 5 columns
    rows = (total_profiles + cols - 1) // cols  # Ceiling division
    
    # Calculate window size to fit screen
    window_width = screen_width // cols
    window_height = screen_height // rows
    
    # Calculate position in grid
    row = (profile_index - 1) // cols
    col = (profile_index - 1) % cols
    
    x_offset = col * window_width
    y_offset = row * window_height
    
    # Log grid layout info for first profile only
    if profile_index == 1:
        logger.info(f"Grid layout: {cols}x{rows} grid, window size: {window_width}x{window_height}, screen: {screen_width}x{screen_height}")
    
    driver.set_window_size(window_width, window_height)
    driver.set_window_position(x_offset, y_offset)
    
    # Subtle, deterministic per-profile noise and property fixes
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

                    // Plugins shape (length > 0)
                    const fakePlugins = [{{ name: 'Chrome PDF Plugin' }}, {{ name: 'Chrome PDF Viewer' }}, {{ name: 'Native Client' }}];
                    const pluginsProxy = new Proxy(fakePlugins, {{
                        get(target, prop) {{
                            if (prop === 'length') return target.length;
                            if (!isNaN(prop)) return target[prop];
                            return target[prop];
                        }}
                    }});
                    Object.defineProperty(navigator, 'plugins', {{ get: () => pluginsProxy }});

                    // Canvas noise: tweak a deterministic byte in getImageData
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
    
    # Extra Step: Adding custom HTTP headers (accept-language) to simulate real requests
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {"Accept-Language": ",".join(languages)}
    })

    # Coherent overrides: timezone, locale, device metrics, geolocation, user agent
    try:
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {"timezoneId": tz})
    except Exception:
        logger.warning(f"Timezone override not supported or failed: {tz}")

    try:
        driver.execute_cdp_cmd('Emulation.setLocaleOverride', {"locale": languages[0]})
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            "width": window_width,
            "height": window_height,
            "deviceScaleFactor": viewport.get("deviceScaleFactor", 1.0),
            "mobile": False,
        })
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "accuracy": geo.get("accuracy", 100)
        })
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": platform,
        })
    except Exception:
        pass
    
    # Log the details of the profile
    logger.info(f"Profile created with path: {profile_path}, User-Agent: {user_agent}")

    return driver

def collect_fingerprint(driver):
    script = '''
        return (() => {
            const getCanvasHash = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = 200; canvas.height = 50;
                    ctx.textBaseline = 'top';
                    ctx.font = '14px Arial';
                    ctx.fillStyle = '#f60';
                    ctx.fillRect(0, 0, 200, 50);
                    ctx.fillStyle = '#069';
                    ctx.fillText('fingerprint-test', 2, 2);
                    const data = canvas.toDataURL();
                    let hash = 0; for (let i=0; i<data.length; i++) { hash = ((hash<<5)-hash) + data.charCodeAt(i); hash |= 0; }
                    return hash.toString();
                } catch(e) { return 'na'; }
            };
            const getWebGLInfo = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return { vendor: 'na', renderer: 'na' };
                    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                    const vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
                    const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
                    return { vendor, renderer };
                } catch (e) { return { vendor: 'na', renderer: 'na' }; }
            };
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const gl = getWebGLInfo();
            const obj = {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                webdriver: navigator.webdriver,
                screen: { width: screen.width, height: screen.height, pixelRatio: window.devicePixelRatio },
                timezone: tz,
                pluginsLength: (navigator.plugins && navigator.plugins.length) || 0,
                canvasHash: getCanvasHash(),
                webglVendor: gl.vendor,
                webglRenderer: gl.renderer,
            };
            return JSON.stringify(obj);
        })();
    '''
    try:
        txt = driver.execute_script(script)
        return json.loads(txt) if isinstance(txt, str) else txt
    except Exception as e:
        logger.warning(f"collect_fingerprint failed: {e}")
        return None

def test_google_search(driver, profile_idx, search_query="test search"):
    """Test Google search and detect CAPTCHA issues"""
    logger.info(f"Testing Google search for profile {profile_idx}...")
    
    results = {
        "profile_idx": profile_idx,
        "success": False,
        "captcha_detected": False,
        "final_url": "",
        "error": None,
        "response_time": 0,
        "timestamp": time.time()
    }
    
    try:
        start_time = time.time()
        
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(random.uniform(2, 4))  # Human-like delay
        
        # Check if we hit CAPTCHA immediately
        current_url = driver.current_url
        if "sorry" in current_url or "captcha" in current_url.lower():
            results["captcha_detected"] = True
            results["final_url"] = current_url
            results["response_time"] = time.time() - start_time
            logger.warning(f"Profile {profile_idx}: CAPTCHA detected on initial Google load")
            return results
        
        # Find search box and perform search
        try:
            search_box = driver.find_element("name", "q")
            search_box.clear()
            
            # Type search query with human-like delays
            for char in search_query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.5))
            search_box.submit()
            
        except Exception as e:
            logger.error(f"Profile {profile_idx}: Failed to find search box: {e}")
            results["error"] = f"Search box not found: {e}"
            return results
        
        # Wait for results
        time.sleep(random.uniform(3, 5))
        
        # Check final URL
        final_url = driver.current_url
        results["final_url"] = final_url
        results["response_time"] = time.time() - start_time
        
        # Analyze results
        if "sorry" in final_url:
            results["captcha_detected"] = True
            logger.warning(f"Profile {profile_idx}: CAPTCHA detected after search - {final_url}")
        elif "search" in final_url and "q=" in final_url:
            results["success"] = True
            logger.info(f"Profile {profile_idx}: Search successful - {final_url}")
        else:
            logger.warning(f"Profile {profile_idx}: Unexpected result - {final_url}")
        
        return results
        
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Profile {profile_idx}: Search test failed: {e}")
        return results

def diagnose_profile_issues(profile_managers, search_query="test search"):
    """Test all profiles and diagnose Google CAPTCHA issues"""
    logger.info("🔍 Starting Google search test for all profiles...")
    
    test_results = []
    successful_profiles = []
    captcha_profiles = []
    failed_profiles = []
    
    for pm in profile_managers:
        if pm.driver and pm.status == "ready":
            result = test_google_search(pm.driver, pm.idx, search_query)
            test_results.append(result)
            
            if result["success"]:
                successful_profiles.append(pm.idx)
            elif result["captcha_detected"]:
                captcha_profiles.append(pm.idx)
            else:
                failed_profiles.append(pm.idx)
            
            # Add delay between tests to avoid rate limiting
            time.sleep(random.uniform(5, 10))
    
    # Generate diagnostic report
    logger.info("📊 DIAGNOSTIC REPORT")
    logger.info("=" * 50)
    logger.info(f"✅ Successful profiles: {len(successful_profiles)} - {successful_profiles}")
    logger.info(f"🚫 CAPTCHA profiles: {len(captcha_profiles)} - {captcha_profiles}")
    logger.info(f"❌ Failed profiles: {len(failed_profiles)} - {failed_profiles}")
    logger.info("")
    
    # Detailed analysis
    for result in test_results:
        logger.info(f"Profile {result['profile_idx']}:")
        logger.info(f"  Status: {'✅ Success' if result['success'] else '🚫 CAPTCHA' if result['captcha_detected'] else '❌ Failed'}")
        logger.info(f"  Response time: {result['response_time']:.2f}s")
        logger.info(f"  Final URL: {result['final_url'][:100]}...")
        if result['error']:
            logger.info(f"  Error: {result['error']}")
        logger.info("")
    
    # Recommendations
    logger.info("💡 RECOMMENDATIONS:")
    if captcha_profiles:
        logger.info("• CAPTCHA detected - Google is blocking automated requests")
        logger.info("• Solutions:")
        logger.info("  - Add more delays between profile actions")
        logger.info("  - Use residential proxies for each profile")
        logger.info("  - Implement more human-like behavior")
        logger.info("  - Reduce number of simultaneous profiles")
        logger.info("  - Add random mouse movements and scrolling")
    
    return test_results

# Resolve profile configurations (JSON or auto-discover)
profile_configs = load_profile_configs()

class ProfileManager:
    """Manages individual profile lifecycle and automation"""
    
    def __init__(self, idx, config):
        self.idx = idx
        self.config = config
        self.driver = None
        self.fingerprint = None
        self.status = "initialized"
    
    def launch(self):
        """Launch this profile in its own thread"""
        try:
            self.status = "launching"
            self.driver = create_chrome_profile(self.config)
            
            if FPRINT_ONLY:
                # Use a neutral page to avoid CSP/frame blockers during fingerprint collection
                try:
                    self.driver.get("https://example.com")
                except Exception:
                    pass
                wait_for_document_ready(self.driver, 10)
                self.fingerprint = collect_fingerprint(self.driver)
            else:
                # Start with a neutral page to warm up the profile
                self.driver.get("https://example.com")
                time.sleep(random.uniform(2, 4))
                
                # Simulate some browsing behavior
                simulate_human_behavior(self.driver)
                
                # Then go to Instagram
                self.driver.get("https://www.instagram.com")
                logger.info(f"Profile {self.idx} opened with URL: {self.driver.current_url}")
                
                # More human-like behavior
                time.sleep(random.uniform(3, 7))
                simulate_human_behavior(self.driver)
            
            self.status = "ready"
            return True
        except Exception as e:
            logger.error(f"Failed to launch profile {self.idx}: {e}")
            self.status = "failed"
            return False
    
    def close(self):
        """Close this profile"""
        try:
            if self.driver:
                self.driver.quit()
                self.status = "closed"
                logger.info(f"Profile {self.idx} closed")
        except Exception as e:
            logger.error(f"Failed to close profile {self.idx}: {e}")
    
    def get_info(self):
        """Get profile information for automation"""
        return {
            "idx": self.idx,
            "driver": self.driver,
            "config": self.config,
            "fingerprint": self.fingerprint,
            "status": self.status
        }

def launch_profile_parallel(profile_manager):
    """Launch a single profile (threading helper)"""
    return profile_manager.launch()

def close_profile_parallel(profile_manager):
    """Close a single profile (threading helper)"""
    try:
        if profile_manager.driver:
            profile_manager.driver.quit()
            profile_manager.status = "closed"
        return profile_manager.idx
    except Exception as e:
        logger.error(f"Failed to close profile {profile_manager.idx}: {e}")
        return profile_manager.idx

# Initialize profile managers
profile_managers = [ProfileManager(idx, config) for idx, config in enumerate(profile_configs, start=1)]
FPRINT_ONLY = os.environ.get("FPRINT_ONLY", "0") == "1"

# Launch all profiles in parallel
logger.info(f"Launching {len(profile_managers)} profiles in parallel...")
max_workers = min(len(profile_managers), 10)  # Limit concurrent threads

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all profile launches
    launch_futures = {
        executor.submit(launch_profile_parallel, pm): pm 
        for pm in profile_managers
    }
    
    # Wait for all launches to complete
    successful_launches = 0
    for future in as_completed(launch_futures):
        pm = launch_futures[future]
        success = future.result()
        if success:
            successful_launches += 1
            logger.info(f"Profile {pm.idx} launched successfully")

logger.info(f"Successfully launched {successful_launches}/{len(profile_managers)} profiles")

# Log fingerprints if collected
fingerprints = []
for pm in profile_managers:
    if pm.fingerprint:
        fingerprints.append({"profile": pm.idx, "fp": pm.fingerprint})

if fingerprints:
    logger.info("Collected fingerprints:")
    for item in fingerprints:
        logger.info(json.dumps(item, ensure_ascii=False))

# Keep profiles open for automation (remove this section if you want immediate closing)
if not FPRINT_ONLY:
    logger.info("All profiles ready for automation.")
    
    # Run diagnostic test for Google search
    if successful_launches > 0:
        logger.info("Running diagnostic test for Google search...")
        time.sleep(5)  # Wait for profiles to stabilize
        test_results = diagnose_profile_issues(profile_managers)
        
        # Save results to file
        results_file = "google_search_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        logger.info(f"Test results saved to: {results_file}")
    
    logger.info("Press Ctrl+C to close all profiles.")
    try:
        # Keep the script running so profiles stay open
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Closing all profiles...")

# Close all profiles in parallel
logger.info("Closing all profiles in parallel...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all close operations simultaneously
    close_futures = [
        executor.submit(close_profile_parallel, pm) 
        for pm in profile_managers
    ]
    
    # Wait for all closes to complete (truly parallel)
    closed_profiles = []
    for future in as_completed(close_futures):
        profile_id = future.result()
        closed_profiles.append(profile_id)

close_time = time.time() - start_time
logger.info(f"All {len(closed_profiles)} profiles closed in {close_time:.2f} seconds")
