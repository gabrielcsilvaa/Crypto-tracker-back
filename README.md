# API REST para rastrear criptomoedas, gerenciar favoritos, portfólio e alertas de preço. Projeto pensado para integrar com o app mobile (React Native/Expo).

---

🚀 Stack

- Django 5 + Django REST Framework
- PostgreSQL
- Redis (cache) + Celery / Celery Beat (tarefas)
- JWT (djangorestframework-simplejwt)
- Docker / Docker Compose
- drf-spectacular (OpenAPI/Swagger)

---

🧩 Arquitetura (pasta → o que faz)

core/

- settings.py: config do Django (apps, DB, CORS, DRF, JWT, cache, Celery).
- urls.py: roteamento raiz (prefixo /api/).
- celery.py: bootstrap do Celery/Beat.

authentication/

- serializers.py: validação e transformação de dados de auth/usuário.
- views.py: endpoints de registrar, login, refresh, me.
- urls.py: rotas de auth.

coins/

- services/coingecko.py: cliente da API CoinGecko.
- services/cache.py: utilitários de cache (Redis) para listas/detalhes/gráfico.
- views.py: listagem, detalhes e gráfico (proxy/coalesce + cache).
- tasks.py: atualização periódica de cache (Celery Beat).
- urls.py: rotas de moedas.

portfolio/

- models.py: Favorite, PortfolioHolding, PriceAlert, Notification.
- serializers.py: (de/para) JSON de favoritos, holdings e alertas.
- views.py: CRUD de favoritos, portfólio e alertas; leitura de notificações.
- tasks.py: verificação de alertas e atualização de preços (on-demand).
- urls.py: rotas de favoritos/portfólio/alertas/notificações.

utils/

- health_check.py: checagens (DB, Redis, Celery, CoinGecko).
- exceptions.py: mapeamento de erros e mensagens.

Infra:

- Dockerfile, docker-compose.yml: subir tudo com DB/Redis/worker/beat.
- .env.example: exemplo de variáveis.
- entrypoint.sh: script de inicialização(tem tanto o migrate quando o python manage runserver 0.0.0.1).
- requirements.txt: dependências.

---

⚙️ Como rodar

```bash
docker-compose up --build
```

API: http://localhost:3000/api/

Docs (Swagger): http://localhost:3000/api/docs/

(opcional) Admin: http://localhost:3000/admin/

Variáveis importantes no .env:

```text
DATABASE_URL=postgresql://...
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

TTLs de cache (em segundos): COIN_LIST_CACHE_TTL, COIN_DETAIL_CACHE_TTL, COIN_CHART_CACHE_TTL

---

🔐 Autenticação (JWT)

Prefixo padrão: /api. Abaixo mostro caminhos sem o prefixo para ficar mais legível; considere sempre /api/<rota> no consumo.

**POST auth/register/**

Cria usuário.

Body

```json
{
  "email": "user@example.com",
  "password": "SenhaForte123!",
  "first_name": "Nome",
  "last_name": "Sobrenome"
}
```

201 → usuário básico (sem tokens).

**POST auth/login/**

Gera tokens.

Body

```json
{ "email": "user@example.com", "password": "SenhaForte123!" }
```

200 →

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": { "id": "uuid", "email": "user@example.com", "first_name": "Nome", "last_name": "Sobrenome" }
}
```

