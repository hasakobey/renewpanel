const {chromium}=require('C:/Users/Hasan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});const page=await browser.newPage();let errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8897/fixture.html');await page.waitForTimeout(900);
assert.equal(await page.locator('#dashKpis>.kpi').count(),12);assert.equal(await page.locator('#dashKpis>.kpi>.ds-icon').count(),12);
const baseline=await page.locator('#dashKpis>.kpi>strong').allTextContents();assert.ok(baseline.includes('₺96.438'));
for(const width of [1440,1024,768,390,360]){await page.setViewportSize({width,height:1000});await page.waitForTimeout(150);
 const overflow=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth,dashboard:document.querySelector('#dashboard').getBoundingClientRect().width}));
 assert.ok(overflow.document<=width+1,JSON.stringify({width,...overflow}));
 await page.screenshot({path:`work/dashboard_stitch/test-${width}.png`,fullPage:true});if(width===390)await page.screenshot({path:'work/dashboard_stitch/mobile-top.png'});
 assert.deepEqual(await page.locator('#dashKpis>.kpi>strong').allTextContents(),baseline);
}
assert.equal(await page.locator('.ds-profit-bar i').first().evaluate(x=>x.style.width),'100%');
await page.locator('#dashboard .hero button').first().click();assert.ok(await page.locator('#modal.show').isVisible());await page.locator('.modalhead button').click();
await page.evaluate(()=>{const d={...fixtureData,sales_count:0,sales_revenue:0,sales_net_profit:0,sales_performance_profit:0,avg_sale_profit:0,avg_sale_sks:0,profitable_sales:0,losing_sales:0,critical_stock:[],top_sales:[],loss_sales:[],monthly_trend:[]};renderDashboard(d)});await page.waitForTimeout(300);assert.equal(await page.locator('#dashKpis>.kpi').count(),12);assert.equal(await page.locator('#dashKpis>.kpi>.ds-icon').count(),12);
await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('#dashKpis>.kpi').first().evaluate(x=>getComputedStyle(x).animationName),'none');
assert.deepEqual(errors,[]);console.log('PASS: 5 viewport widths, 12 KPI values preserved, unique icons, empty sales period, reduced motion, no JS exceptions');await browser.close();})().catch(e=>{console.error(e);process.exit(1)});
