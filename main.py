from pathlib import Path
import os,secrets,time
from typing import Any
from fastapi import FastAPI,Form,Request
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from .auth import verify_password
from .runner import ToolRunner

BASE=Path(__file__).resolve().parent.parent
TOOLS=BASE/'tools'; LOGS=BASE/'logs'; TOOLS.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
app=FastAPI(title='Python Tool Panel')
app.add_middleware(SessionMiddleware,secret_key=os.environ.get('SESSION_SECRET',secrets.token_urlsafe(32)),max_age=43200,same_site='lax',https_only=os.environ.get('COOKIE_SECURE','0')=='1')
templates=Jinja2Templates(directory=str(BASE/'app'/'templates')); runner=ToolRunner(TOOLS,LOGS)
def auth(r): return r.session.get('authenticated') is True
@app.get('/',response_class=HTMLResponse)
async def index(r:Request): return RedirectResponse('/dashboard' if auth(r) else '/login',303)
@app.get('/login',response_class=HTMLResponse)
async def login_page(r:Request): return templates.TemplateResponse('login.html',{'request':r,'error':None})
@app.post('/login',response_class=HTMLResponse)
async def login(r:Request,password:str=Form(...)):
    if verify_password(password): r.session.update(authenticated=True,csrf=secrets.token_urlsafe(24)); return RedirectResponse('/dashboard',303)
    return templates.TemplateResponse('login.html',{'request':r,'error':'Invalid credentials'},status_code=401)
@app.post('/logout')
async def logout(r:Request): r.session.clear(); return RedirectResponse('/login',303)
@app.get('/dashboard',response_class=HTMLResponse)
async def dashboard(r:Request):
    if not auth(r): return RedirectResponse('/login',303)
    return templates.TemplateResponse('dashboard.html',{'request':r,'tools':runner.list_tools(),'states':runner.status()})
@app.get('/tool/{name}',response_class=HTMLResponse)
async def tool_page(r:Request,name:str):
    if not auth(r): return RedirectResponse('/login',303)
    if name not in runner.list_tools(): return HTMLResponse('Tool not found',404)
    return templates.TemplateResponse('tool.html',{'request':r,'name':name,'csrf':r.session.get('csrf','')})
@app.post('/api/tools/{name}/start')
async def start(r:Request,name:str):
    if not auth(r): return JSONResponse({'error':'unauthorized'},401)
    b:dict[str,Any]=await r.json()
    if b.get('csrf')!=r.session.get('csrf'): return JSONResponse({'error':'invalid csrf'},403)
    args=b.get('args',[])
    if not isinstance(args,list) or not all(isinstance(x,str) for x in args): return JSONResponse({'error':'args must be a string array'},400)
    try: return JSONResponse(await runner.start(name,args))
    except ValueError as e: return JSONResponse({'error':str(e)},400)
    except RuntimeError as e: return JSONResponse({'error':str(e)},409)
@app.post('/api/tools/{name}/stop')
async def stop(r:Request,name:str):
    if not auth(r): return JSONResponse({'error':'unauthorized'},401)
    b=await r.json()
    if b.get('csrf')!=r.session.get('csrf'): return JSONResponse({'error':'invalid csrf'},403)
    return JSONResponse(await runner.stop(name))
@app.get('/api/tools/{name}/logs')
async def logs(r:Request,name:str):
    if not auth(r): return JSONResponse({'error':'unauthorized'},401)
    try: return JSONResponse({'logs':runner.read_logs(name)})
    except ValueError as e: return JSONResponse({'error':str(e)},404)
@app.get('/healthz')
async def healthz(): return {'status':'ok','time':time.time()}