**POST auth/refresh/**

Troca refresh por novo access.

Body

```json
{ "refresh": "<jwt>" }
```

200 →

```json
{ "access": "<novo_access>" }
```

**GET auth/me/** (Auth)

Dados do usuário logado.

200 →

```json
{ "id":"uuid","email":"user@example.com","first_name":"Nome","last_name":"Sobrenome","created_at":"..." }
```

---

🪙 Moedas (CoinGecko proxy + cache)

**GET coins/**

Lista paginada (cache curto via Redis).

Query (opc.) page, per_page (max 100), search

200 →

```json
{
  "count": 100,
  "next": "http://.../coins/?page=2",
  "previous": null,
  "results": [
    {
      "id": "bitcoin",
      "symbol": "btc",
      "name": "Bitcoin",
      "image": "https://...",
      "current_price": 43521.0,
      "price_change_24h": 1023.45,
      "price_change_percentage_24h": 2.34,
      "market_cap": 850200000000,
      "market_cap_rank": 1,
      "total_volume": 23400000000,
      "high_24h": 44000.0,
      "low_24h": 42000.0,
      "cached": true,
      "cached_at": "2024-03-15T10:30:00Z"
    }
  ]
}
```

**GET coins/<coin_id>/**

Detalhes da moeda (cache).

**GET coins/<coin_id>/chart/**

Histórico de preços (pares [timestamp_ms, price]).

Query days ∈ {1,7,30,90,365,max}

Background: Celery Beat pode pré-atualizar cache das top 100 moedas periodicamente para suavizar rate limit e dar tempo de resposta constante.

---

⭐ Favoritos (sync)

**GET portfolio/favorites/** (Auth)

Lista favoritos do usuário.

**POST portfolio/favorites/** (Auth)

Cria favorito.

Body

```json
{ "coin_id": "bitcoin" }
```

201 →

```json
{
  "id":"uuid","coin_id":"bitcoin","coin_name":"Bitcoin",
  "coin_symbol":"btc","coin_image":"https://...","created_at":"..."
}
```

**DELETE portfolio/favorites/<id>/** (Auth)

Remove favorito. 204

---

💼 Portfólio (holdings)

**GET portfolio/** (Auth)

Resumo + holdings.

200 →

```json
{
  "total_value_usd": 5432.0,
  "total_invested_usd": 5197.5,
  "total_profit_usd": 234.5,
  "total_profit_percentage": 4.51,
  "holdings": [
    {
      "id":"uuid","coin_id":"bitcoin","coin_name":"Bitcoin","coin_symbol":"btc","coin_image":"https://...",
      "amount":0.05,"purchase_price_usd":42000.0,"current_price_usd":43521.0,
      "invested_value_usd":2100.0,"current_value_usd":2176.05,"profit_usd":76.05,"profit_percentage":3.62,
      "purchase_date":"2024-02-15T10:30:00Z","created_at":"...","updated_at":"..."
    }
  ]
}
```

**POST portfolio/** (Auth)

Adiciona holding.

Body

```json
{ "coin_id":"bitcoin","amount":0.05,"purchase_price_usd":42000.0,"purchase_date":"2024-02-15" }
```

201 → holding calculada com preços atuais.

**PATCH portfolio/<id>/** (Auth)

Atualiza amount/purchase_price_usd. 200

**DELETE portfolio/<id>/** (Auth)

Remove holding. 204

---

🚨 Alertas de preço

**GET portfolio/alerts/** (Auth)

Lista alertas do usuário.

200 →

```json
[
  {
    "id":"uuid","coin_id":"bitcoin","coin_name":"Bitcoin","coin_symbol":"btc",
    "condition":"above","target_price_usd":45000.0,"current_price_usd":43521.0,
    "is_active":true,"triggered":false,"created_at":"..."
  }
]
```

**POST portfolio/alerts/** (Auth)

Cria alerta.

Body

```json
{ "coin_id":"bitcoin","condition":"above","target_price_usd":45000.0 }
```

201 → alerta ativo.

**DELETE portfolio/alerts/<id>/** (Auth)

Remove alerta. 204

Worker: tarefa periódica do Celery verifica alertas (e.g., a cada 5 min). Quando disparar, marca triggered=true, is_active=false e cria uma Notification.

---

🔔 Notificações

**GET notifications/** (Auth)

Lista notificações (ex.: disparos de alerta).

**PATCH notifications/<id>/read/** (Auth)

Marca como lida. 200

---

❤️ Health & 📚 Docs

**GET health/**

Status do serviço e dependências (DB, Redis, Celery worker/beat, CoinGecko, versão, timestamp).

**GET docs/**

Swagger/OpenAPI da API completa.

---

⏱️ Tarefas (Celery)

- update_coin_prices_cache (Beat): atualiza cache das top moedas (lista, detalhes e/ou gráfico).
- check_price_alerts (Beat): avalia PriceAlert ativos, dispara e cria Notification.
- update_portfolio_prices(user_id) (on-demand): recalcula preços correntes de holdings de um usuário (pode ser invocado após mutações, se necessário).

---

🧪 Respostas / Erros (padrão)

- 200/201/204 nas operações OK.
- 400 validação de serializer.
- 401 não autenticado / token inválido (refresh recomendado no app).
- 403 sem permissão (acesso a recurso de outro usuário).
- 404 não encontrado (id inexistente).
- 429 (opcional) se houver rate limit local.

---

📦 Paginação & Cache

- Listas usam paginação DRF (?page=1&per_page=20).
- Moedas usam Redis com TTL curto para reduzir chamadas à CoinGecko.
- Falha na CoinGecko → responde com cache se disponível.

---

🔐 Segurança

- Senhas hasheadas (Django).
- JWT com expiração (access curto, refresh mais longo).
- CORS configurado.
- Validação de entrada via serializers.
- Recomenda-se HTTPS em produção e rate limit.
