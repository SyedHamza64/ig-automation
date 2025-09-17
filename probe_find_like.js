(function () {
    const root = document.querySelector('[role="dialog"]') || document;
    const buttons = Array.from(root.querySelectorAll('button, div[role="button"]'));
    const find = () => buttons.find(b => {
      const al = (b.getAttribute('aria-label') || '').toLowerCase();
      if (al.includes('like') || al.includes('unlike')) return true;
      const svg = b.querySelector('svg');
      const svgAl = (svg?.getAttribute?.('aria-label') || '').toLowerCase();
      return svgAl.includes('like') || svgAl.includes('unlike');
    });
    const btn = find();
    if (!btn) return { found:false };
  
    const aria = (btn.getAttribute('aria-label') || btn.querySelector('svg')?.getAttribute('aria-label') || '').toLowerCase();
    const already = aria.includes('unlike'); // IG shows "Unlike" when it's already liked
    return { found:true, aria, already };
  })()
  