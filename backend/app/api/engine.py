from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.auth import require_admin
from app.models.account import Account
from app.services.cdp import navigate
import asyncio
from urllib.parse import urlparse
from app.services.ig_probe import check_login_state
from fastapi import Body
from app.services.actions import ensure_profile_ws, CDPClient
from app.services.ig_login import login_once
import json

router = APIRouter()
log = logging.getLogger(__name__)

def _normalize_url(u: str) -> str:
    if "://" not in u:
        return "https://" + u
    return u

@router.post("/visit", dependencies=[Depends(require_admin)])
async def visit(profile_id: int = Query(...), url: str = Query(...), db: Session = Depends(get_db)):
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="account has no stored WS; open it first")

    url = _normalize_url(url)
    # very basic guard
    try:
        urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid URL")

    try:
        info = await asyncio.wait_for(navigate(p.last_ws_puppeteer, url), timeout=20)
        return {"profile_id": p.id, "navigated_to": info}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"navigation failed: {e}")
    
@router.post("/login", dependencies=[Depends(require_admin)])
async def do_login(
    profile_id: int = Query(...),
    payload: dict = Body(...)
    , db: Session = Depends(get_db)
):
    """
    One-time helper to submit Instagram login form via CDP.
    Does NOT store credentials. Use it only to seed the AdsPower profile cookies.
    payload = { "username": "...", "password": "..." }
    """
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")
    if not p.last_ws_puppeteer:
        raise HTTPException(status_code=400, detail="account has no stored WS; open it first")

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username/password required")

    try:
        # submit login
        res = await asyncio.wait_for(login_once(p.last_ws_puppeteer, username, password), timeout=25)
        # re-check state
        st = await asyncio.wait_for(check_login_state(p.last_ws_puppeteer), timeout=12)
        return {
            "profile_id": p.id,
            "submitted": res.get("submitted"),
            "after_submit": res.get("after"),
            "login_state": st,
            "note": "If state is 'checkpoint', complete 2FA/checkpoint manually in the AdsPower window."
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"login failed: {e}")

