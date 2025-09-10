# Letter Image API - Documentação

API para geração de imagens de texto e backgrounds personalizados para times usando IA.

## URL Base
```
https://letter-image.onrender.com
```

## Endpoints Disponíveis

### 1. Status da API
**GET** `/`

Verifica se a API está funcionando.

**Resposta:**
```json
{
  "message": "Text to Image API"
}
```

---

### 2. Renderização de Texto
**GET** `/render`

Gera uma imagem com texto personalizado.

**Parâmetros (Query String):**
- `text` (obrigatório): Texto a ser renderizado
- `width` (opcional): Largura da imagem (padrão: 400)
- `height` (opcional): Altura da imagem (padrão: 200)
- `font_size` (opcional): Tamanho da fonte (padrão: 32)
- `text_color` (opcional): Cor do texto (padrão: "#000000")
- `background_color` (opcional): Cor de fundo (padrão: "#FFFFFF", use "transparent" para fundo transparente)
- `font` (opcional): Nome do arquivo da fonte (padrão: "DejaVuSans.ttf")

**Exemplo:**
```
GET /render?text=Hello%20World&width=500&height=100&font_size=24&text_color=%23FF0000&background_color=transparent
```

**Resposta:** Imagem PNG

---

### 3. Geração de Backgrounds para Times
**POST** `/generate-team-backgrounds`

Gera backgrounds personalizados para um time usando IA, combinando o escudo do time com backgrounds aleatórios.

**Body (JSON):**
```json
{
  "team_name": "flamengo",
  "count": 3,
  "size": "1024x1536",
  "quality": "medium"
}
```

**Parâmetros:**
- `team_name` (obrigatório): Nome do time (deve existir em `/stored_images/`)
- `count` (opcional): Número de backgrounds a gerar (padrão: 5, máximo: quantidade disponível em `/bgs/`)
- `size` (opcional): Tamanho da imagem (padrão: "1024x1024")
- `quality` (opcional): Qualidade da imagem (padrão: "medium")

**Resposta de Sucesso:**
```json
{
  "success": true,
  "team_name": "flamengo",
  "count": 5,
  "urls": [
    "https://iynirubuonhsnxzzmrry.supabase.co/storage/v1/object/public/fotos/flamengo/bg1.png",
    "https://iynirubuonhsnxzzmrry.supabase.co/storage/v1/object/public/fotos/flamengo/bg15.png",
    "https://iynirubuonhsnxzzmrry.supabase.co/storage/v1/object/public/fotos/flamengo/bg23.png",
    "https://iynirubuonhsnxzzmrry.supabase.co/storage/v1/object/public/fotos/flamengo/bg40.png",
    "https://iynirubuonhsnxzzmrry.supabase.co/storage/v1/object/public/fotos/flamengo/bg52.png"
  ]
}
```

**Exemplo de Uso (JavaScript):**
```javascript
const response = await fetch('https://letter-image.onrender.com/generate-team-backgrounds', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    team_name: 'flamengo',
    count: 3,
    size: '1024x1536',
    quality: 'medium'
  })
});

const result = await response.json();
console.log(result.urls); // Array com as URLs das imagens geradas
```

**Exemplo de Uso (Python):**
```python
import requests

data = {
    "team_name": "flamengo",
    "count": 3,
    "size": "1024x1536", 
    "quality": "medium"
}

response = requests.post(
    "https://letter-image.onrender.com/generate-team-backgrounds",
    json=data
)

result = response.json()
print(result["urls"])  # Lista com as URLs das imagens geradas
```

---

### 4. Listar Imagens Disponíveis
**GET** `/list-images`

Lista todos os escudos de times disponíveis para geração de backgrounds.

**Resposta:**
```json
{
  "images": [
    "flamengo.svg",
    "santos.png", 
    "palmeiras.jpg",
    "corinthians.png",
    "vasco.svg"
  ]
}
```

---

## Como Funciona a Geração de Backgrounds

1. **Seleção Aleatória**: A API seleciona N backgrounds aleatórios da pasta `/bgs/` (onde N = parâmetro `count`)
2. **IA Generativa**: Para cada background, usa OpenAI GPT-Image para combinar:
   - O background original
   - O escudo do time
   - Prompt fixo: "Quero esse fundo com a mesma forma e estilo porem com as cores desse escudo do escudo.png, coloque o logo com opacidade 50% para parecer integrado ao fundo"
3. **Cache Inteligente**: Se a imagem já existe no Supabase, reutiliza em vez de gerar novamente
4. **Organização**: Salva no Supabase em `/fotos/{team_name}/{bg_name}.png`

## Códigos de Erro

- **404**: Time não encontrado ou backgrounds insuficientes
- **500**: Erro interno (IA, Supabase, etc.)

## Limitações

- Apenas times com escudos na pasta `/stored_images/`
- Quantidade de backgrounds na pasta `/bgs/` deve ser >= parâmetro `count`
- Processamento pode demorar 1-3 minutos dependendo da IA
- URLs das imagens são permanentes (Supabase Storage)

## Suporte

Para issues e sugestões: [GitHub Repository](https://github.com/pedroccm/letter-image)