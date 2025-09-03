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
    width: int = 800
    height: int = 400
    font_size: int = 32
    text_color: str = "#000000"
    background_color: str = "#FFFFFF"

@app.get("/")
async def root():
    return {"message": "Text to Image API"}

@app.get("/render")
async def render_text(
    text: str = Query(..., description="Texto a ser renderizado"),
    width: int = Query(800, description="Largura da imagem"),
    height: int = Query(400, description="Altura da imagem"),
    font_size: int = Query(32, description="Tamanho da fonte"),
    text_color: str = Query("#000000", description="Cor do texto"),
    background_color: str = Query("#FFFFFF", description="Cor de fundo"),
    font: str = Query("DejaVuSans.ttf", description="Nome do arquivo da fonte")
):
    try:
        # Criar uma nova imagem
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Tentar carregar a fonte
        try:
            font_path = os.path.join("fonts", font)
            font_obj = ImageFont.truetype(font_path, font_size)
        except:
            # Usar fonte padrão se não encontrar a fonte personalizada
            font_obj = ImageFont.load_default()
        
        # Calcular posição para centralizar o texto
        bbox = draw.textbbox((0, 0), text, font=font_obj)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
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