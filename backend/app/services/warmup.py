import asyncio
import time
import random
from typing import AsyncGenerator, Dict, Any, Optional, Tuple

from .actions import CDPClient

# ===== WARMUP/FOCUS =====
JS_WARMUP_BOOT = r"""(function(){ try{ document.body.focus(); const el=document.elementFromPoint(window.innerWidth/2, window.innerHeight/2); if(el) el.dispatchEvent(new MouseEvent('click',{bubbles:true})); }catch(e){} return {ok:true}; })();"""

# ===== ENSURE WE ARE ON HOME FEED ("/") =====
JS_ENSURE_HOME = r"""
(()=>{ 
  try{
    // If not on root feed, force navigate back to "/"
    const badPath = location.pathname !== "/";
    const badHash = !!location.hash;
    const badSearch = !!location.search;
    // Also block obvious non-feed sections
    const notFeed = /^\/(reel|p|explore|direct|accounts|stories|topics|likes|saved)\b/.test(location.pathname);

    if (badPath || badHash || badSearch || notFeed) {
      history.replaceState(null, "", "/");
      // soft reload the feed UI without full navigation if possible
      try { window.dispatchEvent(new PopStateEvent("popstate")); } catch(e){}
    }

    // If after replace we're still not "/", perform hard navigate
    if (location.pathname !== "/") {
      location.assign("/");
    }

    // Close any dialogs/stories if opened
    const pressEsc = () => document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));
    for (let i=0;i<2;i++) pressEsc();

    // Heuristic: if no articles yet, nudge focus and wait a bit
    const arts = document.querySelectorAll('main article, article');
    if (arts.length === 0) {
      try{ (document.elementFromPoint(innerWidth/2, innerHeight/2)||document.body).click(); }catch(e){}
    }

    return {ok:true, path:location.pathname, arts: (arts && arts.length) || 0};
  }catch(e){
    return {ok:false, err: String(e) };
  }
})();
"""

# ===== REELS HELPERS =====
JS_FIND_CURRENT_REEL = r"""(function(){ const videos=Array.from(document.querySelectorAll('video')); if(!videos.length) return {ok:false,reason:'no-videos'}; const centerY=window.innerHeight/2; const scored=videos.map(v=>{const r=v.getBoundingClientRect(); const cy=r.top+r.height/2; return {el:v,dist:Math.abs(cy-centerY),rect:{top:r.top,height:r.height}};}).sort((a,b)=>a.dist-b.dist); const v=scored[0].el; try{ v.muted=true; v.play().catch(()=>{}); }catch(e){} let container=v.closest('article'); if(!container){ let p=v.parentElement; while(p&&p!==document.body){ const rr=p.getBoundingClientRect(); if(rr.height>0.6*window.innerHeight){ container=p; break;} p=p.parentElement;} if(!container) container=v; } return {ok:true,found:true,height:container.getBoundingClientRect().height,r:scored[0].rect}; })();"""

JS_SCROLL_NEXT_REEL = r"""
(function(){
  const centerY = window.innerHeight/2;
  const vids = Array.from(document.querySelectorAll('video'));
  if (!vids.length) return {ok:false, reason:'no-videos'};

  const list = vids.map(v => {
    const r = v.getBoundingClientRect();
    return { v, cy: r.top + r.height/2, r };
  }).sort((a,b)=>a.cy-b.cy);

  let idx = 0, best = 1e9;
  for (let i=0;i<list.length;i++){
    const d = Math.abs(list[i].cy - centerY);
    if (d < best){ best = d; idx = i; }
  }

  const nextIdx = Math.min(idx+1, list.length-1);
  const target = list[nextIdx].v;
  const cont = target.closest('article') || target.parentElement || target;

  cont.scrollIntoView({behavior:'smooth', block:'center'});
  try {
    for (let i=0;i<3;i++){
      const dy = 40 + Math.floor(Math.random()*40);
      const ev = new WheelEvent('wheel', {deltaY: dy, bubbles:true, cancelable:true});
      (document.scrollingElement||document.body).dispatchEvent(ev);
    }
  } catch(e){}

  return {ok:true, index: nextIdx, total:list.length, via:'scrollIntoView+wheel'};
})();
"""

