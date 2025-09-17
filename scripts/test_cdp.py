import argparse
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--ws", required=True, help="WebSocket URL")
parser.add_argument("--eval", help="JS code to eval")
parser.add_argument("--eval-file", help="Path to a JS file to eval")
args = parser.parse_args()

# Load JS from file if given
if args.eval_file:
    with open(args.eval_file, "r", encoding="utf-8") as f:
        js_code = f.read()
else:
    js_code = args.eval

WS = args.ws

with sync_playwright() as p:
    print("Connecting to:", WS)
    browser = p.chromium.connect_over_cdp(WS)

    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()

    if page.url in ("about:blank", "chrome://newtab/", ""):
        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print("Navigation error (ignored):", e)

    result = page.evaluate(js_code)
    print("Eval result:", result)
