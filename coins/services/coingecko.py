import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

# Base URL e autenticação (Demo)
BASE = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3").rstrip("/")
COINGECKO_KEY = os.getenv("COINGECKO_KEY", "")
USE_QUERY_KEY = os.getenv("COINGECKO_KEY_IN_QUERY", "0") == "1"  # por segurança, manter 0

# Resiliência / timeouts
DEFAULT_TIMEOUT = float(os.getenv("COINGECKO_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("COINGECKO_MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("COINGECKO_BACKOFF_BASE", "0.7"))  # segundos


def _build_headers() -> Dict[str, str]:
    """
    Monta headers, incluindo o x-cg-demo-api-key (método recomendado pela CoinGecko).
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "CryptoTracker-Backend/1.0",
    }
    if COINGECKO_KEY and not USE_QUERY_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    return headers


def _inject_key_in_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    (Opcional, não recomendado) Permite mandar a chave via query string
    se COINGECKO_KEY_IN_QUERY=1 — mantenha 0 para usar header.
    """
    params = dict(params or {})
    if COINGECKO_KEY and USE_QUERY_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_KEY
    return params


def _request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Tuple[int, Any]:
    """
    Faz a request com retry/backoff em 429/502/503/504 e erros de rede.
    Retorna (status_code, json|text).
    """
    url = urljoin(BASE + "/", path.lstrip("/"))
    headers = _build_headers()
    params = _inject_key_in_params(params)
    timeout = timeout or DEFAULT_TIMEOUT

    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.request(method, url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as exc:
            if attempt <= MAX_RETRIES:
                sleep_for = BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning("CoinGecko network error (%s). retry %d/%d in %.2fs", exc, attempt, MAX_RETRIES, sleep_for)
                time.sleep(sleep_for)
                continue
            raise

        if resp.status_code in (429, 502, 503, 504):
            if attempt <= MAX_RETRIES:
                retry_after = resp.headers.get("Retry-After")
                sleep_for = float(retry_after) if retry_after and retry_after.isdigit() else BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning("CoinGecko %s for %s. retry %d/%d in %.2fs", resp.status_code, url, attempt, MAX_RETRIES, sleep_for)
                time.sleep(sleep_for)
                continue

        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        return resp.status_code, data


# --------- Helpers públicos usados pelos views/serviços ---------

def ping() -> Dict[str, Any]:
    status, data = _request("GET", "/ping")
    if status != 200:
        raise RuntimeError(f"CoinGecko ping failed: {status} - {data}")
    return data

def list_markets(page: int = 1, per_page: int = 20, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    /coins/markets — lista moedas com preços.
    'search' não é suportado nativamente aqui; se quiser buscar por texto,
    você pode usar /search para obter 'ids' e filtrar (não implementado aqui para manter compatível).
    """
    params: Dict[str, Any] = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": min(max(per_page, 1), 250),
        "page": max(page, 1),
        "sparkline": "false",
        "price_change_percentage": "24h",
        "locale": "en",
    }
    # Mantém compatível com sua assinatura atual:
    # se precisar realmente aplicar 'search' na CG, posso te adicionar um search_ids() depois.
    status, data = _request("GET", "/coins/markets", params=params)
    if status != 200 or not isinstance(data, list):
        raise RuntimeError(f"CoinGecko markets failed: {status} - {data}")
    return data

def coin_detail(coin_id: str) -> Dict[str, Any]:
    """
    /coins/{id} — detalhes com market_data (usado no PortfolioSummary e afins).
    """
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    status, data = _request("GET", f"/coins/{coin_id}", params=params)
    if status != 200 or not isinstance(data, dict):
        raise RuntimeError(f"CoinGecko coin detail failed: {status} - {data}")
    return data

def coin_chart(coin_id: str, days: int | str = 7) -> Dict[str, Any]:
    """
    /coins/{id}/market_chart — séries para gráficos. days: 1,7,30,90,365,max
    """
    params = {"vs_currency": "usd", "days": str(days)}
    status, data = _request("GET", f"/coins/{coin_id}/market_chart", params=params)
    if status != 200 or not isinstance(data, dict):
        raise RuntimeError(f"CoinGecko market chart failed: {status} - {data}")
    return data