JS_SCROLL_PREV_REEL = r"""
(function(){
  const centerY = window.innerHeight/2;
  const vids = Array.from(document.querySelectorAll('video'));
  if (!vids.length) return {ok:false, reason:'no-videos'};

  const list = vids.map(v => {
    const r = v.getBoundingClientRect();
    return { v, cy: r.top + r.height/2, r };
  }).sort((a,b)=>a.cy-b.cy);

  let idx = 0, best = 1e9;
  for (let i=0;i<list.length;i++){
    const d = Math.abs(list[i].cy - centerY);
    if (d < best){ best = d; idx = i; }
  }

  const prevIdx = Math.max(idx-1, 0);
  const target = list[prevIdx].v;
  const cont = target.closest('article') || target.parentElement || target;

  cont.scrollIntoView({behavior:'smooth', block:'center'});
  try {
    for (let i=0;i<3;i++){
      const dy = -(40 + Math.floor(Math.random()*40));
      const ev = new WheelEvent('wheel', {deltaY: dy, bubbles:true, cancelable:true});
      (document.scrollingElement||document.body).dispatchEvent(ev);
    }
  } catch(e){}

  return {ok:true, index: prevIdx, total:list.length, via:'scrollIntoView+wheel'};
})();
"""

# ===== LIKE HELPERS =====
JS_FORCE_LIKE = r"""
(function(){
  const centerY = window.innerHeight / 2;
  const rectCenter = (el) => { const r = el.getBoundingClientRect(); return {x:r.left+r.width/2, y:r.top+r.height/2, r}; };
  const dist2 = (a, b) => (a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y);
  const isVisible = el => { if(!el) return false; const r=el.getBoundingClientRect(); const s=getComputedStyle(el); return r.width>4 && r.height>4 && s.visibility!=='hidden' && s.display!=='none'; };
  const findNearest = (nodes, point) => { let best=null, bd=Infinity; for (const el of nodes){ if(!isVisible(el)) continue; const c=rectCenter(el); const d=dist2({x:c.x,y:c.y}, point); if (d < bd){ bd=d; best={el, center:c, d2:d}; } } return best; };

  const vids = Array.from(document.querySelectorAll('video'));
  if (!vids.length) return {ok:false, reason:'no-videos'};

  const target = vids.sort((a,b)=>{
    const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
    const da=Math.abs((ra.top+ra.height/2)-centerY), db=Math.abs((rb.top+rb.height/2)-centerY);
    return da-db;
  })[0];

  target.scrollIntoView({behavior:'smooth', block:'center'});

  const vC = rectCenter(target);
  const unlike = Array.from(document.querySelectorAll('svg[aria-label="Unlike"], button[aria-label="Unlike"]'));
  const nearUnlike = findNearest(unlike, vC);
  if (nearUnlike && Math.sqrt(nearUnlike.d2) < 700) return {ok:false, reason:'already-liked'};

  const likes = Array.from(document.querySelectorAll('svg[aria-label="Like"]'));
  const nearLike = findNearest(likes, vC);
  if (!nearLike || Math.sqrt(nearLike.d2) >= 700) return {ok:false, reason:'no-like-nearby'};

  const svg = nearLike.el;
  const btn = svg.closest('button') || svg.closest('[role="button"]') || svg;
  if (!btn || !isVisible(btn)) return {ok:false, reason:'no-like-button'};

  try { btn.click(); } catch(e) { return {ok:false, reason:'click-failed'}; }

  const verify = findNearest(Array.from(document.querySelectorAll('svg[aria-label="Unlike"], button[aria-label="Unlike"]')), vC);
  if (verify && Math.sqrt(verify.d2) < 700) return {ok:true, via:'nearest-heart', dist: Math.round(Math.sqrt(nearLike.d2))};
  return {ok:false, reason:'no-unlike-after-click'};
})();
"""

JS_SMART_LIKE = r"""(function(){ const centerY=window.innerHeight/2; const videos=Array.from(document.querySelectorAll('video')); if(!videos.length) return {ok:false,reason:'no-videos'}; const target=videos.sort((a,b)=>{ const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect(); const da=Math.abs((ra.top+ra.height/2)-centerY), db=Math.abs((rb.top+rb.height/2)-centerY); return da-db; })[0]; let scope=target.closest('article')||target.closest('[role=\"presentation\"]')||target.parentElement||document; const btns=[]; scope.querySelectorAll('button,[role=\"button\"],svg').forEach(el=>{ const al=(el.getAttribute&&(el.getAttribute('aria-label')||''))||''; const title=(el.querySelector&&el.querySelector('title')&&el.querySelector('title').textContent)||''; const txt=(el.textContent||'').toLowerCase(); const hint=(al+title+txt).toLowerCase(); if(/\\blike\\b/.test(hint)) btns.push(el.closest('button')||el); if(/\\bunlike\\b/.test(hint)) btns.push('already-liked'); }); if(btns.includes('already-liked')) return {ok:false,reason:'already-liked'}; for(const b of btns){ if(b&&b.click){ try{ b.click(); return {ok:true,via:'aria/title/text'} }catch(e){} } } return {ok:false,reason:'no-like-button'} })();"""

