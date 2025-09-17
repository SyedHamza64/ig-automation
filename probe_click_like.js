(function () {
    const root = document.querySelector('[role="dialog"]') || document;
    const buttons = Array.from(root.querySelectorAll('button, div[role="button"]'));
    function findBtn() {
      for (const b of buttons) {
        const aria = (b.getAttribute('aria-label') || '').toLowerCase();
        const svgAl = (b.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
        if (aria.includes('like') || svgAl.includes('like')) return b;
        if (aria.includes('unlike') || svgAl.includes('unlike')) return b;
      }
      return null;
    }
    const btn = findBtn();
    if (!btn) return { clicked:false, reason:'notfound' };
  
    const aria = (btn.getAttribute('aria-label') || btn.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
    if (aria.includes('unlike')) return { clicked:false, status:'already_liked' };
  
    btn.click();
    return { clicked:true, status:'liked' };
  })()
  