from rest_framework import views, response, permissions, status
from django.conf import settings
from urllib.parse import urlencode

from .services import coingecko, cache

LIST_TTL = int(getattr(settings, "COIN_LIST_CACHE_TTL", 120))
DETAIL_TTL = int(getattr(settings, "COIN_DETAIL_CACHE_TTL", 300))
CHART_TTL = int(getattr(settings, "COIN_CHART_CACHE_TTL", 300))


def _build_page_url(request, page, per_page, search):
    base = request.build_absolute_uri().split("?")[0]
    q = {"page": page, "per_page": per_page}
    if search:
        q["search"] = search
    return f"{base}?{urlencode(q)}"


class CoinsListView(views.APIView):
    """
    GET /api/coins/?page=1&per_page=20&search=bitcoin
    Lista moedas (CoinGecko /coins/markets), com cache e paginação básica.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            page = max(1, int(request.GET.get("page", 1)))
        except ValueError:
            page = 1
        try:
            per_page = int(request.GET.get("per_page", 20))
        except ValueError:
            per_page = 20
        per_page = max(1, min(per_page, 100))  # limite de segurança
        search = (request.GET.get("search") or "").strip()

        # 1) cache
        cached = cache.get_json("coins:list", str(page), str(per_page), search)
        if cached:
            cached["cached"] = True
            return response.Response(cached)

        # 2) fetch CoinGecko (nota: o 'search' não é aplicado nativamente em /markets)
        data = coingecko.list_markets(page=page, per_page=per_page, search=search)

        results = []
        for c in data:
            results.append({
                "id": c.get("id"),
                "symbol": c.get("symbol"),
                "name": c.get("name"),
                "image": c.get("image"),
                "current_price": c.get("current_price"),
                "price_change_24h": c.get("price_change_24h"),
                "price_change_percentage_24h": c.get("price_change_percentage_24h"),
                "market_cap": c.get("market_cap"),
                "market_cap_rank": c.get("market_cap_rank"),
                "total_volume": c.get("total_volume"),
                "high_24h": c.get("high_24h"),
                "low_24h": c.get("low_24h"),
            })

        # CoinGecko não devolve o total. Mantemos um valor simbólico (ou pode ser None).
        payload = {
            "count": 100,
            "next": None if len(data) < per_page else _build_page_url(request, page + 1, per_page, search),
            "previous": None if page == 1 else _build_page_url(request, page - 1, per_page, search),
            "results": results,
            "cached": False,
            "cached_at": cache.now_iso(),
        }

        cache.set_json("coins:list", payload, LIST_TTL, str(page), str(per_page), search)
        return response.Response(payload)


class CoinDetailView(views.APIView):
    """
    GET /api/coins/{coin_id}/
    Mapeia CoinGecko /coins/{id} para o payload plano exigido no desafio.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, coin_id):
        # 1) cache
        cached = cache.get_json("coins:detail", coin_id)
        if cached:
            cached["cached"] = True
            return response.Response(cached)

        # 2) fetch CoinGecko
        try:
            d = coingecko.coin_detail(coin_id)
        except Exception:
            return response.Response(
                {"detail": f"coin '{coin_id}' not found or upstream error"},
                status=status.HTTP_404_NOT_FOUND
            )

        md = d.get("market_data") or {}
        out = {
            "id": d.get("id"),
            "symbol": d.get("symbol"),
            "name": d.get("name"),
            "description": (d.get("description") or {}).get("en", ""),
            "image": (d.get("image") or {}).get("large")
                     or (d.get("image") or {}).get("small")
                     or (d.get("image") or {}).get("thumb"),
            "current_price": (md.get("current_price") or {}).get("usd"),
            "market_cap": (md.get("market_cap") or {}).get("usd"),
            "market_cap_rank": md.get("market_cap_rank") or d.get("market_cap_rank"),
            "total_volume": (md.get("total_volume") or {}).get("usd"),
            "high_24h": (md.get("high_24h") or {}).get("usd"),
            "low_24h": (md.get("low_24h") or {}).get("usd"),
            # price_change_24h: valor absoluto em USD (usamos em_currency se existir)
            "price_change_24h": (md.get("price_change_24h_in_currency") or {}).get("usd", md.get("price_change_24h")),
            "price_change_percentage_24h": md.get("price_change_percentage_24h"),
            "circulating_supply": md.get("circulating_supply"),
            "total_supply": md.get("total_supply"),
            "max_supply": md.get("max_supply"),
            "ath": (md.get("ath") or {}).get("usd"),
            "ath_date": (md.get("ath_date") or {}).get("usd"),
            "links": {
                "homepage": ((d.get("links") or {}).get("homepage") or [""])[0],
                "blockchain_site": ((d.get("links") or {}).get("blockchain_site") or [""])[0],
                "official_forum": ((d.get("links") or {}).get("official_forum_url") or [None])[0],
            },
            "cached": False,
            "cached_at": cache.now_iso(),
        }

        cache.set_json("coins:detail", out, DETAIL_TTL, coin_id)
        return response.Response(out)


class CoinChartView(views.APIView):
    """
    GET /api/coins/{coin_id}/chart/?days=7
    Retorna série histórica: {"prices": [[timestamp_ms, price], ...], "cached": bool}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, coin_id: str):
        days = (request.query_params.get("days") or "7").lower()
        allowed = {"1", "7", "30", "90", "365", "max"}
        if days not in allowed:
            # normaliza valores inválidos silenciosamente para "7"
            days = "7"

        # 1) cache
        cached = cache.get_json("coins:chart", coin_id, days)
        if cached:
            cached["cached"] = True
            return response.Response(cached, status=status.HTTP_200_OK)

        # 2) fetch CoinGecko
        try:
            raw = coingecko.coin_chart(coin_id, days)
        except Exception:
            return response.Response(
                {"detail": f"coin '{coin_id}' not found or upstream error"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3) resposta + cache
        payload = {
            "prices": raw.get("prices", []),
            "cached": False,
            "cached_at": cache.now_iso(),
        }
        cache.set_json("coins:chart", payload, CHART_TTL, coin_id, days)
        return response.Response(payload, status=status.HTTP_200_OK)
