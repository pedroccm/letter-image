from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from fastapi.responses import Response
import os

app = FastAPI(title="Text to Image API", description="API para converter texto em imagem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

class TextRequest(BaseModel):
    text: str
    width: int = 400
    height: int = 200
    font_size: int = 32
    text_color: str = "#000000"
    background_color: str = "#FFFFFF"

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)