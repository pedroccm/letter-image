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
        print(f"📤 Iniciando upload: {file_name}")
        
        # Ler o arquivo de imagem
        with open(image_path, "rb") as f:
            file_data = f.read()
        
        print(f"📊 Tamanho do arquivo: {len(file_data)} bytes")
        
        # Upload para o bucket "fotos"
        response = supabase.storage.from_("fotos").upload(
            path=file_name,
            file=file_data,
            file_options={
                "content-type": "image/png",
                "upsert": True  # Sobrescrever se já existir
            }
        )
        
        print(f"📋 Resposta do upload: {response}")
        
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Erro no upload: {response.error}")
        
        # Obter URL pública
        public_url = supabase.storage.from_("fotos").get_public_url(file_name)
        print(f"🔗 URL gerada: {public_url}")
        
        return public_url
    
    except Exception as e:
        print(f"❌ Erro detalhado no upload para Supabase: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
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
                    # Extrair nome original do background (ex: bg1, bg15, bg23)
                    bg_original_name = bg_path.stem  # Nome sem extensão
                    supabase_path = f"{request.team_name}/{bg_original_name}.png"
                    
                    # Verificar se a imagem já existe no Supabase
                    try:
                        # Tentar obter URL pública - se não der erro, arquivo existe
                        public_url = supabase.storage.from_("fotos").get_public_url(supabase_path)
                        
                        # Verificar se realmente existe fazendo uma requisição HEAD
                        test_response = requests.head(public_url, timeout=5)
                        if test_response.status_code == 200:
                            urls.append(public_url)
                            print(f"⚡ {bg_original_name} já existe, reutilizando: {public_url}")
                            continue
                    except Exception as check_error:
                        print(f"🔍 Arquivo {bg_original_name} não existe, será gerado: {str(check_error)}")
                        pass  # Arquivo não existe, continuar com geração
                    
                    # Gerar nova imagem se não existir
                    print(f"🔄 Processando {bg_original_name}...")
                    
                    # Abre as imagens para a API (igual ao seu exemplo)
                    images = [open(bg_path, "rb"), open(team_logo_path, "rb")]
                    
                    try:
                        # Usar cliente OpenAI exatamente igual ao seu exemplo
                        result = client.images.edit(
                            model="openai/gpt-image-1",
                            image=images,
                            prompt="Quero esse fundo com a mesma forma e estilo porem com as cores desse escudo do escudo.png, coloque o logo com opacidade 50% para parecer integrado ao fundo",
                            size="1024x1536",
                            output_format="png",
                            quality="medium",
                            background="auto",
                        )

                        choice = result.data[0]
                        
                        # Salva a imagem temporariamente
                        output_filename = f"{bg_original_name}.png"
                        output_path = os.path.join(temp_dir, output_filename)
                        
                        if getattr(choice, "url", None):
                            save_from_url(choice.url, pathlib.Path(output_path))
                        elif getattr(choice, "b64_json", None):
                            img_bytes = base64.b64decode(choice.b64_json)
                            with open(output_path, "wb") as f:
                                f.write(img_bytes)
                        else:
                            raise HTTPException(status_code=500, detail="Resposta inesperada da API")
                        
                        # Upload para Supabase
                        public_url = upload_image_to_supabase(output_path, supabase_path)
                        
                        urls.append(public_url)
                        print(f"✅ {bg_original_name} gerado: {public_url}")
                        
                    finally:
                        # Fechar arquivos
                        for f in images:
                            f.close()
                        
                except Exception as e:
                    print(f"❌ Erro detalhado ao processar {bg_path.name}: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
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