@router.get("/login-state", dependencies=[Depends(require_admin)])
async def login_state(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")

    # Ensure a running browser profile and get a valid WS URL (auto-opens if needed)
    try:
        ws_url = await ensure_profile_ws(db, profile_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"failed to open profile: {e}")

    # Efficient flow: if already on Instagram, don't re-navigate; otherwise, go once
    try:
        async with CDPClient(ws_url) as cdp:
            sid = await cdp.get_page_session()
            try:
                current_url = await cdp.eval(sid, "location.href")
            except Exception:
                current_url = None
            log.info("check_login: ws ok; current_url=%s", current_url)
            if not (isinstance(current_url, str) and "instagram.com" in current_url):
                log.info("check_login: navigating to instagram.com")
                await cdp.goto(sid, "https://www.instagram.com/", wait="domcontent")
                await asyncio.sleep(0.6)
    except Exception as e:
        log.warning("check_login: navigation/setup issue: %s", e)

    try:
        info = await asyncio.wait_for(check_login_state(ws_url), timeout=12)
        log.info("check_login: result=%s", info)
        return {"profile_id": p.id, "login": info}
    except Exception as e:
        log.error("check_login: probe failed: %s", e)
        raise HTTPException(status_code=502, detail=f"login-state failed: {e}")

@router.post("/sync-username", dependencies=[Depends(require_admin)])
async def sync_username(profile_id: int, db: Session = Depends(get_db)):
    """
    Sync logged-in Instagram username quickly & reliably.
    Uses Instagram's own internal JSON endpoints before falling back to DOM/meta.
    """
    p = db.query(Account).get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="account not found")
    if not p.bulk_profile_name:
        raise HTTPException(status_code=400, detail="account has no linked profile")

    try:
        ws_url = await ensure_profile_ws(db, profile_id)
        if not ws_url:
            raise HTTPException(status_code=400, detail="could not open profile")

        async with CDPClient(ws_url) as cdp:
            sid = await cdp.get_page_session()

            # Fast path: if already on instagram.com, don't navigate
            try:
                current_url = await cdp.eval(sid, "location.href")
            except Exception:
                current_url = None
            if not (isinstance(current_url, str) and "instagram.com" in current_url):
                await cdp.goto(sid, "https://www.instagram.com/", wait="domcontent")
                await asyncio.sleep(0.3)

            username_js = r"""
            (async function(){
              const valid = u => /^[a-z0-9._]{1,50}$/i.test(u);
              const getCookie = name => {
                const m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/[-[\]/{}()*+?.\\^$|]/g, "\\$&") + '=([^;]*)'));
                return m ? decodeURIComponent(m[1]) : '';
              };
              const BAD = new Set(["","explore","direct","accounts","account","login","reel","reels","p","stories","challenge","sessions","session","notifications","terms","privacy","about","graphql","developer","downloads"]);

              async function tryAPIs(){
                const csrf = getCookie('csrftoken');
                const headers = {
                  'Accept': 'application/json',
                  'X-Requested-With': 'XMLHttpRequest',
                  'X-CSRFToken': csrf || '',
                  'X-IG-App-ID': '936619743392459',
                  'X-ASBD-ID': '129477'
                };
                const urls = [
                  '/api/v1/accounts/current_user/?edit=true',
                  '/api/v1/accounts/edit/web_form_data/'
                ];
                for(const url of urls){
                  try{
                    const res = await fetch(url, {credentials:'same-origin', headers});
                    if(!res.ok) continue;
                    const j = await res.json();
                    const u = j?.user?.username || j?.form_data?.username || j?.username;
                    if(valid(u)) return {success:true, username:String(u).toLowerCase(), via:'api:'+url};
                  }catch(_){ }
                }
                return null;
              }

              function tryDOM(){
                const roots = [document.querySelector('nav'), document.querySelector('header'), document.querySelector('aside')].filter(Boolean);
                const anchors = roots.flatMap(r => Array.from(r.querySelectorAll('a[href^="/\"][href$="/\"]')));
                let best = null, bestScore = -1;
                for(const a of anchors){
                  const href = a.getAttribute('href') || '';
                  const m = /^\/([a-z0-9._]{1,50})\/$/i.exec(href);
                  if(!m) continue;
                  const uname = m[1].toLowerCase();
                  if(!valid(uname) || BAD.has(uname)) continue;
                  let score = 0;
                  const txt = (a.textContent||'').toLowerCase();
                  if(/\bprofile\b/.test(txt)) score += 3;
                  if(a.querySelector('img[alt$="profile picture"]')) score += 5;
                  if(a.closest('nav')) score += 1;
                  if(a.closest('aside')) score += 1;
                  if(score > bestScore){ bestScore = score; best = {success:true, username:uname, via:'dom:anchors', score}; }
                }
                return best;
              }

              const api = await tryAPIs();
              if(api) return api;
              const dom = tryDOM();
              if(dom) return dom;

              // Final fallback: canonical/og
              const canon = document.querySelector('link[rel="canonical"]');
              if(canon && canon.href){
                const m = canon.href.match(/instagram\.com\/([a-z0-9._]+)\//i);
                if(m && valid(m[1])) return {success:true, username:m[1], via:'canonical'};
              }
              const ogUrl = document.querySelector('meta[property="og:url"]');
              if(ogUrl && ogUrl.content){
                const m = ogUrl.content.match(/instagram\.com\/([a-z0-9._]+)\//i);
                if(m && valid(m[1])) return {success:true, username:m[1], via:'og:url'};
              }
              return {success:false, error:'username not found'};
            })();
            """

            result = await cdp.eval(sid, username_js)

            if result and result.get("success") and result.get("username"):
                username = result["username"].lower()
                p.instagram_username = username
                db.commit()
                db.refresh(p)

                log.info(f"Profile {profile_id}: Updated Instagram username to {username} via {result.get('via')}")
                return {
                    "profile_id": p.id,
                    "instagram_username": username,
                    "source": result.get("via"),
                    "message": f"Successfully synced username: @{username}"
                }

            error_msg = (result or {}).get("error", "username not found")
            log.warning(f"Profile {profile_id}: Failed to extract username - {error_msg}")
            return {
                "profile_id": p.id,
                "instagram_username": None,
                "message": f"Failed to extract username: {error_msg}"
            }

    except Exception as e:
        log.error(f"Profile {profile_id}: Sync username failed: {e}")
        raise HTTPException(status_code=502, detail=f"sync username failed: {e}")


