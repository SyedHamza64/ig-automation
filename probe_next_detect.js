(function () {
    const root = document.querySelector('[role="dialog"]') || document;
  
    // candidates that commonly appear on IG
    const candidates = [
      '[role="dialog"] button svg[aria-label="Next"]',
      '[role="dialog"] button[aria-label="Next"]',
      '[role="dialog"] div[role="button"] svg[aria-label="Next"]',
      '[role="dialog"] a[aria-label="Next"]',
      'svg[aria-label="Next"]',                 // fallback if not inside dialog
      'button[aria-label="Next"]',
      'div[role="button"] svg[aria-label="Next"]'
    ];
  
    let el = null, sel = null;
    for (const c of candidates) {
      el = root.querySelector(c);
      if (el) { sel = c; break; }
    }
  
    return { found: !!el, selector: sel || null };
  })()
  