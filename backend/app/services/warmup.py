import asyncio
import time
import random
from typing import AsyncGenerator, Dict, Any

from .actions import CDPClient


JS_SCROLL_FEED = r"""
(function(){
  // Attempt to scroll the main feed gently
  const scroller = document.scrollingElement || document.body;
  const before = (scroller && scroller.scrollTop) || 0;
  let scrolled = false;
  try {
    scroller.scrollTop = before + (100 + Math.floor(Math.random() * 150));
    scrolled = (scroller.scrollTop > before);
  } catch(e) {}

  if(!scrolled) {
    try {
      window.scrollBy(0, 150);
      scrolled = true;
    } catch(e) {}
  }

  try {
    const we = new WheelEvent('wheel', { deltaY: 120, bubbles: true, cancelable: true });
    window.dispatchEvent(we);
  } catch(e) {}

  const after = (scroller && scroller.scrollTop) || 0;
  return { ok: (after > before), before, after };
})();
"""


JS_LIKE_VISIBLE = r"""
(function(){
  // Find visible Like buttons on posts and click one
  // Heuristics: buttons with aria-label="Like" or SVG with aria-label
  const isInViewport = (el) => {
    const r = el.getBoundingClientRect();
    return r.top >= 0 && r.left >= 0 && r.bottom <= (window.innerHeight || document.documentElement.clientHeight);
  };

  const candidates = [];
  document.querySelectorAll('button[aria-label="Like"], svg[aria-label="Like"]').forEach((el) => {
    let btn = el.tagName.toLowerCase() === 'button' ? el : el.closest('button');
    if (btn && isInViewport(btn)) candidates.push(btn);
  });

  if (candidates.length === 0) return { ok: false, reason: 'no-like-found' };
  const target = candidates[Math.floor(Math.random() * candidates.length)];
  try {
    target.click();
    return { ok: true };
  } catch (e) {
    return { ok: false, reason: 'click-failed' };
  }
})();
"""

JS_DEBUG_REEL_CONTROLS = r"""
(function(){
  const isInViewport = (el) => {
    const r = el.getBoundingClientRect();
    return r.top >= 0 && r.left >= 0 && r.bottom <= (window.innerHeight || document.documentElement.clientHeight);
  };
  const videos = Array.from(document.querySelectorAll('video'));
  const visible = videos.filter(isInViewport);
  if (!visible.length) return { ok:false, reason:'no-video' };
  visible.sort((a,b)=>{
    const ca = Math.abs(a.getBoundingClientRect().top + a.clientHeight/2 - window.innerHeight/2);
    const cb = Math.abs(b.getBoundingClientRect().top + b.clientHeight/2 - window.innerHeight/2);
    return ca - cb;
  });
  const v = visible[0];
  const scope = v.closest('article, div') || document.body;
  const buttons = Array.from(scope.querySelectorAll('button, [role="button"], svg'))
    .slice(0, 30)
    .map(el => ({
      tag: el.tagName,
      role: el.getAttribute('role')||'',
      aria: el.getAttribute('aria-label')||'',
      testid: el.getAttribute('data-testid')||'',
      class: el.className||'',
      title: (el.querySelector && (el.querySelector('title')||{}).textContent) || '',
      text: (el.textContent||'').trim().slice(0,80)
    }));
  return { ok:true, buttons };
})();
"""


