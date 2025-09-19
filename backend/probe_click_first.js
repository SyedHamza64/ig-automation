(function () {
    const sel = 'a[href*="/reel/"], a[href*="/p/"]'; // matches /reel/ and /instagram/reel/
    const a = document.querySelector(sel);
    if (!a) return { clicked: false, reason: "no_thumb" };
    a.click();
    return { clicked: true, href: a.getAttribute("href") };
  })()
  