# ===== Home feed: smooth 20s scroller with NAV GUARD + CLICK BLOCKER =====
JS_SCROLL_HOME_FEED = r"""
(()=>{ 
  const T=20_000, r=(a,b)=>a+Math.random()*(b-a), ri=(a,b)=>Math.floor(r(a,b+1)), sl=ms=>new Promise(f=>setTimeout(f,ms));
  const root=()=>document.scrollingElement||document.documentElement||document.body;
  const focus=()=>{try{(document.elementFromPoint(innerWidth/2,innerHeight/2)||document.body).dispatchEvent(new MouseEvent("click",{bubbles:true}));document.body.focus();}catch{}};
  const closeModal=()=>{const m=document.querySelector('[role="dialog"],[aria-modal="true"]');if(m)document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}))};
  const closeStories=()=>{for(let i=0;i<2;i++){document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}))}};
  const relax=()=>{for(const el of [document.documentElement,document.body,document.querySelector('main,[role="main"]')].filter(Boolean)){const cs=getComputedStyle(el);if((cs.overflowY==='hidden'||cs.overflow==='hidden')&&el.scrollHeight>el.clientHeight+10){el.style.overflowY='auto';el.style.overflow='auto';}}};
  const ensureHome=()=>{ 
    const notFeed=/^\/(reel|p|explore|direct|accounts|stories|topics|likes|saved)\b/.test(location.pathname);
    if(location.pathname!=="/" || location.hash || location.search || notFeed){
      history.replaceState(null,"","/"); 
      try{ window.dispatchEvent(new PopStateEvent("popstate")); }catch(e){}
      if(location.pathname!=="/"){ try{ location.assign("/"); }catch(e){} }
    }
  };
  const findSc=()=>{const rt=root();if(rt.scrollHeight>rt.clientHeight+10)return rt;const c=new Set();const m=document.querySelector('main,[role="main"]');if(m){c.add(m);m.querySelectorAll('div,section').forEach(e=>c.add(e));}
    document.querySelectorAll('div,section').forEach((e,i)=>i<300&&c.add(e));
    for(const e of c){const s=getComputedStyle(e);if((s.overflowY==='auto'||s.overflowY==='scroll')&&e.scrollHeight>e.clientHeight+10)return e;}
    return rt};
  const wheel=(el,dy)=>{try{el.dispatchEvent(new WheelEvent('wheel',{deltaY:dy,bubbles:true,cancelable:true}));}catch{window.scrollBy(0,dy)}};
  const nudge=()=>{try{document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true}))}catch{}};
  const center=()=>{const m=document.querySelector('main,[role="main"]');if(!m)return;const A=[...m.querySelectorAll('article')];if(!A.length)return;const y=innerHeight/2;let best=A[0],bd=1e9;for(const a of A){const r=a.getBoundingClientRect(),d=Math.abs((r.top+r.height/2)-y);if(d<bd){bd=d;best=a}}try{best.scrollIntoView({behavior:'smooth',block:'center'})}catch{}};

  // Block anchor clicks during run to avoid accidental profile/story opens
  let clickBlocker = (e)=>{ 
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href')||'';
    if (/^\/(reel|p|explore|direct|accounts|stories|topics|likes|saved|[A-Za-z0-9_.]+\/?)$/.test(href)) {
      e.preventDefault(); e.stopPropagation();
    }
  };

  let run=true;window.__IG_STOP__=()=>{run=false; console.warn('⏹️ stopped'); try{window.removeEventListener('click',clickBlocker,true);}catch(e){}};

  (async()=>{
    console.log('▶️ smooth scroll 20s… stop: __IG_STOP__()');
    ensureHome();
    closeStories();
    closeModal();
    relax();
    focus();
    center();

    // install click blocker
    try{ window.addEventListener('click', clickBlocker, true); }catch(e){}

    let sc=findSc(),t0=performance.now();
      while(run && performance.now()-t0<T){
        ensureHome();
        closeStories();
        // burst - ONLY DOWN SCROLLING
        const down=true, steps=ri(5,9);
        for(let i=0;i<steps&&run;i++){
          const dy=ri(18,36); // always positive (down)
          const before=(sc.scrollTop??window.scrollY);
          wheel(sc,dy);
          if(Math.abs((sc.scrollTop??window.scrollY)-before)<1){try{sc.scrollTop=before+dy}catch{}}
          await sl(ri(12,22));
        }
        await sl(ri(180,360)); if(Math.random()<.18) await sl(ri(700,1200));
        if(Math.random()<.25) nudge();
        if(Math.random()<.22){center();await sl(ri(100,200))}
        if(Math.random()<.1){closeModal();relax();sc=findSc()}
      }

    try{ window.removeEventListener('click',clickBlocker,true); }catch(e){}
    console.log('✅ done');
  })();
})();
"""

