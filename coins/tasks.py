from celery import shared_task
from .services import coingecko, cache

@shared_task
def update_coin_prices_cache():
    # Atualiza cache da lista top 100
    data = coingecko.list_markets(page=1, per_page=100)
    out = {"count":100,"next":None,"previous":None,"results":[]}
    for c in data:
        out["results"].append({
            "id": c["id"], "symbol": c["symbol"], "name": c["name"],
            "image": c.get("image"),
            "current_price": c.get("current_price"),
            "price_change_24h": c.get("price_change_24h"),
            "price_change_percentage_24h": c.get("price_change_percentage_24h"),
            "market_cap": c.get("market_cap"),
            "market_cap_rank": c.get("market_cap_rank"),
            "total_volume": c.get("total_volume"),
            "high_24h": c.get("high_24h"),
            "low_24h": c.get("low_24h"),
            "cached": True, "cached_at": cache.now_iso(),
        })
    cache.set_json("coins:list", out, 300, "1", "100", "")
