"""Optional Chromium smoke test and original-PR/revised layout benchmark.

Requires Playwright, /usr/bin/chromium, and original PR Git history.
Timings exclude raster/compositor/GPU completion. Run from repository root.
"""
import json, re, tempfile, threading, time
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from cognigenesis.commandcenter import server
from cognigenesis.commandcenter.geometry import HTML
from cognigenesis.commandcenter.store import CommandCenterStore
import subprocess
servers=[]
def factory(*args):
    http=ThreadingHTTPServer(*args);servers.append(http);return http
server.ThreadingHTTPServer=factory
with tempfile.TemporaryDirectory() as tmp:
    workspace=Path(tmp)
    store=CommandCenterStore(workspace/'.cognigenesis/command-center.json')
    store.save({'tasks':[{'id':'t1','title':'<script>alert(1)</script>'}]})
    thread=threading.Thread(target=server.serve_command_center,args=(workspace,'127.0.0.1',0),daemon=True);thread.start()
    while not servers: time.sleep(.01)
    url=f'http://127.0.0.1:{servers[0].server_port}'
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1280,'height':800})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(url+'/geometry');page.wait_for_function("() => document.getElementById('nodeCount').textContent==='1'")
        assert "sha256-" in response.headers['content-security-policy']
        for size in [(375,812),(1440,900)]:
            page.set_viewport_size({'width':size[0],'height':size[1]})
            page.wait_for_timeout(100)
            assert page.evaluate('canvas.width>0 && width>0 && height>0')
        store.save({'tasks':[{'id':'t1','title':'Renamed'},{'id':'t2','title':'New'}]})
        page.wait_for_function("() => document.getElementById('nodeCount').textContent==='2'",timeout=6000)
        assert page.evaluate("nodes.find(n=>n.id==='task:t1').label")=='Renamed'
        denied=page.request.get(url+'/api/topology',headers={'Host':'attacker.example'})
        assert denied.status==403
        assert page.request.get(url+'/api/topology',headers={'Sec-Fetch-Site':'cross-site'}).status==403
        baseline=subprocess.check_output(['git','show','2120f050:cognigenesis/commandcenter/geometry.py'],text=True)
        namespace={};exec(baseline,namespace)
        results={}
        for name,html in [('before',namespace['HTML']),('after',HTML)]:
            bench=browser.new_page()
            bench.route('**/api/topology',lambda route:route.fulfill(json={'nodes':[],'links':[]}))
            bench.goto(url+'/geometry')
            # Replace document using the original or revised script, without HTTP CSP.
            bench.goto('about:blank');bench.set_content(html)
            results[name]={}
            for n in [100,1000,2000]:
                data={'nodes':[{'id':f'task:{i}','label':str(i),'type':'task'} for i in range(n)],'links':[{'source':f'task:{i-1}','target':f'task:{i}','relation':'depends_on'} for i in range(1,n)]}
                result=bench.evaluate('''data=>{window.requestAnimationFrame=()=>null;integrate(data);const samples=[];for(let i=0;i<35;i++){const t=performance.now();step();if(i>=5)samples.push(performance.now()-t)}samples.sort((a,b)=>a-b);return {median_ms:samples[15],p95_ms:samples[28]}}''',data)
                results[name][n]=result
            if name == 'after':
                assert bench.evaluate("() => {remaining=1;step();const stopped=remaining===0;integrate({nodes:nodes.map(({id,label,type})=>({id,label,type})),links:edges.map(({source,target,relation})=>({source,target,relation}))});return stopped && remaining===0}")
                assert bench.evaluate("() => {resize();return remaining===300}")
            bench.close()
        assert not errors,errors
        print(json.dumps({'browser':'Chromium headless, software rendering','checks':'CSP execution, polling updates, Host/cross-site rejection, 375px and 1440px resize, no JS errors','frame_cost':results},indent=2))
        browser.close()
    servers[0].shutdown();thread.join()
