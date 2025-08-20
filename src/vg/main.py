from .utils import check_gpu_availability,analyze_stock_with_ollama
from fastapi import FastAPI, UploadFile, File, Form
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64


class ImageQueryRequest(BaseModel):
    user_query: str="Its a stock trend, Give me candle pairs which might trigger 100 point movement with maximum pullback of 40 points"
    base_64: str
    model: Optional[str] = 'gemma3'
    num_gpu: Optional[int] = -1
    num_ctx: Optional[int] = 20480


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Application started")
    print(check_gpu_availability())
    
    import os
    host = getattr(app.state, 'host', os.getenv('HOST', '0.0.0.0'))
    port = getattr(app.state, 'port', os.getenv('PORT', '8000'))
    
    # Print dynamic URLs
    print(f"🚀 App running at: http://{host}:{port}")
    print(f"📚 Swagger UI: http://{host}:{port}{app.docs_url or '/docs'}")
    print(f"📋 ReDoc: http://{host}:{port}{app.redoc_url or '/redoc'}")
    print(f"📊 OpenAPI JSON: http://{host}:{port}{app.openapi_url or '/openapi.json'}")
    
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
    result=analyze_stock_with_ollama(
        base64_image=request.base_64,
        model=request.model,
        num_gpu=request.num_gpu,
        num_ctx=request.num_ctx,
        prompt=request.user_query
    )
    return {"data": result}


@app.post("/upload_and_query")
async def upload_and_query(
    file: UploadFile = File(...),
    user_query: str = Form("Its a stock trend, Give me candle pairs which might trigger 100 point movement with maximum pullback of 40 points"),
    model: Optional[str] = Form('gemma3'),
    num_gpu: Optional[int] = Form(-1),
    num_ctx: Optional[int] = Form(20480)
):
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
        prompt=user_query
    )
    
    return {"data": result }


import uvicorn
import sys
import time
import logging

def run():
    # Set host and port in app state for dynamic URL generation
    app.state.host = "0.0.0.0"
    app.state.port = "8000"
    
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(
        "vg.main:app", 
        host="0.0.0.0", 
        port=8000, 
        workers=2,
        reload=True,
        reload_dirs=["./src"], 
        log_level="debug",      
        access_log=True,        
        use_colors=True
    )

def run_service():
    """Run the application as a system service (production mode)"""
    # Set host and port in app state for dynamic URL generation
    app.state.host = "0.0.0.0"
    app.state.port = "8000"
    
    # Production configuration for service
    uvicorn.run(
        "vg.main:app", 
        host="0.0.0.0", 
        port=8000, 
        workers=4,  # More workers for production
        reload=False,  # No reload in production
        log_level="debug",  # Less verbose logging
        access_log=True,
        use_colors=False
    )
