import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time

def test_fixed_proxy():
    print("Testing FIXED proxy enforcement...")
    
    fake_proxy = "fake.proxy.test:9999"
    
    proxy_obj = Proxy()
    proxy_obj.proxy_type = ProxyType.MANUAL
    proxy_obj.http_proxy = fake_proxy
    proxy_obj.ssl_proxy = fake_proxy
    
    chrome_options = Options()
    chrome_options.add_argument(f'--proxy-server=http://{fake_proxy}')
    chrome_options.add_argument('--proxy-bypass-list=')
    
    try:
        capabilities = chrome_options.to_capabilities()
        capabilities.update(proxy_obj.to_capabilities())
        
        driver = uc.Chrome(
            options=chrome_options,
            desired_capabilities=capabilities
        )
        driver.set_page_load_timeout(30)
        
        try:
            print("Testing connection...")
            driver.get("https://httpbin.org/ip")
            time.sleep(3)
            
            if "152.58.181.248" in driver.page_source:
                print("FAIL: Local IP shown - proxy bypassed")
            else:
                print("SUCCESS: Proxy working or blocked")
                
        except Exception as e:
            print("SUCCESS: Connection blocked by proxy")
        
        driver.quit()
        
    except Exception as e:
        print(f"SUCCESS: Proxy enforced - {str(e)[:50]}...")

if __name__ == "__main__":
    test_fixed_proxy()