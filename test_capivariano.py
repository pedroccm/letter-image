#!/usr/bin/env python3
import requests
import json
import signal
import sys
import threading
import time

# Teste simples - gerar backgrounds para Capivariano
BASE_URL = "https://letter-image.onrender.com"
team_name = "capivariano"

print(f"🦫 Gerando backgrounds para: {team_name}")
print("💡 Pressione Ctrl+C para cancelar a qualquer momento")

# Função para capturar Ctrl+C
def signal_handler(sig, frame):
    print("\n\n🛑 Cancelado pelo usuário!")
    print("👋 Saindo...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

data = {
    "team_name": team_name,
    "count": 1,
    "size": "1024x1536",
    "quality": "medium"
}

# Mostrar progresso durante timeout
def show_progress():
    dots = 0
    while True:
        print(f"\r⏳ Aguardando resposta{'.' * (dots % 4):<3}", end="", flush=True)
        dots += 1
        time.sleep(1)

print("\n🚀 Enviando requisição...")

try:
    # Iniciar thread de progresso
    progress_thread = threading.Thread(target=show_progress, daemon=True)
    progress_thread.start()
    
    response = requests.post(
        f"{BASE_URL}/generate-team-backgrounds",
        json=data,
        timeout=60  # Reduzido para 1 minuto
    )
    
    print(f"\n📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Sucesso! {result['count']} imagem(ns) gerada(s)")
        print("🔗 URLs:")
        
        for i, url in enumerate(result['urls'], 1):
            print(f"   {i}. {url}")
    else:
        print(f"❌ Erro: {response.text}")
        
except requests.Timeout:
    print(f"\n⏰ TIMEOUT após 60s - Servidor muito lento")
    print("💡 Tente novamente ou verifique o servidor")
except KeyboardInterrupt:
    print(f"\n🛑 Cancelado pelo usuário!")
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("\n🏁 Teste finalizado")