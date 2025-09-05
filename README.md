# Text to Image API

Uma API FastAPI para converter texto em imagens PNG customizáveis.

## 🌐 Live Demo

A API está disponível em: **https://letter-image.onrender.com**

## 📋 Descrição

Esta API permite gerar imagens PNG a partir de texto com diversas opções de personalização, incluindo:

- Tamanho da imagem (largura e altura)
- Tamanho da fonte
- Cores do texto e fundo
- Fontes personalizadas da família Agharti

## 🚀 Como Usar

### Endpoint Principal

```
GET /render
```

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Valor Padrão | Descrição |
|-----------|------|-------------|--------------|-----------|
| `text` | string | ✅ | - | Texto a ser renderizado |
| `width` | integer | ❌ | 800 | Largura da imagem em pixels |
| `height` | integer | ❌ | 400 | Altura da imagem em pixels |
| `font_size` | integer | ❌ | 32 | Tamanho da fonte |
| `text_color` | string | ❌ | #000000 | Cor do texto (formato hexadecimal) |
| `background_color` | string | ❌ | #FFFFFF | Cor do fundo (formato hexadecimal) |
| `font` | string | ❌ | DejaVuSans.ttf | Nome do arquivo da fonte |

### Exemplos de Uso

#### 1. Exemplo Básico
```
https://letter-image.onrender.com/render?text=Olá+Mundo!
```

#### 2. Com Dimensões Customizadas
```
https://letter-image.onrender.com/render?text=Python+FastAPI&width=800&height=200&font_size=48
```

#### 3. Com Cores Personalizadas
```
https://letter-image.onrender.com/render?text=Texto+Colorido&width=600&height=300&font_size=40&text_color=%234A90E2&background_color=%23F5F5F5
```

#### 4. Com Fonte Personalizada
```
https://letter-image.onrender.com/render?text=Fonte+Agharti&font=AghartiVF.ttf&font_size=48
```

## 🎨 Fontes Disponíveis

A API inclui a família completa de fontes **Agharti** com diversas variações:

### Pesos Disponíveis
- Hair, Thin, Light, Regular, Demi, Bold, Black

### Larguras Disponíveis
- UltraCondensed, Condensed, SemiCondensed, Regular, SemiWide, Wide, UltraWide

### Arquivo Variável
- `AghartiVF.ttf` - Fonte variável que permite ajustes dinâmicos

### Exemplos de Fontes
```
Agharti-Regular.ttf
Agharti-Bold.ttf
Agharti-Light.ttf
Agharti-BlackCondensed.ttf
AghartiVF.ttf
```

## 📚 Documentação da API

Acesse a documentação interativa em:
- **Swagger UI**: https://letter-image.onrender.com/docs
- **ReDoc**: https://letter-image.onrender.com/redoc

## 🛠️ Desenvolvimento Local

### Pré-requisitos
- Python 3.7+
- pip

### Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd letter-image
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python app.py
```

ou

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em `http://localhost:8000`

### Dependências

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pillow==10.4.0
```

## 🔧 Estrutura do Projeto

```
letter-image/
├── app.py              # Aplicação principal FastAPI
├── requirements.txt    # Dependências do projeto
├── fonts/             # Pasta com fontes Agharti
├── test_api.py        # Testes da API
├── test_api.ipynb     # Notebook de testes
└── README.md          # Este arquivo
```

## 📝 Funcionalidades

- ✅ Geração de imagens PNG a partir de texto
- ✅ Personalização completa de cores (texto e fundo)
- ✅ Ajuste de dimensões da imagem
- ✅ Controle do tamanho da fonte
- ✅ Suporte a fontes personalizadas Agharti
- ✅ Centralização automática do texto
- ✅ API RESTful com FastAPI
- ✅ CORS habilitado
- ✅ Documentação automática (Swagger/OpenAPI)
- ✅ Deploy no Render.com

## 🌍 Deploy

A aplicação está configurada para deploy automático no Render.com e pode ser acessada em:

**https://letter-image.onrender.com**

## 🤝 Como Contribuir

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.