async def _sync_username_one(db: Session, account_id: int) -> dict:
    """Internal helper to sync a single account's username. Returns result dict."""
    try:
        p = db.query(Account).get(account_id)
        if not p:
            return {"id": account_id, "status": "error", "error": "account_not_found"}
        if not p.bulk_profile_name:
            return {"id": account_id, "status": "skipped", "reason": "no_linked_profile"}

        ws_url = await ensure_profile_ws(db, account_id)
        async with CDPClient(ws_url) as cdp:
            sid = await cdp.get_page_session()
            try:
                current_url = await cdp.eval(sid, "location.href")
            except Exception:
                current_url = None
            if not (isinstance(current_url, str) and "instagram.com" in current_url):
                await cdp.goto(sid, "https://www.instagram.com/", wait="domcontent")
            username_js = r"""
            (async function(){
              const valid = u => /^[a-z0-9._]{1,50}$/i.test(u);
              const getCookie = name => {
                const m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/[-[\]/{}()*+?.\\^$|]/g, "\\$&") + '=([^;]*)'));
                return m ? decodeURIComponent(m[1]) : '';
              };
              const BAD = new Set(["","explore","direct","accounts","account","login","reel","reels","p","stories","challenge","sessions","session","notifications","terms","privacy","about","graphql","developer","downloads"]);
              async function tryAPIs(){
                const csrf = getCookie('csrftoken');
                const headers = { 'Accept':'application/json','X-Requested-With':'XMLHttpRequest','X-CSRFToken': csrf||'', 'X-IG-App-ID':'936619743392459','X-ASBD-ID':'129477' };
                const urls = ['/api/v1/accounts/current_user/?edit=true','/api/v1/accounts/edit/web_form_data/'];
                for(const url of urls){ try{ const res = await fetch(url,{credentials:'same-origin',headers}); if(!res.ok) continue; const j = await res.json(); const u = j?.user?.username || j?.form_data?.username || j?.username; if(valid(u)) return {success:true, username:String(u).toLowerCase(), via:'api:'+url}; }catch(_){}}
                return null;
              }
              function tryDOM(){
                const roots=[document.querySelector('nav'),document.querySelector('header'),document.querySelector('aside')].filter(Boolean);
                const anchors = roots.flatMap(r=>Array.from(r.querySelectorAll('a[href^="/\"][href$="/\"]')));
                for(const a of anchors){ const m = /^\/([a-z0-9._]{1,50})\/$/i.exec(a.getAttribute('href')||''); if(!m) continue; const u=m[1].toLowerCase(); if(!valid(u)||BAD.has(u)) continue; if(a.querySelector('img[alt$="profile picture"]')) return {success:true, username:u, via:'dom:anchors'}; }
                return null;
              }
              const api = await tryAPIs(); if(api) return api;
              const dom = tryDOM(); if(dom) return dom;
              const canon=document.querySelector('link[rel="canonical"]'); if(canon&&canon.href){ const m=canon.href.match(/instagram\.com\/([a-z0-9._]+)\//i); if(m&&valid(m[1])) return {success:true, username:m[1], via:'canonical'}; }
              const og=document.querySelector('meta[property="og:url"]'); if(og&&og.content){ const m=og.content.match(/instagram\.com\/([a-z0-9._]+)\//i); if(m&&valid(m[1])) return {success:true, username:m[1], via:'og:url'}; }
              return {success:false, error:'username not found'};
            })();
            """
            result = await cdp.eval(sid, username_js)
            if result and isinstance(result, dict) and result.get("success") and result.get("username"):
                username = str(result["username"]).lower()
                p.instagram_username = username
                db.commit()
                return {"id": p.id, "status": "ok", "instagram_username": username, "via": result.get("via")}
            else:
                return {"id": p.id, "status": "fail", "error": (result or {}).get("error", "username not found")}
    except Exception as e:
        return {"id": account_id, "status": "error", "error": str(e)}


@router.post("/sync-usernames-bulk", dependencies=[Depends(require_admin)])
async def sync_usernames_bulk(
    account_ids: list[int] = Body(..., embed=True),
    concurrency: int = Body(5, embed=True),
    db: Session = Depends(get_db),
):
    if not account_ids:
        return {"count": 0, "results": []}
    concurrency = max(1, min(int(concurrency or 5), 10))
    sem = asyncio.Semaphore(concurrency)

    async def _task(aid: int):
        async with sem:
            return await _sync_username_one(db, aid)

    tasks = [asyncio.create_task(_task(aid)) for aid in account_ids]
    results = await asyncio.gather(*tasks)
    # No bulk commit; per-task commits already performed
    ok = sum(1 for r in results if r.get("status") == "ok")
    return {"count": len(results), "updated": ok, "results": results}
