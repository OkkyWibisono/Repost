const puppeteer = require('puppeteer-core');

async function locateElement() {
   const args = process.argv.slice(2);
   if (args.length < 2) {
      console.error(JSON.stringify({ error: "Usage: node locate.js <port> <selector>" }));
      process.exit(1);
   }

   const port = args[0];
   const selector = args[1];
   const browserURL = `http://127.0.0.1:${port}`;

   let browser;
   try {
      browser = await puppeteer.connect({
         browserURL: browserURL,
         defaultViewport: null
      });

      // Find the active tab (pages() returns all pages)
      const pages = await browser.pages();

      // Simple heuristic: take the first page that is not about:blank, or just the first one.
      // Better: Filter for x.com if possible, or just use the last opened one (often the active one).
      // Let's try to find the one with x.com or just the first visible one.
      let page = pages[0];
      for (const p of pages) {
         const url = p.url();
         if (url && url !== 'about:blank') {
            const state = await p.evaluate(() => document.visibilityState);
            if (state === 'visible') {
               page = p;
               break;
            }
         }
      }

      if (!page) {
         console.error(JSON.stringify({ error: "No valid page found" }));
         browser.disconnect();
         process.exit(1);
      }

      // Wait for element to be present (short timeout)
      try {
         await page.waitForSelector(selector, { timeout: 2000 });
      } catch (e) {
         // Ignore timeout, we will check if it exists next
      }

      const element = await page.$(selector);

      if (!element) {
         console.log(JSON.stringify({ error: `Element not found: ${selector}` }));
      } else {
         const box = await element.boundingBox();
         if (box) {
            // Collect window metrics for coordinate conversion
            const metrics = await page.evaluate(() => {
               return {
                  dpr: window.devicePixelRatio || 1,
                  screenX: window.screenX,
                  screenY: window.screenY,
                  outerHeight: window.outerHeight,
                  innerHeight: window.innerHeight,
                  outerWidth: window.outerWidth,
                  innerWidth: window.innerWidth
               };
            });

            const x = Math.round(box.x + box.width / 2);
            const y = Math.round(box.y + box.height / 2);

            console.log(JSON.stringify({
               x,
               y,
               ...metrics
            }));
         } else {
            console.log(JSON.stringify({ error: "Element has no bounding box (hidden?)" }));
         }
      }

   } catch (err) {
      console.error(JSON.stringify({ error: err.message }));
   } finally {
      if (browser) {
         browser.disconnect();
      }
   }
}

locateElement();
