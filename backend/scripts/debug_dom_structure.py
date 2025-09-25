#!/usr/bin/env python3
"""
Debug script to extract DOM structure from Instagram's followers/following modal
to understand the actual structure for username extraction.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.actions import CDPClient

async def debug_dom_structure():
    """Debug DOM structure in Instagram modal"""
    
    # Debug JS to extract DOM structure
    JS_DEBUG_DOM = r"""
    (function(){
      const modal = document.querySelector('div[role="dialog"]');
      if(!modal) return {error: 'no-modal'};
      
      const result = {
        modalFound: true,
        modalClasses: modal.className,
        modalId: modal.id,
        allLis: [],
        allButtons: [],
        allLinks: [],
        allSpans: []
      };
      
      // Get all li elements
      const lis = Array.from(modal.querySelectorAll('li'));
      for(let i = 0; i < Math.min(lis.length, 5); i++) {
        const li = lis[i];
        const liInfo = {
          index: i,
          classes: li.className,
          id: li.id,
          role: li.getAttribute('role'),
          innerHTML: li.innerHTML.substring(0, 500) // truncate for readability
        };
        result.allLis.push(liInfo);
        
        // Get buttons in this li
        const buttons = Array.from(li.querySelectorAll('button, div[role="button"]'));
        for(const btn of buttons) {
          result.allButtons.push({
            liIndex: i,
            text: btn.innerText,
            classes: btn.className,
            ariaLabel: btn.getAttribute('aria-label'),
            type: btn.tagName
          });
        }
        
        // Get links in this li
        const links = Array.from(li.querySelectorAll('a'));
        for(const link of links) {
          result.allLinks.push({
            liIndex: i,
            href: link.getAttribute('href'),
            text: link.innerText,
            classes: link.className
          });
        }
        
        // Get spans in this li
        const spans = Array.from(li.querySelectorAll('span'));
        for(const span of spans) {
          result.allSpans.push({
            liIndex: i,
            text: span.innerText,
            classes: span.className,
            parentTag: span.parentElement?.tagName
          });
        }
      }
      
      return result;
    })();
    """
    
    # Get profile from command line or use default
    profile_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    target_user = sys.argv[2] if len(sys.argv) > 2 else "nike"
    
    print(f"Debugging DOM structure for profile {profile_id}, target: {target_user}")
    
    # Get profile info
    from app.db.session import get_db
    from app.models.profile import Profile
    
    db = next(get_db())
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        print(f"Profile {profile_id} not found")
        return
    
    ws_url = profile.websocket_url
    print(f"Using WebSocket URL: {ws_url}")
    
    async with CDPClient(ws_url) as cdp:
        session_id = await cdp.get_page_session()
        
        # Navigate to target profile
        await cdp.goto(session_id, f"https://www.instagram.com/{target_user}/", wait="domcontent")
        await asyncio.sleep(2)
        
        # Open followers modal
        await cdp.eval(session_id, """
        (function(){
          const link = document.querySelector('a[href$="/followers/"]');
          if(link) {
            link.click();
            return {ok: true};
          }
          return {ok: false, error: 'followers-link-not-found'};
        })();
        """)
        
        await asyncio.sleep(3)  # Wait for modal to load
        
        # Extract DOM structure
        dom_info = await cdp.eval(session_id, JS_DEBUG_DOM)
        
        print("\n=== DOM STRUCTURE DEBUG ===")
        print(json.dumps(dom_info, indent=2))
        
        # Save to file for analysis
        with open("dom_debug_output.json", "w") as f:
            json.dump(dom_info, f, indent=2)
        
        print(f"\nDebug output saved to dom_debug_output.json")

if __name__ == "__main__":
    asyncio.run(debug_dom_structure())
