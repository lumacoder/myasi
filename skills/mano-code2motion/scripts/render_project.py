"""Capture an authored Canvas2D project, not a MotionSpec. Python stdlib + Chrome/ffmpeg.
Only run local code you have inspected. No dependencies are installed automatically.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
import hashlib
import html
import http.server
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import unquote, urlsplit, quote

def find_chrome(explicit=None):
    candidates=[explicit] if explicit else [shutil.which(x) for x in
        ('google-chrome','chromium','chromium-browser','chrome')]
    if not explicit and sys.platform=='win32':
        for base in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            for vendor in ('Google/Chrome/Application/chrome.exe','Microsoft/Edge/Application/msedge.exe'):
                candidates.append(str(Path(os.environ.get(base,''))/vendor))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():return str(Path(candidate).resolve())
    raise RuntimeError('Chrome/Chromium not found; supply --chrome /path/to/executable')


def run(command,timeout=60):
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=timeout,encoding='utf8',errors='replace')
    if result.returncode:
        raise RuntimeError('command failed (%d): %s\n%s'%(result.returncode,command[0],result.stderr[-4000:]))
    return result.stdout


ROOT = Path(__file__).resolve().parents[1]

# The page must explicitly finish initialization. Capture fails closed if it never does.
HARNESS = r'''<script>
(async () => {
 const p=document.createElement('pre'); p.id='motion-capture'; p.hidden=true;
 document.body.append(p); p.textContent=JSON.stringify({status:'pending'});
 try {
  const q=new URLSearchParams(location.search), t=Number(q.get('t'));
  if(!Number.isFinite(t))throw Error('nonfinite capture time');
  while(window.READY!==true || typeof window.renderAt!=='function')
    await new Promise(r=>setTimeout(r,10));
  await document.fonts.ready;
  const c=document.querySelector('canvas'); if(!c)throw Error('Canvas2D required');
  await window.renderAt(t); const a=c.toDataURL();
  if(q.get('probe')==='1') {
    await window.renderAt(Number(q.get('duration'))); await window.renderAt(0);
    await window.renderAt(t);
    if(c.toDataURL()!==a)throw Error('seek-order pixel mismatch');
  }
  p.textContent=JSON.stringify({status:'ready',time_s:t,width:c.width,height:c.height,
    seek_order_checked:q.get('probe')==='1'});
 } catch(e) {p.textContent=JSON.stringify({status:'error',message:String(e)});}
})();</script>'''


def settings(duration, fps, width, height):
    if not math.isfinite(duration) or duration <= 0 or duration > 3600:
        raise ValueError('duration must be finite, in (0,3600] seconds')
    if fps not in range(1,121) or width < 2 or height < 2 or width%2 or height%2:
        raise ValueError('fps must be 1..120; width/height must be positive even integers')
    count=round(duration*fps)
    if count < 1 or abs(count-duration*fps)>1e-8:
        raise ValueError('duration * fps must be an integer frame count')
    return count


def safe_file(root, request_path):
    root=Path(root).resolve()
    relative=unquote(urlsplit(request_path).path).lstrip('/')
    candidate=(root/relative).resolve()
    try: candidate.relative_to(root)
    except ValueError: raise ValueError('path outside project (including symlinks)')
    if not candidate.is_file():
        raise ValueError('not a project file')
    return candidate


@contextlib.contextmanager
def serve_project(root, entry):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            try:
                path=safe_file(root,self.path)
                data=path.read_bytes()
                if path==entry: data+=HARNESS.encode('utf8')
                mime={'.html':'text/html; charset=utf-8','.js':'text/javascript',
                      '.json':'application/json','.css':'text/css','.png':'image/png',
                      '.jpg':'image/jpeg','.svg':'image/svg+xml','.woff2':'font/woff2'}
                self.send_response(200)
                self.send_header('Content-Type',mime.get(path.suffix,'application/octet-stream'))
                self.send_header('Content-Length',str(len(data)))
                self.end_headers(); self.wfile.write(data)
            except (OSError,ValueError): self.send_error(404)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try: yield 'http://127.0.0.1:%d/'%server.server_address[1]
    finally: server.shutdown(); server.server_close(); thread.join()


def parse_protocol(dom,t,width,height,probe=False):
    match=re.search(r'<pre id="motion-capture"[^>]*>(.*?)</pre>',dom,re.S)
    if not match: raise ValueError('missing capture protocol (script failed or browser not ready)')
    result=json.loads(html.unescape(match.group(1)))
    if (result.get('status')!='ready' or not isinstance(result.get('time_s'),(int,float)) or not math.isfinite(result.get('time_s',float('nan'))) or abs(result.get('time_s',-1)-t)>1e-10 or
        result.get('width')!=width or result.get('height')!=height or
        (probe and result.get('seek_order_checked') is not True)):
        raise ValueError('capture protocol failed: '+str(result))
    return result


def capture(chrome,url,target,width,height,t,probe=False):
    with tempfile.TemporaryDirectory(prefix='motion-project-chrome-') as profile:
        cmd=[chrome,'--headless=new','--disable-gpu','--disable-dev-shm-usage',
             '--disable-background-networking','--disable-extensions','--no-first-run',
             '--no-default-browser-check','--hide-scrollbars','--force-device-scale-factor=1',
             '--user-data-dir='+profile,'--window-size=%d,%d'%(width,height),
             '--virtual-time-budget=2000','--run-all-compositor-stages-before-draw',
             '--dump-dom','--screenshot='+str(target)]
        if hasattr(os,'geteuid') and os.geteuid()==0: cmd.append('--no-sandbox')
        dom=run(cmd+[url],timeout=45)
        protocol=parse_protocol(dom,t,width,height,probe)
        if not target.is_file() or target.stat().st_size<100:
            raise ValueError('missing PNG')
        protocol['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        return protocol


def source_hashes(root):
    suffixes={'.html','.js','.mjs','.css','.json','.svg','.png','.jpg','.webp','.woff2','.ttf'}
    result={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if any(part.startswith('.') or part=='__pycache__' for part in relative.parts): continue
        if path.is_file() and path.suffix in suffixes:
            checked=safe_file(root,'/'+relative.as_posix())
            result[relative.as_posix()]=hashlib.sha256(checked.read_bytes()).hexdigest()
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project',type=Path)
    p.add_argument('--entry',default='index.html')
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--chrome')
    p.add_argument('--duration',required=True,type=float)
    p.add_argument('--fps',type=int,default=24)
    p.add_argument('--width',type=int,default=1280)
    p.add_argument('--height',type=int,default=720)
    p.add_argument('--workers',type=int,choices=range(1,5),default=2)
    p.add_argument('--times',help='Only render these comma-separated seconds; no MP4')
    a=p.parse_args(argv)
    try:
        count=settings(a.duration,a.fps,a.width,a.height)
        root=a.project.resolve(); entry=safe_file(root,'/'+a.entry)
        if entry.suffix!='.html': raise ValueError('entry must be an HTML file')
        out=a.out.resolve()
        if out==root or root in out.parents: raise ValueError('output must be outside project')
        source_before=source_hashes(root)
        for ancestor in (out,)+tuple(out.parents):
            if ancestor==ROOT or (ancestor/'.git').exists():
                raise ValueError('output must be outside the skill/repository')
        if out.exists(): raise ValueError('output exists; refuse overwrite')
        times=[float(x) for x in a.times.split(',')] if a.times else [i/a.fps for i in range(count)]
        if not times or any(not math.isfinite(t) or t<0 or t>a.duration for t in times):
            raise ValueError('times must be finite and inside [0,duration]')
        for tool in (() if a.times else ('ffmpeg','ffprobe')):
            if not shutil.which(tool): raise ValueError(tool+' required on PATH')
        chrome=find_chrome(a.chrome)
        out.mkdir(parents=True); (out/'frames').mkdir()
        records=[]
        with serve_project(root,entry) as base:
            url=base+quote(entry.relative_to(root).as_posix())
            # Out-of-order pixel probes are necessary engineering checks, never a visual score.
            for i,t in enumerate((0.,a.duration/2,a.duration)):
                records.append(capture(chrome,url+'?probe=1&t=%.17g&duration=%.17g'%(t,a.duration),
                    out/('probe-%d.png'%i),a.width,a.height,t,True))
            def one(pair):
                i,t=pair; target=out/'frames'/('%06d.png'%i)
                result=capture(chrome,url+'?t=%.17g'%t,target,a.width,a.height,t)
                result['file']=str(target.relative_to(out)); return result
            with ThreadPoolExecutor(max_workers=a.workers) as pool:
                for i,result in enumerate(pool.map(one,enumerate(times)),1):
                    records.append(result)
                    if i%24==0 or i==len(times): print('Frames %d/%d'%(i,len(times)),flush=True)
        if source_hashes(root)!=source_before: raise ValueError('project source changed during capture')
        metadata=None
        if not a.times:
            run(['ffmpeg','-v','error','-framerate',str(a.fps),'-i',str(out/'frames/%06d.png'),
                 '-frames:v',str(count),'-c:v','libx264','-crf','18','-preset','medium',
                 '-pix_fmt','yuv420p','-an','-movflags','+faststart',str(out/'film.mp4')],180)
            metadata=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams',
                                      '-show_format','-of','json',str(out/'film.mp4')]))
            streams=metadata['streams']
            if len(streams)!=1 or streams[0]['codec_type']!='video': raise ValueError('unexpected streams')
            s=streams[0]
            if (s['codec_name']!='h264' or s['pix_fmt']!='yuv420p' or s['width']!=a.width or
                s['height']!=a.height or int(s['nb_read_frames'])!=count or
                s['avg_frame_rate']!='%d/1'%a.fps or
                abs(float(metadata['format']['duration'])-a.duration)>0.001):
                raise ValueError('encoded properties mismatch')
            (out/'ffprobe.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
        result={'project':str(root),'entry':a.entry,'fps':a.fps,'duration_s':a.duration,
                'size':[a.width,a.height],'frames':records,'visual_verdict':'NOT_REVIEWED',
                'chrome_version':run([chrome,'--version']).strip(),
                'source_sha256':source_before,
                'scope':'Canvas2D only; explicit READY; screenshot after seek; no automatic aesthetics'}
        (out/'capture-report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('Capture verified, visual review still required: '+str(out),flush=True)
        return 0
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
        print('Capture failed; partial output retained: '+str(exc),file=sys.stderr); return 1

if __name__=='__main__': sys.exit(main())
