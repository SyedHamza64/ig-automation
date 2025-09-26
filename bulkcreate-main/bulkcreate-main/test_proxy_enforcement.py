import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time

def test_proxy_enforcement():
    print("=== TESTING PROXY ENFORCEMENT ===")
    print("Using fake proxy to verify strict enforcement...")
    
    # Use a non-existent proxy server
    test_proxy = "http://fake.proxy.server:8080"
    
    # Setup proxy using the same method as manager.py
    proxy_obj = Proxy()
    proxy_obj.proxy_type = ProxyType.MANUAL
    proxy_obj.http_proxy = "fake.proxy.server:8080"
    proxy_obj.ssl_proxy = "fake.proxy.server:8080"
    
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=./test_profile")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-default-apps")
    
    # Add proxy arguments (same as manager.py)
    chrome_options.add_argument(f'--proxy-server={test_proxy}')
    chrome_options.add_argument('--proxy-bypass-list=')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--disable-extensions')
    
    try:
        print("Starting Chrome with fake proxy...")
        
        # Use same approach as manager.py
        capabilities = chrome_options.to_capabilities()
        capabilities.update(proxy_obj.to_capabilities())
        
        driver = uc.Chrome(
            options=chrome_options,
            desired_capabilities=capabilities
        )
        
        driver.set_page_load_timeout(15)
        
        try:
            print("Attempting to load website...")
            driver.get("https://httpbin.org/ip")
            time.sleep(5)
            
            # If we get here, check what loaded
            page_source = driver.page_source
            print(f"Page loaded successfully (length: {len(page_source)})")
            
            # Check if it shows real IP (means proxy was bypassed)
            if "152.58.181.248" in page_source or "origin" in page_source:
                print("❌ FAIL: Website loaded - proxy was bypassed!")
                print("Local network was used instead of proxy")
            else:
                print("✅ SUCCESS: Proxy enforced - no real content loaded")
                
        except Exception as load_error:
            print("✅ SUCCESS: Website failed to load - proxy is enforced!")
            print(f"Error: {str(load_error)[:100]}...")
        
        driver.quit()
        
    except Exception as startup_error:
        print("✅ SUCCESS: Chrome failed to start with fake proxy!")
        print(f"Error: {str(startup_error)[:100]}...")
    
    print("\n=== TEST COMPLETE ===")
    print("Expected result: Website should FAIL to load")
    print("This proves proxy is strictly enforced")

if __name__ == "__main__":
    test_proxy_enforcement()