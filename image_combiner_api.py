#!/usr/bin/env python3
"""
image_combiner_api.py

API FastAPI para combinar/editar duas imagens usando o modelo openai/gpt-image-1 da AIML.
"""

import pathlib
import base64
import requests
import tempfile
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from openai import OpenAI
import uvicorn

app = FastAPI(title="Image Combiner API", version="1.0.0")

# Diretório onde ficam as imagens armazenadas
IMAGES_DIR = pathlib.Path("stored_images")

# Sua chave fixa
API_KEY = "a2c4457ed6a14299a425dd670e5a8ad0"

# Cliente OpenAI apontando para o endpoint da AIML
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.aimlapi.com/v1",
)

def save_from_url(url: str, out_path: pathlib.Path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)

def find_image_by_name(image_name: str) -> pathlib.Path:
    """
    Encontra uma imagem pelo nome, com ou sem extensão.
    Suporta extensões: .jpg, .jpeg, .png, .webp
    """
    # Se já tem extensão, usa diretamente
    if '.' in image_name:
        image_path = IMAGES_DIR / image_name
        if image_path.exists():
            return image_path
    else:
        # Busca por extensões suportadas
        extensions = ['.jpg', '.jpeg', '.png', '.webp']
        for ext in extensions:
            image_path = IMAGES_DIR / f"{image_name}{ext}"
            if image_path.exists():
                return image_path
    
    # Se não encontrou, levanta exceção
    raise HTTPException(status_code=404, detail=f"Imagem '{image_name}' não encontrada")

@app.post("/combine-images")
async def combine_images(
    image1_name: str = Form(..., description="Nome da primeira imagem armazenada"),
    image2_name: str = Form(..., description="Nome da segunda imagem armazenada"), 
    prompt: str = Form(..., description="Prompt para combinar as imagens"),
    size: str = Form("1024x1536", description="Tamanho da imagem resultante"),
    quality: str = Form("medium", description="Qualidade da imagem")
):
    """
    Combina duas imagens armazenadas no servidor usando AI baseado no prompt fornecido.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Encontra as imagens (com ou sem extensão)
            image1_path = find_image_by_name(image1_name)
            image2_path = find_image_by_name(image2_name)
            
            # Abre as imagens para a API
            images = [open(image1_path, "rb"), open(image2_path, "rb")]
            
            try:
                result = client.images.edit(
                    model="openai/gpt-image-1",
                    image=images,
                    prompt=prompt,
                    size=size,
                    output_format="png",
                    quality=quality,
                    background="auto",
                )
                
                choice = result.data[0]
                
                # Salva a imagem resultante
                output_path = os.path.join(temp_dir, "result.png")
                
                if getattr(choice, "url", None):
                    save_from_url(choice.url, pathlib.Path(output_path))
                elif getattr(choice, "b64_json", None):
                    img_bytes = base64.b64decode(choice.b64_json)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                else:
                    raise HTTPException(status_code=500, detail="Resposta inesperada da API")
                
                return FileResponse(
                    output_path,
                    media_type="image/png",
                    filename="combined_image.png"
                )
                
            finally:
                for f in images:
                    f.close()
                    
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar imagens: {str(e)}")

@app.get("/list-images")
async def list_images():
    """
    Lista todas as imagens disponíveis no servidor.
    """
    try:
        if not IMAGES_DIR.exists():
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            return {"images": []}
        
        images = [f.name for f in IMAGES_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar imagens: {str(e)}")

@app.get("/")
async def root():
    """
    Endpoint de status da API.
    """
    return {"message": "Image Combiner API está funcionando!"}

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)