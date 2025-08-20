"""
Stock Analysis using AI/ML Libraries
A tool for analyzing stock trends using image analysis and language models.
"""

import os
import base64
import torch
from typing import Optional
import ollama

def check_gpu_availability():
    print(f"CUDA available: {torch.cuda.is_available()}")
    num_gpus = torch.cuda.device_count()
    print(f"Number of GPUs available: {num_gpus}")
    for i in range(num_gpus):
        props = torch.cuda.get_device_properties(i)
        print(f"GPU {i}: {props.name}, Memory: {props.total_memory / (1024**3):.2f} GB")


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_bytes = base64.b64encode(image_file.read())
        return encoded_bytes.decode("utf-8")


def analyze_stock_with_ollama(
    base64_image: str, 
    model: str = 'gemma3',
    num_gpu: int = -1,
    num_ctx: int = 1024 * 20,
    prompt: str = "Its a stock trend, Give me candle pairs which might trigger 100 point movement with maximum pullback of 40 points",
    ollama_host: str = "http://localhost:11434",
    ollama_headers: Optional[dict] = None
) -> str:
    
    client = ollama.Client(
        host=ollama_host,  # Remote endpoint: public IP, domain, or ngrok URL
        headers=ollama_headers  # Optional headers
    )
    
    response = client.chat(
        model=model,
        options={'num_ctx': num_ctx, 'num_gpu': num_gpu},
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [base64_image]
        }]
    )
    
    return response.model_dump()["message"]["content"]