# Stop helper to terminate the one-shot home scroller if needed
JS_STOP_HOME_SCROLL = r"""(()=>{ try{ if (window.__IG_STOP__) window.__IG_STOP__(); }catch(e){} return {ok:true, stopped: !!window.__IG_STOP__}; })();"""

JS_LIKE_HOME_POST = r"""(function(){
  const isInViewport = (el) => {
    const r = el.getBoundingClientRect();
    const h = (window.innerHeight || document.documentElement.clientHeight);
    return r.top >= 0 && r.left >= 0 && r.top < h*0.7 && r.bottom > h*0.3; // more central
  };

  const articles = Array.from(document.querySelectorAll('main article, article')).filter(isInViewport);
  if (articles.length === 0) return { ok: false, reason: 'no-posts' };

  const target = articles[Math.floor(Math.random() * Math.min(articles.length, 3))]; // bias to top 3

  const candidates = new Set();
  target.querySelectorAll('button[aria-label="Like"], svg[aria-label="Like"], [data-testid="like"]').forEach((el) => {
    let btn = el.tagName && el.tagName.toLowerCase() === 'button' ? el : el.closest('button');
    if (btn) candidates.add(btn);
  });

  target.querySelectorAll('svg[aria-label="Like"]').forEach(svg=>{
    const el = svg.closest('button') || svg.closest('[role="button"]') || svg;
    if (el) candidates.add(el);
  });

  target.querySelectorAll('svg title').forEach(t=>{
    if ((t.textContent||'').trim().toLowerCase()==='like'){
      const el = t.closest('button') || t.closest('[role="button"]') || t.closest('svg');
      if (el) candidates.add(el);
    }
  });

  const arr = Array.from(candidates);
  if (arr.length === 0) return { ok: false, reason: 'no-like-button' };

  const targetBtn = arr[Math.floor(Math.random() * arr.length)];
  try {
    targetBtn.click();
    return { ok: true, via: 'home-post' };
  } catch (e) {
    return { ok: false, reason: 'click-failed' };
  }
})();"""


