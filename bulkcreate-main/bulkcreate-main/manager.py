import os
import json
import argparse
import sys
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import shutil
import random
import urllib.parse

# --- CONFIGURATION ---
# ❗ IMPORTANT: Change this path to where your chromedriver.exe is located!
CHROMEDRIVER_PATH = "E:/work/IG-Automation/bulkcreate-main/bulkcreate-main/chromedriver.exe"
PROFILES_DIR = "./selenium_profiles"
PROFILE_CONFIG_FILE = os.path.join(PROFILES_DIR, "profiles.json")

# List of user agents to be chosen from randomly
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # macOS Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    # macOS Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
    # macOS Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    # iOS Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    # Android Firefox
    "Mozilla/5.0 (Mobile; rv:127.0) Gecko/127.0 Firefox/127.0",
    "Mozilla/5.0 (Android 13; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0",
    "Mozilla/5.0 (Android 12; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0"
]

# Screen resolutions (desktop and mobile)
SCREEN_RESOLUTIONS = [
    # Desktop resolutions
    [1920, 1080], [1366, 768], [1536, 864], [1440, 900], [1280, 720],
    # Mobile resolutions
    [375, 667], [414, 896], [390, 844], [360, 640], [412, 915]
]

# Languages
LANGUAGES = [
    "en-US,en;q=0.9", "en-GB,en;q=0.9", "es-ES,es;q=0.9", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9"
]

# Timezones (focused on German and European zones)
TIMEZONES = [
    "Europe/Berlin", "Europe/Munich", "Europe/Hamburg", "Europe/Cologne",
    "Europe/Frankfurt", "Europe/Stuttgart", "Europe/Dusseldorf",
    "Europe/Vienna", "Europe/Zurich", "Europe/Amsterdam",
    "Europe/Paris", "Europe/London", "Europe/Rome", "Europe/Madrid"
]

# Ensure the main profiles directory exists
os.makedirs(PROFILES_DIR, exist_ok=True)


# --- HELPER FUNCTIONS ---

