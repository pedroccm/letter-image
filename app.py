from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import pathlib
import requests
import tempfile
from openai import OpenAI

app = FastAPI(title="Text to Image API", description="API para converter texto em imagem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Configuração para combinação de imagens
IMAGES_DIR = pathlib.Path("stored_images")
API_KEY = "a2c4457ed6a14299a425dd670e5a8ad0"

class TextRequest(BaseModel):
    text: str
    width: int = 400
    height: int = 200
    font_size: int = 32
    text_color: str = "#000000"
    background_color: str = "#FFFFFF"

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
        extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg']
        for ext in extensions:
            image_path = IMAGES_DIR / f"{image_name}{ext}"
            if image_path.exists():
                return image_path
    
    # Se não encontrou, levanta exceção
    raise HTTPException(status_code=404, detail=f"Imagem '{image_name}' não encontrada")

@app.get("/")
async def root():
    return {"message": "Text to Image API"}

@app.get("/render")
async def render_text(
    text: str = Query(..., description="Texto a ser renderizado"),
    width: int = Query(400, description="Largura da imagem"),
    height: int = Query(200, description="Altura da imagem"),
    font_size: int = Query(32, description="Tamanho da fonte"),
    text_color: str = Query("#000000", description="Cor do texto"),
    background_color: str = Query("#FFFFFF", description="Cor de fundo"),
    font: str = Query("DejaVuSans.ttf", description="Nome do arquivo da fonte")
):
    try:
        # Verificar se o fundo deve ser transparente
        if background_color.lower() == 'transparent' or background_color.lower() == '#00000000':
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        else:
            img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Tentar carregar a fonte
        try:
            font_path = os.path.join("fonts", font)
            font_obj = ImageFont.truetype(font_path, font_size)
        except:
            # Usar fonte padrão se não encontrar a fonte personalizada
            font_obj = ImageFont.load_default()
        
        # Posicionar texto no canto superior esquerdo sem margem
        x = 0
        y = 0
        
        # Desenhar o texto
        draw.text((x, y), text, fill=text_color, font=font_obj)
        
        # Retornar imagem diretamente
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return Response(content=buffer.getvalue(), media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar imagem: {str(e)}")

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
                # Inicializar cliente apenas quando necessário
                client = OpenAI(
                    api_key=API_KEY,
                    base_url="https://api.aimlapi.com/v1",
                )
                
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
        
        images = [f.name for f in IMAGES_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.svg']]
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar imagens: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)