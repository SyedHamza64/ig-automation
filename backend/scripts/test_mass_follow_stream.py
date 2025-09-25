import argparse
import json
import sys
import time
from typing import Optional

import requests


def login(base: str, email: str, password: str) -> str:
    resp = requests.post(f"{base}/auth/login", json={"email": email, "password": password}, timeout=20)
    if resp.status_code != 200:
        raise SystemExit(f"login failed: {resp.status_code} {resp.text}")
    token = resp.json().get("access_token")
    if not token:
        raise SystemExit("login response missing access_token")
    return token


def stream(base: str, token: str, account_id: int, profile_id: int, username: str, mode: str,
           limit: int, percent: Optional[int], max_scrolls: int, section: str = "followers", max_events: int = 20) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "account_id": account_id,
        "profile_id": profile_id,
        "username": username,
        "mode": mode,
        "limit": limit,
        "max_scrolls": max_scrolls,
        "section": section,
    }
    if percent is not None:
        params["percent"] = percent

    with requests.get(f"{base}/actions/mass-follow-stream", headers=headers, params=params, stream=True, timeout=300) as r:
        print(f"SSE status: {r.status_code} {r.reason}")
        if r.status_code != 200:
            print(r.text)
            return
        ct = 0
        for line in r.iter_lines():
            if not line:
                continue
            s = line.decode(errors="ignore")
            if s.startswith("data: "):
                payload = s[6:]
                print(payload)
                ct += 1
                if ct >= max_events:
                    break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--email", default="admin@example.com")
    ap.add_argument("--password", default="admin123")
    ap.add_argument("--account", type=int, required=True)
    ap.add_argument("--profile", type=int, required=True)
    ap.add_argument("--username", required=True)
    ap.add_argument("--mode", choices=["follow", "unfollow"], default="follow")
    ap.add_argument("--section", choices=["followers", "following"], default="followers")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--percent", type=int, default=None)
    ap.add_argument("--max_scrolls", type=int, default=200)
    ap.add_argument("--events", type=int, default=20)
    args = ap.parse_args()

    token = login(args.base, args.email, args.password)
    stream(
        base=args.base,
        token=token,
        account_id=args.account,
        profile_id=args.profile,
        username=args.username,
        mode=args.mode,
        limit=args.limit,
        percent=args.percent,
        max_scrolls=args.max_scrolls,
        section=args.section,
        max_events=args.events,
    )


if __name__ == "__main__":
    main()