def load_profiles():
    """Loads the profiles data from the JSON file."""
    if not os.path.exists(PROFILE_CONFIG_FILE):
        return {}
    try:
        with open(PROFILE_CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_profiles(data):
    """Saves the profiles data to the JSON file."""
    with open(PROFILE_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


# --- CORE LOGIC FUNCTIONS ---

def list_profiles():
    """Prints all profile configurations as a JSON string to standard output."""
    profiles = load_profiles()
    # Print the raw JSON string so Node.js can easily parse it
    print(json.dumps(profiles, indent=4))

def create_bulk_profiles(count, device_type="random", name_prefix="Profile"):
    """Creates multiple profiles with specified device type."""
    if not count or count <= 0:
        print("Error: Count must be a positive number.", file=sys.stderr)
        sys.exit(1)
    
    # Filter user agents by device type
    if device_type == "ios":
        filtered_agents = [ua for ua in USER_AGENTS if "iPhone" in ua or "iPad" in ua]
        filtered_resolutions = [[375, 667], [414, 896], [390, 844]]  # iOS resolutions
    elif device_type == "android":
        filtered_agents = [ua for ua in USER_AGENTS if "Android" in ua and "Mobile" in ua]
        filtered_resolutions = [[360, 640], [412, 915], [375, 667]]  # Android resolutions
    elif device_type == "windows":
        filtered_agents = [ua for ua in USER_AGENTS if "Windows" in ua]
        filtered_resolutions = [[1920, 1080], [1366, 768], [1536, 864]]  # Desktop resolutions
    elif device_type == "macos":
        filtered_agents = [ua for ua in USER_AGENTS if "Macintosh" in ua and "Mobile" not in ua]
        filtered_resolutions = [[1920, 1080], [1440, 900], [1280, 720]]  # Desktop resolutions
    else:
        filtered_agents = USER_AGENTS
        filtered_resolutions = SCREEN_RESOLUTIONS
    
    profiles = load_profiles()
    created_profiles = []
    
    for i in range(1, count + 1):
        profile_name = f"{name_prefix}_{i}"
        
        # Skip if profile already exists
        if profile_name in profiles:
            print(f"Info: Profile '{profile_name}' already exists. Skipping.", file=sys.stderr)
            continue
        
        # Create profile directory
        profile_data_path = os.path.join(PROFILES_DIR, profile_name)
        os.makedirs(profile_data_path, exist_ok=True)
        default_profile_path = os.path.join(profile_data_path, "Default")
        os.makedirs(default_profile_path, exist_ok=True)
        
        # Create profile config
        profiles[profile_name] = {
            "proxy": "",
            "user_agent": random.choice(filtered_agents),
            "window_size": random.choice(filtered_resolutions),
            "remark": f"Bulk created - {device_type}",
            "language": random.choice(LANGUAGES),
            "timezone": random.choice(TIMEZONES),
            "webrtc": "disabled",
            "startup_urls": ["https://amiunique.org/fp"]
        }
        created_profiles.append(profile_name)
    
    save_profiles(profiles)
    print(f"Success: Created {len(created_profiles)} profiles with {device_type} devices.", file=sys.stderr)
    for name in created_profiles:
        print(f"  - {name}", file=sys.stderr)

def create_profile(name, config=None):
    """Creates a new profile with specified or random configuration if it doesn't exist."""
    if not name:
        print("Error: Profile name cannot be empty.", file=sys.stderr)
        sys.exit(1)
        
    profiles = load_profiles()
    
    if name in profiles:
        print(f"Info: Profile '{name}' already exists. No changes made.", file=sys.stderr)
        return

    # Each profile gets its own data directory with proper structure
    profile_data_path = os.path.join(PROFILES_DIR, name)
    os.makedirs(profile_data_path, exist_ok=True)
    
    # Ensure Default profile directory exists for Chrome data
    default_profile_path = os.path.join(profile_data_path, "Default")
    os.makedirs(default_profile_path, exist_ok=True)

    # Use provided config or generate random values
    if config is None:
        config = {}
    
    profiles[name] = {
        "proxy": config.get("proxy", ""),
        "user_agent": config.get("user_agent", random.choice(USER_AGENTS)),
        "window_size": config.get("window_size", random.choice(SCREEN_RESOLUTIONS)),
        "remark": config.get("remark", ""),
        "language": config.get("language", random.choice(LANGUAGES)),
        "timezone": config.get("timezone", random.choice(TIMEZONES)),
        "webrtc": config.get("webrtc", "disabled"),
        "startup_urls": config.get("startup_urls", ["https://amiunique.org/fp"])
    }
    
    save_profiles(profiles)
    print(f"Success: New profile '{name}' was created.", file=sys.stderr)
    print(f"  - User Agent: {profiles[name]['user_agent']}", file=sys.stderr)
    print(f"  - Window Size: {profiles[name]['window_size'][0]}x{profiles[name]['window_size'][1]}", file=sys.stderr)


def launch_profile(name):
    """Launches an undetected_chromedriver instance with the specified profile."""
    profiles = load_profiles()
    
    if name not in profiles:
        print(f"Error: Profile '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    profile_config = profiles[name]
    profile_data_path = os.path.abspath(os.path.join(PROFILES_DIR, name))
    
    print(f"Info: Launching profile '{name}'...", file=sys.stderr)
    
    chrome_options = Options()
    
    # This is the most important part for session isolation and data persistence
    chrome_options.add_argument(f"--user-data-dir={profile_data_path}")
    chrome_options.add_argument(f"--profile-directory=Default")
    
    # Essential options for data persistence
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    # Force data and session persistence
    chrome_options.add_argument("--enable-local-storage")
    chrome_options.add_argument("--enable-session-storage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--restore-last-session")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    
    # Set user agent and other stealth options from the saved profile config
    user_agent = profile_config['user_agent']
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Set language
    language = profile_config.get('language', 'en-US,en;q=0.9')
    chrome_options.add_argument(f"--accept-lang={language}")
    
    # Set timezone
    timezone = profile_config.get('timezone', 'America/New_York')
    chrome_options.add_argument(f"--timezone={timezone}")
    
    # WebRTC settings
    webrtc = profile_config.get('webrtc', 'disabled')
    if webrtc == 'disabled':
        chrome_options.add_argument("--disable-webrtc")
    elif webrtc == 'replace':
        chrome_options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")
    
    # Apply proxy if it exists and is not empty
    proxy = profile_config.get("proxy", "").strip()
    if not proxy:
        print("Info: No proxy configured for this profile.", file=sys.stderr)

    # Configure proxy before driver starts
    if proxy:
        # Parse proxy URL
        import urllib.parse
        parsed = urllib.parse.urlparse(proxy if proxy.startswith('http') else f'http://{proxy}')
        
        # Use simple proxy-server argument
        chrome_options.add_argument(f'--proxy-server=http://{parsed.hostname}:{parsed.port}')
        
        print(f"Info: Proxy configured: {parsed.hostname}:{parsed.port}", file=sys.stderr)

    try:
        # Use undetected_chromedriver
        # Enable DevTools remote debugging if requested
        remote_debug = os.environ.get('REMOTE_DEBUG', '').lower() in ('1', 'true', 'yes')
        remote_arg = None
        if remote_debug:
            # let Chrome pick a free port automatically
            remote_arg = '--remote-debugging-port=0'
            chrome_options.add_argument(remote_arg)

        driver = uc.Chrome(
            driver_executable_path=CHROMEDRIVER_PATH, 
            options=chrome_options,
            version_main=None
        )
        
        if proxy:
            print("Info: Proxy configured - authentication will be requested by browser", file=sys.stderr)
        
        # Set the window size from the saved profile config  
        width, height = profile_config['window_size']
        driver.set_window_size(width, height)
        print(f"Info: Set window size to {width}x{height}", file=sys.stderr)
        
        # Check if profile has existing session data
        session_file = os.path.join(profile_data_path, 'Default', 'Current Session')
        tabs_file = os.path.join(profile_data_path, 'Default', 'Current Tabs')
        cookies_file = os.path.join(profile_data_path, 'Default', 'Cookies')
        
        has_existing_session = os.path.exists(session_file) or os.path.exists(tabs_file)
        has_existing_data = os.path.exists(cookies_file)
        
        if has_existing_session:
            # Existing session - Chrome should restore tabs automatically
            print("Info: Restoring previous session with tabs", file=sys.stderr)
            time.sleep(3)  # Give Chrome time to restore session
        else:
            # New session - open startup URLs (fallback to Google if none)
            startup_urls = profile_config.get('startup_urls', ["https://www.google.com"]) or ["https://www.google.com"]
            try:
                driver.get(startup_urls[0])
            except Exception:
                # As an ultra-safe fallback, ensure a tab remains open
                driver.get("https://www.google.com")
            time.sleep(2)
            for url in startup_urls[1:]:
                try:
                    driver.execute_script(f"window.open('{url}', '_blank');")
                except Exception:
                    pass
            print("Info: New session - opened initial tab", file=sys.stderr)
        
        if has_existing_data:
            print("Info: Profile data loaded - cookies and history available", file=sys.stderr)
        
        # Keep the browser open and monitor for closure
        print("Info: Browser is open and running.", file=sys.stderr)

        # If remote debugging was enabled, locate the DevToolsActivePort and print WS JSON
        if remote_debug:
            try:
                # DevToolsActivePort lives under user data dir root
                active_port_file = os.path.join(profile_data_path, 'DevToolsActivePort')
                port = None
                if os.path.exists(active_port_file):
                    with open(active_port_file, 'r') as f:
                        lines = f.read().strip().splitlines()
                        if lines:
                            port = int(lines[0])
                if port:
                    import urllib.request, json as _json
                    ver_url = f'http://127.0.0.1:{port}/json/version'
                    with urllib.request.urlopen(ver_url, timeout=3) as resp:
                        meta = _json.loads(resp.read().decode('utf-8'))
                        ws = meta.get('webSocketDebuggerUrl')
                        if ws:
                            # Emit a single-line JSON for the caller to parse
                            print(_json.dumps({"ws": ws}))
                            sys.stdout.flush()
            except Exception as e:
                print(f"Warn: could not resolve DevTools WS: {e}", file=sys.stderr)
        
        # Monitor browser status
        try:
            while True:
                try:
                    # Check if browser is still alive
                    driver.current_url
                    time.sleep(2)
                except:
                    # Browser was closed by user
                    break
        except KeyboardInterrupt:
            # Process was killed by server
            try:
                driver.quit()
            except:
                pass
        
        # Ensure all data and session are properly saved before closing
        try:
            # Force save all data and session state
            driver.execute_script("window.localStorage.setItem('profile_closed', Date.now());")
            driver.execute_script("window.sessionStorage.setItem('profile_closed', Date.now());")
            
            # Force Chrome to save session data
            driver.execute_cdp_cmd('Page.enable', {})
            driver.execute_cdp_cmd('Runtime.evaluate', {
                'expression': 'chrome.sessions && chrome.sessions.getRecentlyClosed && chrome.sessions.getRecentlyClosed()'
            })
            
            # Give Chrome extra time to write session data to disk
            time.sleep(3)
        except:
            pass
        print(f"Success: Browser for profile '{name}' closed. Session and data saved to: {profile_data_path}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error launching browser for profile '{name}': {e}", file=sys.stderr)
        sys.exit(1)

def delete_bulk_profiles(names):
    """Deletes multiple profiles."""
    if not names:
        print("Error: No profile names provided.", file=sys.stderr)
        sys.exit(1)
    
    profiles = load_profiles()
    deleted_profiles = []
    
    for name in names:
        if name not in profiles:
            print(f"Warning: Profile '{name}' not found. Skipping.", file=sys.stderr)
            continue
        
        # Remove from dictionary
        del profiles[name]
        
        # Delete profile data folder with error handling
        profile_data_path = os.path.join(PROFILES_DIR, name)
        if os.path.exists(profile_data_path):
            try:
                # Force delete on Windows
                import stat
                def handle_remove_readonly(func, path, exc):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                
                shutil.rmtree(profile_data_path, onerror=handle_remove_readonly)
            except Exception as e:
                print(f"Warning: Could not delete folder for '{name}': {e}", file=sys.stderr)
        
        deleted_profiles.append(name)
    
    save_profiles(profiles)
    print(f"Success: Deleted {len(deleted_profiles)} profiles.", file=sys.stderr)
    for name in deleted_profiles:
        print(f"  - {name}", file=sys.stderr)

def disable_proxy(name):
    """Disables proxy for a specific profile."""
    profiles = load_profiles()
    
    if name not in profiles:
        print(f"Error: Profile '{name}' not found.", file=sys.stderr)
        sys.exit(1)
    
    profiles[name]["proxy"] = ""
    save_profiles(profiles)
    print(f"Success: Proxy disabled for profile '{name}'.", file=sys.stderr)

def rename_profile(old_name, new_name):
    """Renames a profile and its data directory."""
    profiles = load_profiles()
    
    if old_name not in profiles:
        print(f"Error: Profile '{old_name}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if new_name in profiles:
        print(f"Error: Profile '{new_name}' already exists.", file=sys.stderr)
        sys.exit(1)
    
    # Update profiles config
    profiles[new_name] = profiles[old_name]
    del profiles[old_name]
    
    # Rename data directory
    old_path = os.path.join(PROFILES_DIR, old_name)
    new_path = os.path.join(PROFILES_DIR, new_name)
    
    if os.path.exists(old_path):
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            print(f"Warning: Could not rename data directory: {e}", file=sys.stderr)
    
    save_profiles(profiles)
    print(f"Success: Profile renamed from '{old_name}' to '{new_name}'.", file=sys.stderr)

def change_proxy(name, new_proxy):
    """Changes proxy for a specific profile."""
    profiles = load_profiles()
    
    if name not in profiles:
        print(f"Error: Profile '{name}' not found.", file=sys.stderr)
        sys.exit(1)
    
    profiles[name]["proxy"] = new_proxy.strip() if new_proxy else ""
    save_profiles(profiles)
    
    if new_proxy.strip():
        print(f"Success: Proxy changed for profile '{name}' to '{new_proxy}'.", file=sys.stderr)
    else:
        print(f"Success: Proxy removed for profile '{name}'.", file=sys.stderr)

def export_profiles(export_path):
    """Exports all profiles with data to a ZIP file."""
    profiles = load_profiles()
    
    if not profiles:
        print("Warning: No profiles to export.", file=sys.stderr)
        return
    
    import zipfile
    
    try:
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add profiles.json
            export_data = {
                "version": "1.0",
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "profiles": profiles
            }
            zipf.writestr('profiles.json', json.dumps(export_data, indent=4))
            
            # Add profile data directories
            for profile_name in profiles.keys():
                profile_data_path = os.path.join(PROFILES_DIR, profile_name)
                if os.path.exists(profile_data_path):
                    for root, dirs, files in os.walk(profile_data_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, PROFILES_DIR)
                            try:
                                zipf.write(file_path, arc_path)
                            except Exception as e:
                                print(f"Warning: Could not add {file_path}: {e}", file=sys.stderr)
        
        print(f"Success: Exported {len(profiles)} profiles with data to {export_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error: Failed to export profiles: {e}", file=sys.stderr)
        sys.exit(1)

def import_profiles(import_path, overwrite=False):
    """Imports profiles with data from a ZIP file."""
    if not os.path.exists(import_path):
        print(f"Error: Import file '{import_path}' not found.", file=sys.stderr)
        sys.exit(1)
    
    import zipfile
    
    try:
        with zipfile.ZipFile(import_path, 'r') as zipf:
            # Read profiles.json
            try:
                profiles_data = zipf.read('profiles.json').decode('utf-8')
                import_data = json.loads(profiles_data)
            except Exception as e:
                print(f"Error: Failed to read profiles.json from archive: {e}", file=sys.stderr)
                sys.exit(1)
            
            if "profiles" not in import_data:
                print("Error: Invalid import file format.", file=sys.stderr)
                sys.exit(1)
            
            current_profiles = load_profiles()
            imported_profiles = import_data["profiles"]
            
            imported_count = 0
            skipped_count = 0
            
            for name, config in imported_profiles.items():
                if name in current_profiles and not overwrite:
                    print(f"Info: Profile '{name}' already exists. Skipping.", file=sys.stderr)
                    skipped_count += 1
                    continue
                
                # Remove existing profile data if overwriting
                profile_data_path = os.path.join(PROFILES_DIR, name)
                if overwrite and os.path.exists(profile_data_path):
                    try:
                        import stat
                        def handle_remove_readonly(func, path, exc):
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                        shutil.rmtree(profile_data_path, onerror=handle_remove_readonly)
                    except Exception as e:
                        print(f"Warning: Could not remove existing data for '{name}': {e}", file=sys.stderr)
                
                # Extract profile data
                for file_info in zipf.filelist:
                    if file_info.filename.startswith(f"{name}/") and not file_info.is_dir():
                        try:
                            zipf.extract(file_info, PROFILES_DIR)
                        except Exception as e:
                            print(f"Warning: Could not extract {file_info.filename}: {e}", file=sys.stderr)
                
                current_profiles[name] = config
                imported_count += 1
            
            save_profiles(current_profiles)
            print(f"Success: Imported {imported_count} profiles with data. Skipped {skipped_count} existing profiles.", file=sys.stderr)
            
    except Exception as e:
        print(f"Error: Failed to import profiles: {e}", file=sys.stderr)
        sys.exit(1)

def delete_profile(name):
    """Deletes a profile's configuration and its data directory."""
    profiles = load_profiles()
    
    if name not in profiles:
        print(f"Error: Profile '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    # Remove from the dictionary
    del profiles[name]
    save_profiles(profiles)
    
    # Delete the profile's data folder with error handling
    profile_data_path = os.path.join(PROFILES_DIR, name)
    if os.path.exists(profile_data_path):
        try:
            # Force delete on Windows
            import stat
            def handle_remove_readonly(func, path, exc):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            
            shutil.rmtree(profile_data_path, onerror=handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Could not delete folder for '{name}': {e}", file=sys.stderr)
        
    print(f"Success: Profile '{name}' and its data have been deleted.", file=sys.stderr)

# --- COMMAND-LINE INTERFACE SETUP ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browser Profile Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Command: list
    parser_list = subparsers.add_parser("list", help="List all available profiles in JSON format.")

    # Command: create
    parser_create = subparsers.add_parser("create", help="Create a new browser profile.")
    parser_create.add_argument("--name", required=True, help="The name of the profile.")
    parser_create.add_argument("--proxy", default="", help="Proxy settings (e.g., 'http://user:pass@host:port'). Optional.")
    parser_create.add_argument("--config", help="JSON configuration string for advanced profile settings.")

    # Command: launch
    parser_launch = subparsers.add_parser("launch", help="Launch a browser session for a specific profile.")
    parser_launch.add_argument("--name", required=True, help="The name of the profile to launch.")

    # Command: delete
    parser_delete = subparsers.add_parser("delete", help="Delete a profile and its data.")
    parser_delete.add_argument("--name", required=True, help="The name of the profile to delete.")
    
    # Command: bulk-create
    parser_bulk_create = subparsers.add_parser("bulk-create", help="Create multiple profiles at once.")
    parser_bulk_create.add_argument("--count", type=int, required=True, help="Number of profiles to create.")
    parser_bulk_create.add_argument("--device-type", choices=["ios", "android", "windows", "macos", "random"], default="random", help="Device type for profiles.")
    parser_bulk_create.add_argument("--prefix", default="Profile", help="Name prefix for profiles.")
    
    # Command: bulk-delete
    parser_bulk_delete = subparsers.add_parser("bulk-delete", help="Delete multiple profiles at once.")
    parser_bulk_delete.add_argument("--names", nargs="+", required=True, help="Names of profiles to delete.")
    
    # Command: disable-proxy
    parser_disable_proxy = subparsers.add_parser("disable-proxy", help="Disable proxy for a profile.")
    parser_disable_proxy.add_argument("--name", required=True, help="The name of the profile.")
    
    # Command: rename
    parser_rename = subparsers.add_parser("rename", help="Rename a profile.")
    parser_rename.add_argument("--old-name", required=True, help="Current name of the profile.")
    parser_rename.add_argument("--new-name", required=True, help="New name for the profile.")
    
    # Command: change-proxy
    parser_change_proxy = subparsers.add_parser("change-proxy", help="Change proxy for a profile.")
    parser_change_proxy.add_argument("--name", required=True, help="The name of the profile.")
    parser_change_proxy.add_argument("--proxy", default="", help="New proxy URL (empty to remove proxy).")
    
    # Command: export
    parser_export = subparsers.add_parser("export", help="Export all profiles with data to a ZIP file.")
    parser_export.add_argument("--path", required=True, help="Path to export ZIP file.")
    
    # Command: import
    parser_import = subparsers.add_parser("import", help="Import profiles with data from a ZIP file.")
    parser_import.add_argument("--path", required=True, help="Path to import ZIP file.")
    parser_import.add_argument("--overwrite", action="store_true", help="Overwrite existing profiles.")

    args = parser.parse_args()

    # Execute the corresponding function based on the command
    if args.command == "list":
        list_profiles()
    elif args.command == "create":
        config = None
        if hasattr(args, 'config') and args.config:
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError:
                print("Error: Invalid JSON configuration.", file=sys.stderr)
                sys.exit(1)
        if config is None:
            config = {"proxy": args.proxy}
        else:
            config["proxy"] = args.proxy
        create_profile(args.name, config)
    elif args.command == "launch":
        launch_profile(args.name)
    elif args.command == "delete":
        delete_profile(args.name)
    elif args.command == "bulk-create":
        create_bulk_profiles(args.count, args.device_type, args.prefix)
    elif args.command == "bulk-delete":
        delete_bulk_profiles(args.names)
    elif args.command == "disable-proxy":
        disable_proxy(args.name)
    elif args.command == "rename":
        rename_profile(args.old_name, args.new_name)
    elif args.command == "change-proxy":
        change_proxy(args.name, args.proxy)
    elif args.command == "export":
        export_profiles(args.path)
    elif args.command == "import":
        import_profiles(args.path, args.overwrite)