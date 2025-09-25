#!/usr/bin/env python3
"""
API-based debug script to extract DOM structure from Instagram's followers/following modal
"""

import argparse
import json
import requests
import time


def login(base: str, email: str, password: str) -> str:
    resp = requests.post(f"{base}/auth/login", json={"email": email, "password": password}, timeout=20)
    if resp.status_code != 200:
        raise SystemExit(f"login failed: {resp.status_code} {resp.text}")
    token = resp.json().get("access_token")
    if not token:
        raise SystemExit("login response missing access_token")
    return token


def debug_dom_structure(base: str, token: str, account_id: int, profile_id: int, username: str):
    """Debug DOM structure through API"""
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "account_id": account_id,
        "profile_id": profile_id,
        "username": username,
        "mode": "follow",
        "limit": 1,  # Just need to see the structure
        "max_scrolls": 1,
        "debug_dom": True,  # Special flag for debugging
    }
    
    print(f"Debugging DOM structure for profile {profile_id}, target: {username}")
    
    try:
        resp = requests.get(f"{base}/actions/mass-follow-stream", headers=headers, params=params, stream=True, timeout=30)
        if resp.status_code != 200:
            print(f"API error: {resp.status_code} {resp.text}")
            return
            
        print("SSE status:", resp.status_code, resp.reason)
        
        dom_data = None
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                try:
                    data = json.loads(data_str)
                    print(data)
                    
                    if data.get("type") == "debug_dom":
                        dom_data = data.get("dom_info")
                        break
                        
                except json.JSONDecodeError:
                    print(f"Failed to parse: {data_str}")
        
        if dom_data:
            print("\n=== DOM STRUCTURE DEBUG ===")
            print(json.dumps(dom_data, indent=2))
            
            # Save to file
            with open("dom_debug_output.json", "w") as f:
                json.dump(dom_data, f, indent=2)
            print("\nDebug output saved to dom_debug_output.json")
        else:
            print("No DOM debug data received")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Debug DOM structure")
    parser.add_argument("--account", type=int, required=True, help="Account ID")
    parser.add_argument("--profile", type=int, required=True, help="Profile ID")
    parser.add_argument("--username", required=True, help="Target username")
    parser.add_argument("--base", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--email", default="admin@example.com", help="Login email")
    parser.add_argument("--password", default="admin123", help="Login password")
    
    args = parser.parse_args()
    
    token = login(args.base, args.email, args.password)
    debug_dom_structure(args.base, token, args.account, args.profile, args.username)


if __name__ == "__main__":
    main()

