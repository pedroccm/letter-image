import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

BASE_URL = "https://letter-image.onrender.com"

# SEU TEXTO E CORES AQUI - EDITE ESTAS VARIÁVEIS
MEU_TEXTO = "Digite seu texto aqui!"
COR_TEXTO = "#000000"          # Cor do texto (exemplo: #ff0000 para vermelho)
COR_FUNDO = "#FFFFFF"          # Cor de fundo (exemplo: #00ff00 para verde)

def testar_api():
    """Teste básico da API"""
    print("=== Teste básico da API ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print()

def gerar_imagem_personalizada():
    """Gerar imagem com suas configurações"""
    print("=== Gerando sua imagem personalizada ===")
    params = {
        'text': MEU_TEXTO,
        'width': 600,
        'height': 300,
        'font_size': 32,
        'text_color': COR_TEXTO,
        'background_color': COR_FUNDO,
        'font': 'AghartiVF.ttf'
    }

    response = requests.get(f"{BASE_URL}/render", params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        plt.figure(figsize=(10, 5))
        plt.imshow(image)
        plt.axis('off')
        plt.title('Sua imagem com fonte AghartiVF')
        plt.show()
        return image
    else:
        print(f"Erro: {response.text}")
        return None

def exemplo_cores():
    """Exemplo com cores personalizadas"""
    print("=== Exemplo com cores personalizadas ===")
    params = {
        'text': 'Texto Colorido!',
        'width': 800,
        'height': 200,
        'font_size': 48,
        'text_color': '#FFFFFF',      # Branco
        'background_color': '#FF4444', # Vermelho
        'font': 'AghartiVF.ttf'
    }

    response = requests.get(f"{BASE_URL}/render", params=params)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        plt.figure(figsize=(12, 3))
        plt.imshow(image)
        plt.axis('off')
        plt.title('Exemplo colorido')
        plt.show()

def salvar_imagem():
    """Salvar sua imagem personalizada"""
    print("=== Salvando sua imagem ===")
    params = {
        'text': MEU_TEXTO,
        'width': 800,
        'height': 400,
        'font_size': 40,
        'text_color': COR_TEXTO,
        'background_color': COR_FUNDO,
        'font': 'AghartiVF.ttf'
    }

    response = requests.get(f"{BASE_URL}/render", params=params)
    if response.status_code == 200:
        with open('minha_imagem.png', 'wb') as f:
            f.write(response.content)
        print("✅ Imagem salva como 'minha_imagem.png'")
        
        image = Image.open(BytesIO(response.content))
        plt.figure(figsize=(10, 5))
        plt.imshow(image)
        plt.axis('off')
        plt.title('Sua imagem salva')
        plt.show()
    else:
        print(f"❌ Erro: {response.text}")

if __name__ == "__main__":
    # Executar todos os testes
    testar_api()
    gerar_imagem_personalizada()
    exemplo_cores()
    salvar_imagem()