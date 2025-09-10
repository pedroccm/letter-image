from fastapi import FastAPI, HTTPException, Query
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
import random
import zipfile
import time
from openai import OpenAI
from supabase import create_client, Client

app = FastAPI(title="Text to Image API", description="API para converter texto em imagem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Configuração para combinação de imagens
IMAGES_DIR = pathlib.Path("stored_images")
BGS_DIR = pathlib.Path("bgs")
API_KEY = os.getenv("AIML_API_KEY", "a2c4457ed6a14299a425dd670e5a8ad0")

# Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://iynirubuonhsnxzzmrry.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5bmlydWJ1b25oc254enptcnJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY3NjY2MjEsImV4cCI6MjA3MjM0MjYyMX0.Xz2OnUsd9R5qNFYO4apKNQe61dyWbBxEk7CeRBNy818")

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

class TextRequest(BaseModel):
    text: str
    width: int = 400
    height: int = 200
    font_size: int = 32
    text_color: str = "#000000"
    background_color: str = "#FFFFFF"

class GenerateTeamBackgroundsRequest(BaseModel):
    team_name: str
    size: str = "1024x1024"
    quality: str = "medium"

def save_from_url(url: str, out_path: pathlib.Path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)

def upload_image_to_supabase(image_path: str, file_name: str) -> str:
    """
    Faz upload de uma imagem para o Supabase Storage e retorna a URL pública.
    
    Args:
        image_path: Caminho para o arquivo de imagem
        file_name: Nome do arquivo no Supabase
    
    Returns:
        URL pública da imagem
    """
    try:
        # Ler o arquivo de imagem
        with open(image_path, "rb") as f:
            file_data = f.read()
        
        # Upload para o bucket "fotos"
        response = supabase.storage.from_("fotos").upload(
            path=file_name,
            file=file_data,
            file_options={
                "content-type": "image/png",
                "upsert": "true"  # Sobrescrever se já existir
            }
        )
        
        if response.error:
            raise Exception(f"Erro no upload: {response.error}")
        
        # Obter URL pública
        public_url = supabase.storage.from_("fotos").get_public_url(file_name)
        
        return public_url
    
    except Exception as e:
        print(f"Erro ao fazer upload para Supabase: {str(e)}")
        raise e

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

@app.post("/generate-team-backgrounds")
async def generate_team_backgrounds(request: GenerateTeamBackgroundsRequest):
    """
    Gera 5 imagens de fundo personalizadas para um time usando IA e retorna URLs do Supabase.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Encontra o escudo do time
            team_logo_path = find_image_by_name(request.team_name)
            
            # Pega 5 imagens aleatórias da pasta bgs
            if not BGS_DIR.exists():
                raise HTTPException(status_code=404, detail="Pasta de backgrounds não encontrada")
            
            bg_files = [f for f in BGS_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
            if len(bg_files) < 5:
                raise HTTPException(status_code=404, detail="Não há backgrounds suficientes na pasta bgs")
            
            selected_bgs = random.sample(bg_files, 5)
            
            # Inicializar cliente OpenAI
            client = OpenAI(
                api_key=API_KEY,
                base_url="https://api.aimlapi.com/v1",
            )
            
            urls = []
            timestamp = int(time.time())
            
            for i, bg_path in enumerate(selected_bgs):
                try:
                    # Abre as imagens para a API (fundo + escudo)
                    with open(bg_path, "rb") as bg_file, open(team_logo_path, "rb") as logo_file:
                        images = [bg_file, logo_file]
                        
                        prompt = f"faça uma versão desse fundo com as cores do escudo do {request.team_name} coloque o escudo por cima mesclado com 50% de opacidade"
                        
                        result = client.images.edit(
                            model="openai/gpt-image-1",
                            image=images,
                            prompt=prompt,
                            size=request.size,
                            output_format="png",
                            quality=request.quality,
                            background="auto",
                        )
                        
                        choice = result.data[0]
                        
                        # Salva a imagem temporariamente
                        output_filename = f"{request.team_name}_bg_{i+1}.png"
                        output_path = os.path.join(temp_dir, output_filename)
                        
                        if getattr(choice, "url", None):
                            save_from_url(choice.url, pathlib.Path(output_path))
                        elif getattr(choice, "b64_json", None):
                            img_bytes = base64.b64decode(choice.b64_json)
                            with open(output_path, "wb") as f:
                                f.write(img_bytes)
                        else:
                            raise HTTPException(status_code=500, detail="Resposta inesperada da API")
                        
                        # Upload para Supabase e obter URL
                        supabase_filename = f"{request.team_name}_bg_{i+1}_{timestamp}.png"
                        public_url = upload_image_to_supabase(output_path, supabase_filename)
                        
                        urls.append(public_url)
                        print(f"✅ Imagem {i+1} processada: {public_url}")
                        
                except Exception as e:
                    print(f"❌ Erro ao processar background {i+1}: {str(e)}")
                    continue
            
            if not urls:
                raise HTTPException(status_code=500, detail="Nenhuma imagem foi gerada com sucesso")
            
            # Retornar URLs das imagens
            return {
                "success": True,
                "team_name": request.team_name,
                "count": len(urls),
                "urls": urls
            }
                    
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