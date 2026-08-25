# FutCarreira — Simulador de Carreira de Futebol

Simulador de carreira de futebol full-stack: **Django + Django REST Framework** no
backend, **React (Vite)** no frontend. Crie um jogador, evolua atributos, jogue
partidas simuladas, receba propostas de transferência, tome decisões que
afetam sua carreira, acompanhe conquistas e histórico.

> Este README cobre a etapa atual do projeto: o **backend está funcionalmente
> completo** (modelos, API, motor de simulação, autenticação, dados
> iniciais). O **frontend ainda é um esqueleto** (Vite + React já configurado,
> mas ainda não consome a API) — próxima etapa do desenvolvimento.

---

## Arquitetura

```
project/
├── backend/
│   ├── manage.py
│   ├── config/          # settings, urls, wsgi/asgi
│   ├── accounts/        # User customizado
│   ├── players/         # Player, PlayerAttributes, cálculo de overall, evolução
│   ├── clubs/           # Club, League, Competition
│   ├── career/          # Season, Training, Achievement, CareerHistory, News,
│   │                     # DecisionEvent/DecisionOption/DecisionLog
│   ├── matches/         # Match, MatchEvent, motor de simulação (engine.py)
│   ├── transfers/       # Transfer, Contract, Injury
│   └── api/              # serializers, views, urls, comando de seed
│
├── frontend/             # React + Vite (esqueleto atual do projeto)
│   ├── src/
│   │   ├── components/  # (a criar)
│   │   ├── pages/       # (a criar)
│   │   ├── services/    # (a criar - cliente da API)
│   │   ├── context/     # GameContext.jsx (a adaptar para consumir a API)
│   │   └── data/        # dadosIniciais.js (dados estáticos locais)
│   └── package.json
│
├── data/                  # JSON com dados de referência (clubes, posições,
│                           # perfis, países, conquistas, eventos de decisão)
├── requirements.txt
└── README.md
```

## Modelos de dados

`User`, `Player`, `PlayerAttributes`, `Club`, `League`, `Competition`,
`Season`, `Match`, `MatchEvent`, `Training`, `Transfer`, `Contract`,
`Injury`, `Achievement`, `PlayerAchievement`, `CareerHistory`, `News`,
`DecisionEvent`, `DecisionOption`, `DecisionLog`.

O **overall** do jogador é sempre calculado no backend (`Player.calcular_overall`),
com pesos por atributo diferentes para cada posição — nunca confiar em cálculo
feito no frontend.

## Motor de simulação

`matches/engine.py` contém `simulate_match(player, forca_adversario, importancia,
mandante)`, isolado de views/serializers. Considera overall, forma atual,
atributos, condição física, força do adversário, importância da partida e
aleatoriedade controlada (com `seed` opcional para testes determinísticos).
Retorna gols, assistências, nota, eventos minuto a minuto e possível lesão.

## Endpoints da API

Base: `/api/`

**Autenticação**
```
POST /api/auth/register/
POST /api/auth/token/            # login -> access + refresh
POST /api/auth/token/refresh/
```

**Dados de referência**
```
GET /api/clubs/
GET /api/leagues/
GET /api/competitions/
```

**Jogador**
```
GET  /api/player/                # jogador do usuário autenticado
POST /api/player/                # cria o jogador (uma vez por usuário)
GET  /api/player/stats/
POST /api/player/train/          # {"tipo": "finalizacao" | "fisico" | ...}
```

**Carreira**
```
GET /api/career/                 # histórico + conquistas + notícias
GET /api/achievements/           # catálogo completo de conquistas
```

**Partidas**
```
GET  /api/matches/
POST /api/matches/simulate/      # {"adversario", "forca_adversario", "importancia", "mandante"}
```

**Transferências**
```
GET  /api/transfers/
POST /api/transfers/generate/            # gera novas propostas
POST /api/transfers/{id}/accept/
POST /api/transfers/{id}/reject/
POST /api/transfers/{id}/negotiate/
```

**Contratos e lesões**
```
GET /api/contracts/
GET /api/injuries/
```

**Decisões**
```
GET  /api/decisions/
POST /api/decisions/submit/      # {"evento_id", "opcao_id"}
```

Toda rota (exceto `register`/`token`) exige o header:
```
Authorization: Bearer <access_token>
```

---

## Como executar o backend

### 1. Pré-requisitos
- Python 3.11+
- pip

### 2. Ambiente virtual
```bash
cd backend
python -m venv .venv

# Ativar (Linux/Mac)
source .venv/bin/activate
# Ativar (Windows)
.venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r ../requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
cp .env.example .env
# edite .env e gere uma SECRET_KEY própria, por exemplo:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Banco de dados
```bash
python manage.py makemigrations accounts players clubs career matches transfers
python manage.py migrate
python manage.py createsuperuser
```

### 6. Popular dados iniciais (clubes, ligas, conquistas, eventos de decisão)
```bash
python manage.py seed_data
```

### 7. Rodar o servidor
```bash
python manage.py runserver
```

A API estará em `http://127.0.0.1:8000/api/` e o admin em
`http://127.0.0.1:8000/admin/`.

---

## Como executar o frontend

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173`. **Ainda não consome a API** — isso faz
parte da próxima etapa do desenvolvimento (services/, adaptação do
GameContext, componentes de tela).

---

## Segurança

- `SECRET_KEY` nunca commitada — vem de `.env` (veja `.env.example`)
- Autenticação via JWT (`djangorestframework-simplejwt`)
- Todas as rotas de jogo exigem autenticação e sempre filtram pelo usuário
  autenticado (`_get_jogador_do_usuario`) — um usuário nunca acessa dados de
  outro
- Todo cálculo de jogo relevante (overall, resultado de partidas, evolução
  de atributos, valores de propostas) acontece no backend; o frontend nunca
  deve ser tratado como fonte confiável desses valores
- CORS restrito por variável de ambiente (`CORS_ALLOWED_ORIGINS`)
- Validação de dados via serializers do DRF em todas as entradas

## Observações sobre este ambiente de geração

O ambiente usado para gerar este código **não tem acesso à internet**, então
não foi possível instalar Django/DRF nem rodar `makemigrations`/`migrate`/testes
automatizados aqui. Todo o código foi escrito e revisado manualmente (sintaxe
Python validada com `py_compile`), mas rode os comandos acima localmente para
gerar as migrations e confirmar que tudo sobe corretamente. Se algo não subir
de primeira, me avise com o erro exato que eu ajusto.

## Próximas etapas

1. Conectar o frontend à API (services/, autenticação, GameContext real)
2. Telas: landing page, criação de jogador, dashboard, partidas com decisões,
   treinamento, transferências, conquistas, notícias, timeline
3. Componentes reutilizáveis: `PlayerCard`, `StatCard`, `MatchCard`,
   `TransferCard`, `NewsCard`, `DecisionModal`, `CareerTimeline`,
   `AttributeChart`
4. Gráficos de evolução (overall, gols, valor de mercado)
5. Ampliar o catálogo de eventos de decisão e notícias
