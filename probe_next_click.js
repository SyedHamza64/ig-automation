(function () {
    const root = document.querySelector('[role="dialog"]') || document;
  
    function findNextButton() {
      const tries = [
        '[role="dialog"] button svg[aria-label="Next"]',
        '[role="dialog"] button[aria-label="Next"]',
        '[role="dialog"] div[role="button"] svg[aria-label="Next"]',
        '[role="dialog"] a[aria-label="Next"]',
        'svg[aria-label="Next"]',
        'button[aria-label="Next"]',
        'div[role="button"] svg[aria-label="Next"]',
      ];
      for (const sel of tries) {
        const el = root.querySelector(sel);
        if (el) return el.closest('button,[role="button"],a') || el;
      }
      return null;
    }
  
    const btn = findNextButton();
    if (btn) {
      btn.click();
      return { clicked: true, method: 'button' };
    }
  
    // Fallback: simulate ArrowRight keypress (IG usually listens for this)
    try {
      const ev1 = new KeyboardEvent('keydown', { key: 'ArrowRight', code: 'ArrowRight', bubbles: true });
      const ev2 = new KeyboardEvent('keyup',   { key: 'ArrowRight', code: 'ArrowRight', bubbles: true });
      document.dispatchEvent(ev1);
      document.dispatchEvent(ev2);
      return { clicked: true, method: 'arrowRight' };
    } catch (e) {
      return { clicked: false, method: 'none', error: String(e) };
    }
  })()

  