async def perform_reels_warmup(
    ws_url: str,
    duration_sec: Optional[int] = None,  # total 60–90
    max_likes: Optional[int] = None,     # 0–2 skewed to 0–1
    down_bias: float = 0.88,
    min_wait: float = 0.8,
    max_wait: float = 2.2
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    COMPLETE WARMUP (kept name for backward compatibility):
      - Reels (first 60–70% of time), then Home (remaining).
      - Total duration: randomized 60–90s (to keep previous API semantics).
      - Likes: 0–2 total, skewed to 0–1.
    """
    if duration_sec is None:
        duration_sec = random.randint(60, 90)

    if max_likes is None:
        pool = [0] * 40 + [1] * 45 + [2] * 15
        max_likes = random.choice(pool)

    started = time.time()
    likes = 0
    moves = 0

    reels_duration = duration_sec * random.uniform(0.6, 0.7)
    home_duration = duration_sec - reels_duration

    async with CDPClient(ws_url) as cdp:
        sid = await cdp.get_page_session()

        # Land on home and enforce it
        await cdp.goto(sid, "https://www.instagram.com/", wait="domcontent")
        await asyncio.sleep(1.2)
        await cdp.eval(sid, JS_WARMUP_BOOT)
        await asyncio.sleep(0.2)
        await cdp.eval(sid, JS_ENSURE_HOME)

        yield {
            "type": "start",
            "mode": "warmup",
            "content": "home",
            "duration_sec": duration_sec,
            "max_likes": max_likes,
            "home_duration": home_duration,
            "reels_duration": reels_duration,
        }

        home_phase = True
        home_start_time = time.time()
        force_like_count = 0
        home_scroller_started = False

        while True:
            elapsed = time.time() - started

            # Phase switch?
            if home_phase and (time.time() - home_start_time) >= home_duration:
                if home_scroller_started:
                    await cdp.eval(sid, JS_STOP_HOME_SCROLL)
                    home_scroller_started = False

                home_phase = False
                yield {"type": "phase_switch", "from": "home", "to": "reels", "home_duration": home_duration}

                await cdp.goto(sid, "https://www.instagram.com/reels/", wait="domcontent")
                await asyncio.sleep(2.0)
                await cdp.eval(sid, JS_WARMUP_BOOT)
                await asyncio.sleep(0.4)
                yield {"type": "navigated", "to": "reels"}

            # Total time stop
            if elapsed >= duration_sec:
                if home_scroller_started:
                    await cdp.eval(sid, JS_STOP_HOME_SCROLL)
                    home_scroller_started = False

                yield {
                    "type": "done",
                    "reason": "duration",
                    "liked": likes,
                    "moves": moves,
                    "elapsed": round(elapsed, 1),
                    "phase": "home" if home_phase else "reels",
                }
                return

            if home_phase:
                # ===== HOME PHASE =====
                # Keep enforcing home (bounce back if navigated)
                await cdp.eval(sid, JS_ENSURE_HOME)

                if not home_scroller_started:
                    await cdp.eval(sid, JS_SCROLL_HOME_FEED)  # one-shot ~20s, with URL guard & click blocker
                    home_scroller_started = True
                    yield {"type": "home_scroller", "started": True, "note": "20s scroller running with nav guard"}

                yield {"type":"debug","message":f"HOME PHASE: elapsed={elapsed:.1f}s, left={home_duration - (time.time() - home_start_time):.1f}s, forced={force_like_count}"}

                # NO LIKING ON HOME PAGE - Just scrolling

                # Lightweight pacing; scroller is moving in-page
                await asyncio.sleep(random.uniform(0.8, 1.8))

                # Dwell sometimes
                if random.random() < 0.15:
                    dwell = random.uniform(3.0, 6.0)
                    await asyncio.sleep(dwell)
                    yield {"type": "dwell", "sec": round(dwell, 2)}

            else:
                # ===== REELS PHASE =====
                yield {"type":"debug","message":f"REELS PHASE: elapsed={elapsed:.1f}s, left={reels_duration - (elapsed - home_duration):.1f}s, forced={force_like_count}"}

                cur = await cdp.eval(sid, JS_FIND_CURRENT_REEL)
                yield {"type": "current", "result": cur}

                if random.random() < down_bias:
                    r = await cdp.eval(sid, JS_SCROLL_NEXT_REEL); direction = "down"
                else:
                    r = await cdp.eval(sid, JS_SCROLL_PREV_REEL); direction = "up"

                moves += 1
                yield {"type": "move", "direction": direction, "result": r, "moves": moves}

                if likes < max_likes and random.random() < 0.35:
                    lr = await cdp.eval(sid, JS_FORCE_LIKE)
                    yield {"type": "like_attempt", "result": lr}
                    if isinstance(lr, dict) and lr.get("ok"):
                        likes += 1
                        yield {"type": "liked", "count": likes}

                await asyncio.sleep(random.uniform(min_wait, max_wait))

                if random.random() < 0.18:
                    dwell = random.uniform(2.5, 5.5)
                    await asyncio.sleep(dwell)
                    yield {"type": "dwell", "sec": round(dwell, 2)}


async def perform_warmup(
    ws_url: str,
    total_sec: Optional[int] = None,     # 60–70
    reels_sec: Optional[int] = None,     # 30–40
    max_likes: Optional[int] = None,     # 0–2 (skewed 0–1)
    down_bias: float = 0.88,
    wait_reels: Tuple[float, float] = (0.7, 1.6),
    wait_home: Tuple[float, float] = (1.0, 2.0),
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    New wrapper with explicit timing. If your route calls this, it behaves like:
      - Reels 30–40s then Home 20–30s (total 60–70s).
    """
    if total_sec is None:
        total_sec = random.randint(60, 70)
    if reels_sec is None:
        reels_sec = random.randint(30, 40)

    async for ev in perform_reels_warmup(
        ws_url=ws_url,
        duration_sec=total_sec,
        max_likes=max_likes,
        down_bias=down_bias,
        min_wait=wait_reels[0],
        max_wait=wait_reels[1],
    ):
        yield ev
