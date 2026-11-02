import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { startFixture } from './runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH ||= path.join(here, '.cache', 'browsers');
const { chromium } = await import('playwright');
const output = path.join(root, '.validation-runtime-' + new Date().toISOString().replaceAll(':', '-') + '-' + randomUUID().slice(0, 6));
await fs.mkdir(output);
await fs.mkdir(path.join(output, 'screenshots/before'), {recursive:true});
await fs.mkdir(path.join(output, 'screenshots/after'), {recursive:true});
const result = {schema_version:1,started_at:new Date().toISOString(),complete:false,engine:'Real WordPress / PHP.wasm / SQLite / Chromium',before:[],after:[],errors:[]};
await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(result,null,2));
let fixture, browser;
const pairs=[];
const oracle=JSON.parse(await fs.readFile(path.join(here,'oracle.json'),'utf8'));
try {
  fixture=await startFixture();
  result.site_url=fixture.url;result.versions=fixture.config;
  browser=await chromium.launch({headless:true});
  const checks=[
    {id:'CONTACT-001',route:'/checkpoint-fixture/',state:'contact submitted with a valid synthetic email',fixture:'editorial contact form',async observe(page){
      await page.getByLabel('Email',{exact:true}).fill('qa@example.test');
      const response=page.waitForResponse(r=>r.url().includes('contact')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'Send message',exact:true}).click();
      const reply=await response;
      await page.locator('#message').filter({hasText:/saved|failed/}).waitFor();
      const message=await page.locator('#message').textContent();
      return {pass:reply.ok()&&message==='Message saved.',observation:{http_status:reply.status(),message}};
    }},
    {id:'CART-001',route:'/checkpoint-fixture/catalogue/',state:'one product added once',fixture:'oak notebook, initially empty cart',async observe(page){
      const response=page.waitForResponse(r=>r.url().includes('cart')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'Add to cart',exact:true}).click();
      const reply=await response;
      await page.locator('#cart').filter({hasText:/Cart: [12]/}).waitFor();
      const quantity=await page.locator('#cart').textContent();
      return {pass:reply.ok()&&quantity==='Cart: 1',observation:{http_status:reply.status(),quantity}};
    }},
    {id:'RESP-001',route:'/checkpoint-fixture/catalogue/',mobile:true,state:'catalogue before adding product',fixture:'oak notebook, initially empty cart',async observe(page){
      const visible=await page.getByRole('button',{name:'Add to cart',exact:true}).isVisible();
      return {pass:visible,observation:{button_visible:visible,viewport:page.viewportSize()}};
    }},
    {id:'PHP-001',route:'/checkpoint-fixture/fatal/',state:'PHP page loaded',fixture:'dedicated availability route',async observe(page,response){
      const heading=await page.locator('h1').allTextContents();
      return {pass:response.status()===200&&heading.includes('PHP route ready'),observation:{http_status:response.status(),heading}};
    }},
    {id:'SEARCH-001',route:'/checkpoint-fixture/',state:'matching article search',fixture:'Oak field notes article',async observe(page){
      await page.getByLabel('Search articles',{exact:true}).fill('a');
      let pending=page.waitForResponse(r=>r.url().includes('search')&&r.request().method()==='GET');
      await page.getByRole('button',{name:'Search',exact:true}).click();
      const invalid=await pending;
      await page.locator('#results').filter({hasText:'Enter at least two characters.'}).waitFor();
      await page.getByLabel('Search articles',{exact:true}).fill('oak');
      pending=page.waitForResponse(r=>r.url().includes('search')&&r.request().method()==='GET');
      await page.getByRole('button',{name:'Search',exact:true}).click();
      const valid=await pending;
      await page.locator('#results').filter({hasText:'Oak field notes'}).waitFor();
      const title=await page.locator('#results').textContent();
      return {pass:invalid.status()===400&&valid.ok()&&title==='Oak field notes',observation:{short_query_status:invalid.status(),matching_status:valid.status(),title}};
    }}
  ];
  for(const phase of ['before','after']){
    await fixture.variant(phase==='before'?'healthy':'broken');
    for(const check of checks){
      const viewport=check.mobile?{width:375,height:812}:{width:1100,height:850};
      const context=await browser.newContext({viewport,deviceScaleFactor:1,locale:'en-US',reducedMotion:'reduce'});
      await context.route('**/*',route=>{
        const requested=new URL(route.request().url());
        return requested.origin===fixture.url?route.continue():route.abort();
      });
      const page=await context.newPage();page.setDefaultTimeout(12000);
      const response=await page.goto(fixture.url+check.route,{waitUntil:'networkidle'});
      const observed=await check.observe(page,response);
      const imagePath='screenshots/'+phase+'/'+check.id+'.png';
      await page.screenshot({path:path.join(output,imagePath),animations:'disabled'});
      const capture={path:imagePath,sha256:createHash('sha256').update(await fs.readFile(path.join(output,imagePath))).digest('hex'),
        url:page.url(),role:'Anonymous',viewport:{...viewport,device_scale_factor:1},locale:'en-US',state:check.state,fixture:check.fixture,
        captured_at:new Date().toISOString(),provenance:{run_id:phase+'-fixture',evidence_path:imagePath}};
      const row={id:check.id,status:observed.pass?'PASS':'FAIL',...observed,capture};
      result[phase].push(row);
      if(phase==='before')pairs.push({id:check.id,test_ids:[check.id],caption:check.id+' observed before and after fixture change',before:capture});
      else pairs.find(p=>p.id===check.id).after=capture;
      await context.close();
      await fs.writeFile(path.join(output,'results.json'),JSON.stringify(result,null,2));
    }
  }
  await fs.writeFile(path.join(output,'log-excerpt.txt'),await fixture.log());
  assert(result.before.every(r=>r.status==='PASS'),'Healthy fixture must pass all checks');
  const failed=result.after.filter(r=>r.status==='FAIL').map(r=>r.id).sort();
  assert.deepEqual(Object.fromEntries(result.before.map(r=>[r.id,r.status])),oracle.before,'Healthy observed results must match public expectations');
  assert.deepEqual(Object.fromEntries(result.after.map(r=>[r.id,r.status])),oracle.after,'Observed failures/controls must match controller oracle');
  await fs.writeFile(path.join(output,'comparison-input.json'),JSON.stringify({schema_version:1,pairs},null,2));
  const compare=spawnSync(process.env.PYTHON || 'python',[path.join(root,'scripts/visual_compare.py'),path.join(output,'comparison-input.json'),'--output',path.join(output,'visual-review')],{cwd:root,windowsHide:true,encoding:'utf8'});
  if(compare.status!==0)throw new Error('Visual helper failed: '+compare.stdout+compare.stderr);
  result.visual_helper_output=compare.stdout.trim();
  const viewer=await browser.newPage({viewport:{width:1280,height:900}});
  const unexpected=[];
  viewer.on('request',request=>{if(/^https?:/.test(request.url()))unexpected.push(request.url());});
  await viewer.goto(pathToFileURL(path.join(output,'visual-review/index.html')).href);
  assert(await viewer.locator('img').count()>0,'Viewer must contain evidence images');
  assert(await viewer.locator('img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0)),'All viewer images must load');
  const slider=viewer.locator('input[type=range]').first();
  await slider.fill('25');await slider.dispatchEvent('input');
  const cut=await viewer.locator('.slider').first().evaluate(element=>element.style.getPropertyValue('--cut'));
  assert(cut.includes('25'),'Reveal slider must change its visual cut position');
  assert.deepEqual(unexpected,[],'Offline viewer must make no remote requests');
  await viewer.evaluate(()=>window.scrollTo(0,0));
  await viewer.screenshot({path:path.join(output,'viewer-preview.png'),fullPage:false});
  result.viewer={images_loaded:true,slider_works:true,remote_requests:unexpected.length};
  result.checks_passed=true;
}catch(error){
  result.errors.push(error.stack||String(error));process.exitCode=1;console.error(error);
}finally{
  result.cleanup={status:'Complete',notes:[]};
  for(const [name,resource] of [['browser',browser],['fixture',fixture]]){
    if(!resource)continue;
    try{await resource.close();result.cleanup.notes.push(name+' closed');}
    catch(error){result.cleanup.status='Incomplete';result.errors.push(name+' cleanup: '+String(error));process.exitCode=1;}
  }
  result.complete=result.checks_passed===true&&result.cleanup.status==='Complete'&&result.errors.length===0;
  result.finished_at=new Date().toISOString();
  try{await fs.writeFile(path.join(output,'results.json'),JSON.stringify(result,null,2));}
  catch(error){process.exitCode=1;console.error('Final evidence write failed:',error);}
  console.log(JSON.stringify({output,complete:result.complete,before_pass:result.before.filter(r=>r.status==='PASS').length,after_expected_fail:result.after.filter(r=>r.status==='FAIL').map(r=>r.id),unchanged_control:'SEARCH-001',viewer:result.viewer,cleanup:result.cleanup}));
  console.log('Saved evaluation artifacts: '+output);
}
