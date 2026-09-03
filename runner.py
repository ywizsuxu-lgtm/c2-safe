from __future__ import annotations
import asyncio,os,signal,time
from pathlib import Path
MAX_RUNTIME=int(os.environ.get('TOOL_MAX_RUNTIME','3600'));MAX_OUTPUT=int(os.environ.get('TOOL_MAX_OUTPUT','65536'))
class ToolRunner:
 def __init__(self,tools:Path,logs:Path):self.tools,self.logs,self.procs,self.tasks=tools,logs,{},{}
 def list_tools(self):return sorted(p.stem for p in self.tools.glob('*.py') if p.is_file() and not p.name.startswith('_'))
 def status(self):return {n:('running' if p.returncode is None else f'exited:{p.returncode}') for n,p in self.procs.items()}
 def path(self,n):
  if n not in self.list_tools():raise ValueError('tool does not exist')
  p=(self.tools/f'{n}.py').resolve()
  if p.parent!=self.tools.resolve():raise ValueError('invalid tool path')
  return p
 async def start(self,n,args):
  p=self.path(n)
  if n in self.procs and self.procs[n].returncode is None:raise RuntimeError('tool already running')
  env={'PATH':os.environ.get('PATH',''),'PYTHONUNBUFFERED':'1','PYTHONPATH':str(self.tools.resolve())}
  proc=await asyncio.create_subprocess_exec('python',str(p),*args,cwd=str(self.tools),env=env,stdin=asyncio.subprocess.DEVNULL,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,start_new_session=True)
  self.procs[n]=proc;self.tasks[n]=asyncio.create_task(self.collect(n,proc));return {'started':True,'pid':proc.pid}
 async def collect(self,n,p):
  started=time.monotonic();log=self.logs/f'{n}.log'
  try:
   with log.open('ab') as f:
    while time.monotonic()-started<MAX_RUNTIME:
     line=await p.stdout.readline()
     if not line:break
     f.write(line[:MAX_OUTPUT]);f.flush()
   if p.returncode is None:os.killpg(p.pid,signal.SIGTERM)
   await p.wait()
  finally:self.procs.pop(n,None);self.tasks.pop(n,None)
 async def stop(self,n):
  p=self.procs.get(n)
  if not p or p.returncode is not None:return {'stopped':False,'reason':'not running'}
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:return {'stopped':True}
  try:await asyncio.wait_for(p.wait(),10)
  except asyncio.TimeoutError:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  return {'stopped':True}
 def read_logs(self,n):
  self.path(n);p=self.logs/f'{n}.log';return p.read_text(encoding='utf-8',errors='replace')[-MAX_OUTPUT:] if p.exists() else ''