JS_NEXT_REEL = r"""
(function(){
  const presses = 1 + Math.floor(Math.random() * 2); // 1-2 arrow downs
  const pressArrowDown = () => {
    const down = new KeyboardEvent('keydown', { key: 'ArrowDown', code: 'ArrowDown', which: 40, keyCode: 40, bubbles: true, cancelable: true });
    const up = new KeyboardEvent('keyup', { key: 'ArrowDown', code: 'ArrowDown', which: 40, keyCode: 40, bubbles: true, cancelable: true });
    document.dispatchEvent(down);
    document.dispatchEvent(up);
  };

  try {
    // Try to focus the main container to ensure key events are handled
    const main = document.querySelector('main') || document.body;
    if (main && typeof main.focus === 'function') main.focus();

    // Send ArrowDown 1-2 times
    for (let i=0;i<presses;i++) setTimeout(pressArrowDown, i*120);

    // Fallbacks to ensure motion if key events are ignored
    try {
      const dy = 200 + Math.floor(Math.random()*300); // 200-500px
      const we = new WheelEvent('wheel', { deltaY: dy, bubbles: true, cancelable: true });
      window.dispatchEvent(we);
    } catch(e) {}

    // Try to scroll next visible video into view as a last resort
    try {
      const videos = Array.from(document.querySelectorAll('video'));
      const center = (el) => {
        const r = el.getBoundingClientRect();
        return Math.abs(r.top + r.height/2 - window.innerHeight/2);
      };
      const sorted = videos.sort((a,b)=> center(a) - center(b));
      const current = sorted[0];
      const next = sorted[1] || videos[1];
      if (next && next.scrollIntoView) next.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch(e) {}

    return { ok: true };
  } catch (e) {
    return { ok: false, error: 'key-event-failed' };
  }
})();
"""

JS_LIKE_REEL = r"""
(function(){
  const isInViewport = (el) => {
    const r = el.getBoundingClientRect();
    return r.top >= 0 && r.left >= 0 && r.bottom <= (window.innerHeight || document.documentElement.clientHeight);
  };

  // Locate centered/visible reel video
  const videos = Array.from(document.querySelectorAll('video'));
  const visible = videos.filter(isInViewport);
  let targetVideo = null;
  if (visible.length > 0) {
    visible.sort((a,b)=>{
      const ca = Math.abs(a.getBoundingClientRect().top + a.clientHeight/2 - window.innerHeight/2);
      const cb = Math.abs(b.getBoundingClientRect().top + b.clientHeight/2 - window.innerHeight/2);
      return ca - cb;
    });
    targetVideo = visible[0];
  }

  if (!targetVideo) return { ok:false, reason:'no-video' };

  // Nudge controls to appear by moving mouse over the video center
  try {
    const r = targetVideo.getBoundingClientRect();
    const cx = r.left + r.width/2;
    const cy = r.top + r.height/2;
    const mm = new MouseEvent('mousemove', { clientX: cx, clientY: cy, bubbles: true, cancelable: true });
    document.dispatchEvent(mm);
  } catch(e) {}

  // Find the actionable Like button in vicinity of the reel controls
  const scope = targetVideo.closest('article, div') || document.body;

  // Gather candidates: explicit buttons first
  const candidates = [];
  scope.querySelectorAll('[aria-label="Like"], button[aria-label="Like this post"], [data-testid="like"], [role="button"][data-testid="like"]').forEach(el=>candidates.push({el, src:'aria/button'}));

  // Then SVG hearts (your provided class and generic aria-label)
  scope.querySelectorAll('svg.x1lliihq.x1n2onr6.xyb1xck[aria-label="Like"], svg[aria-label="Like"]').forEach(svg=>{
    const el = svg.closest('button') || svg.closest('[role="button"]') || svg;
    candidates.push({el, src:'svg-aria'});
  });

  // Finally, <title>Like</title> under svg
  scope.querySelectorAll('svg title').forEach(t=>{
    if ((t.textContent||'').trim().toLowerCase()==='like'){
      const el = t.closest('button') || t.closest('[role="button"]') || t.closest('svg');
      if (el) candidates.push({el, src:'svg-title'});
    }
  });

  // Global fallback: search the whole document for the provided heart svg or aria-label
  if (candidates.length === 0) {
    const global = [];
    document.querySelectorAll('svg.x1lliihq.x1n2onr6.xyb1xck[aria-label="Like"], svg[aria-label="Like"]').forEach(svg=>{
      const el = svg.closest('button') || svg.closest('[role="button"]') || svg;
      global.push({el, src:'global-svg'});
    });
    global.forEach(x=>candidates.push(x));
  }

  // Rank by proximity to target video center
  const centerDist = (el) => {
    const r = el.getBoundingClientRect();
    const cy = r.top + r.height/2;
    return Math.abs(cy - (window.innerHeight/2));
  };
  candidates.sort((a,b)=> centerDist(a.el) - centerDist(b.el));

  for (const c of candidates){
    const el = c.el;
    const label = (el.getAttribute && el.getAttribute('aria-label')) ? el.getAttribute('aria-label').toLowerCase() : '';
    if (label.includes('unlike')) continue;
    try {
      el.click();
      return { ok:true, via:'button', src:c.src };
    } catch(e) {
      // try parent button
      const btn = el.closest && (el.closest('button') || el.closest('[role="button"]'));
      if (btn) {
        try { btn.click(); return {ok:true, via:'button', src:c.src+'-closest'}; } catch(e2) {}
      }
    }
  }

  return { ok:false, reason:'no-like-button' };
})();
"""


