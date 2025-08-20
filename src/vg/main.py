from .utils import check_gpu_availability,analyze_stock_with_ollama
from fastapi import FastAPI, UploadFile, File, Form
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64
import json

class ImageQueryRequest(BaseModel):
    user_query: str="Its a stock trend, Give me candle pairs which might trigger 100 point movement with maximum pullback of 40 points"
    base_64: str
    model: Optional[str] = 'gemma3'
    num_gpu: Optional[int] = -1
    num_ctx: Optional[int] = 20480
    ollama_host: Optional[str] = "http://localhost:11434"
    ollama_headers: Optional[dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Application started")
    print(check_gpu_availability())
    
    import os
    host = getattr(app.state, 'host', os.getenv('LLM_API_HOST', '::'))
    port = getattr(app.state, 'port', os.getenv('LLM_API_PORT', '8484'))
    
    # Format URLs properly for IPv6
    if ':' in host and not host.startswith('['):
        # IPv6 address - wrap in brackets for URLs
        if host == '::':
            display_host = 'localhost'  # More user-friendly for display
            url_host = 'localhost'
        else:
            display_host = f'[{host}]'
            url_host = f'[{host}]'
    else:
        # IPv4 address or already formatted
        display_host = host if host != '0.0.0.0' else 'localhost'
        url_host = display_host
    
    # Print dynamic URLs
    print(f"🚀 App running at: http://{url_host}:{port}")
    print(f"📚 Swagger UI: http://{url_host}:{port}{app.docs_url or '/docs'}")
    print(f"📋 ReDoc: http://{url_host}:{port}{app.redoc_url or '/redoc'}")
    print(f"📊 OpenAPI JSON: http://{url_host}:{port}{app.openapi_url or '/openapi.json'}")
    print(f"🌐 Server bound to: {display_host}:{port} (IPv4/IPv6)")
    
    yield
    print("✅ Application shutting down")

    

app = FastAPI(lifespan=lifespan,debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins
    allow_credentials=True,    # Allow cookies & auth headers
    allow_methods=["*"],       # Allow all HTTP methods, including OPTIONS
    allow_headers=["*"],       # Allow all headers
)


@app.post("/query_image")
def query_image(request: ImageQueryRequest):
    try:
        result=analyze_stock_with_ollama(
            base64_image=request.base_64,
            model=request.model,
            num_gpu=request.num_gpu,
            num_ctx=request.num_ctx,
            prompt=request.user_query,
            ollama_host=request.ollama_host,
            ollama_headers=request.ollama_headers
        )
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@app.post("/upload_and_query")
async def upload_and_query(
    file: UploadFile = File(...),
    user_query: str = Form("Its a stock trend, Give me candle pairs which might trigger 100 point movement with maximum pullback of 40 points"),
    model: Optional[str] = Form('gemma3'),
    num_gpu: Optional[int] = Form(-1),
    num_ctx: Optional[int] = Form(20480),
    ollama_host: Optional[str] = Form("http://localhost:11434"),
    ollama_headers: Optional[str] = Form(r"{}")
):
    try:
        # Read the uploaded file content
        file_content = await file.read()
        
        # Convert to base64
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Analyze the image using the existing function
        result = analyze_stock_with_ollama(
            base64_image=base64_image,
            model=model,
            num_gpu=num_gpu,
            num_ctx=num_ctx,
            prompt=user_query,
            ollama_host=ollama_host,
            ollama_headers=json.loads(ollama_headers) if ollama_headers else None
        )
        
        return {"data": result }
    except Exception as e:
        return {"error": str(e)}


import uvicorn
import sys
import time
import logging
import os

# Global server configuration
SERVER_CONFIG = {
    "host": os.getenv("LLM_API_HOST", "::"),  # Bind to all IPv6 (includes IPv4 on dual-stack)
    "port": int(os.getenv("LLM_API_PORT", "8484")),
}
SERVER_ADDRESS = f"[{SERVER_CONFIG['host']}]:{SERVER_CONFIG['port']}" if ':' in SERVER_CONFIG['host'] else f"{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}"

def run():
    # Set in app state for dynamic URL generation
    app.state.host = SERVER_CONFIG["host"]
    app.state.port = str(SERVER_CONFIG["port"])
    
    print(f"🔧 Starting development server at {SERVER_ADDRESS}")
    
    uvicorn.run(
        "vg.main:app", 
        host=SERVER_CONFIG["host"], 
        port=SERVER_CONFIG["port"], 
        workers=2,
        reload=True,
        reload_dirs=["./src"], 
        log_level="debug",      
        access_log=True,        
        use_colors=True
    )

def run_service():
    """Run the application as a system service (production mode)"""
    # Set in app state for dynamic URL generation
    app.state.host = SERVER_CONFIG["host"]
    app.state.port = str(SERVER_CONFIG["port"])
    
    print(f"🚀 Starting production service at {SERVER_ADDRESS}")
    
    # Production configuration for service
    uvicorn.run(
        "vg.main:app", 
        host=SERVER_CONFIG["host"], 
        port=SERVER_CONFIG["port"], 
        workers=4,  # More workers for production
        reload=False,  # No reload in production
        log_level="debug",  # Less verbose logging
        access_log=True,
        use_colors=False
    )
