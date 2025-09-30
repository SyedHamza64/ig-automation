// 20-Second Instagram Home Page Scroll Test
// Copy and paste this into browser console on https://www.instagram.com/

(() => {
  console.log('🧪 Starting 20-second Instagram Home Page Scroll Test...');
  
  let isRunning = true;
  let testCount = 0;
  
  // Stop function
  window.stopScrollTest = () => {
    isRunning = false;
    console.log('⏹️ Scroll test stopped');
  };
  
  const testScroll = () => {
    const down = Math.random() < 0.85;
    const steps = 2 + Math.floor(Math.random()*3);
    const deltas = [];
    
    for (let i=0;i<steps;i++){
      const base = 120 + Math.floor(Math.random()*120);
      deltas.push(down ? base : -base);
    }

    console.log(`📱 Test ${++testCount}: ${down ? 'DOWN' : 'UP'}, ${steps} steps`);

    // Center articles
    try {
      const main = document.querySelector('main,[role="main"]');
      const arts = main ? Array.from(main.querySelectorAll('article')) : [];
      if (arts.length){
        const centerY = window.innerHeight/2;
        let best = arts[0], bd = 1e9;
        for (const a of arts){
          const r = a.getBoundingClientRect();
          const cy = r.top + r.height/2;
          const d = Math.abs(cy - centerY);
          if (d < bd){ bd = d; best = a; }
        }
        best.scrollIntoView({behavior:'smooth', block:'center'});
      }
    } catch(e){}

    // Dispatch wheel events
    try {
      const root = (document.scrollingElement||document.body);
      deltas.forEach(dy => {
        const ev = new WheelEvent('wheel', {deltaY: dy, bubbles:true, cancelable:true});
        root.dispatchEvent(ev);
      });
    } catch(e){}

    return {ok:true, direction: down?'down':'up', bursts: deltas};
  };

  // Run continuous test for 20 seconds
  const run20sTest = async () => {
    const startTime = Date.now();
    const duration = 20000; // 20 seconds
    
    console.log('🚀 Starting 20-second continuous scroll test...');
    console.log('💡 Run stopScrollTest() to stop early');
    
    while (isRunning && (Date.now() - startTime) < duration) {
      testScroll();
      
      // Wait 1-3 seconds between scrolls
      const waitTime = 1000 + Math.random() * 2000;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      // Show progress
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      const remaining = Math.round((duration - (Date.now() - startTime)) / 1000);
      if (elapsed % 5 === 0) {
        console.log(`⏱️ ${elapsed}s elapsed, ${remaining}s remaining`);
      }
    }
    
    console.log(`✅ 20-second test completed! Ran ${testCount} scroll tests`);
    console.log('📊 Final stats:', {
      totalTests: testCount,
      duration: '20s',
      avgInterval: Math.round(20000 / testCount) + 'ms'
    });
  };

  // Start the test
  run20sTest();
  
  console.log('🎯 Test started! Watch the page scroll naturally for 20 seconds');
  console.log('🛑 To stop early: stopScrollTest()');
})();