async def perform_warmup_stream(ws_url: str, duration_sec: int = 90, max_likes: int = 5, content: str = "home") -> AsyncGenerator[Dict[str, Any], None]:
  """
  Open Instagram home feed, gently scroll with randomized delays, and like a
  few posts. Stream progress events suitable for SSE.
  """
  started_at = time.time()
  # If caller requests random likes, draw a skewed random in 0..5 (favor 0-1)
  if max_likes is None or max_likes == -1:
    pool = [0]*50 + [1]*30 + [2]*10 + [3]*5 + [4]*3 + [5]*2
    max_likes = random.choice(pool)
  liked = 0
  scrolled = 0

  async with CDPClient(ws_url) as cdp:
    sid = await cdp.get_page_session()

    # Go to selected content
    target_url = "https://www.instagram.com/" if content != "reels" else "https://www.instagram.com/reels/"
    await cdp.goto(sid, target_url, wait="domcontent")
    await asyncio.sleep(1.5)

    yield {"type": "start", "mode": "warmup", "content": content, "duration_sec": duration_sec, "max_likes": max_likes}
    if content == "reels":
      try:
        dbg = await cdp.eval(sid, JS_DEBUG_REEL_CONTROLS)
        yield {"type": "controls_debug", "data": dbg}
      except Exception:
        pass

    while True:
      # Stop by duration or likes cap
      if (time.time() - started_at) >= duration_sec:
        yield {"type": "done", "reason": "duration", "liked": liked, "scrolled": scrolled}
        return
      if max_likes and liked >= max_likes:
        yield {"type": "done", "reason": "likes", "liked": liked, "scrolled": scrolled}
        return

      if content == "reels":
        # Randomly attempt like on current reel (prefer the heart button; no dblclick)
        if (not max_likes or liked < max_likes) and random.random() < 0.6:
          attempt = await cdp.eval(sid, JS_LIKE_REEL)
          yield {"type": "like_attempt", "result": attempt}
          if isinstance(attempt, dict) and attempt.get("ok"):
            liked += 1
            yield {"type": "like", "liked": liked, "via": attempt.get('via')}
            await asyncio.sleep(2.0 + random.random() * 1.5)

        # Advance reels: press ArrowDown 1-2 times with either quick or slow cadence
        advance_times = 1 + (1 if random.random() < 0.4 else 0)  # 40% chance do 2 steps
        for _ in range(advance_times):
          next_result = await cdp.eval(sid, JS_NEXT_REEL)
          scrolled += 1
          yield {"type": "next_reel", "count": scrolled, "result": next_result}
          # Cadence: 60% quick (0.3-0.8s), 40% slow (2.8-3.6s)
          if random.random() < 0.6:
            await asyncio.sleep(0.3 + random.random() * 0.5)
          else:
            await asyncio.sleep(2.8 + random.random() * 0.8)
      else:
        # Home feed warmup
        like_result = await cdp.eval(sid, JS_LIKE_VISIBLE)
        if isinstance(like_result, dict) and like_result.get("ok"):
          liked += 1
          yield {"type": "like", "liked": liked}
          await asyncio.sleep(2.0 + random.random() * 1.5)
        else:
          scroll_result = await cdp.eval(sid, JS_SCROLL_FEED)
          scrolled += 1
          yield {"type": "scroll", "scrolled": scrolled, "result": scroll_result}
          await asyncio.sleep(1.0 + random.random() * 1.2)


