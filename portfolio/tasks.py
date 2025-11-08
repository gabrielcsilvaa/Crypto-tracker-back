# portfolio/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import PriceAlert, Notification
from coins.services import coingecko  

@shared_task(name="portfolio.tasks.check_price_alerts")
def check_price_alerts():
    """
    Varre alerts ativos, busca preço atual no coingecko e dispara notificação
    quando o alvo é atingido. Marca 'triggered' e desativa se for o caso.
    """
    alerts = PriceAlert.objects.filter(is_active=True, triggered=False)
    # Agrupar por coin_id para reduzir chamadas (opcional: melhorar com cache)
    for alert in alerts:
        try:
            data = coingecko.coin_detail(alert.coin_id)
            price = (data.get("market_data", {})
                        .get("current_price", {})
                        .get("usd"))
            if price is None:
                continue

            hit = (
                (alert.condition == "above" and float(price) >= float(alert.target_price_usd))
                or
                (alert.condition == "below" and float(price) <= float(alert.target_price_usd))
            )

            if hit:
                with transaction.atomic():
                    # cria notificação
                    Notification.objects.create(
                        user=alert.user,
                        type="price_alert",
                        title=f"Alerta de preço — {alert.coin_symbol.upper()}",
                        message=(
                            f"{alert.coin_name} ({alert.coin_symbol.upper()}) "
                            f"atingiu ${price:.2f} (alvo: {alert.condition} ${float(alert.target_price_usd):.2f})"
                        ),
                        data={
                            "coin_id": alert.coin_id,
                            "coin_symbol": alert.coin_symbol,
                            "current_price_usd": float(price),
                            "target_price_usd": float(alert.target_price_usd),
                            "condition": alert.condition,
                        },
                        read=False,
                    )
                    # marca como disparado
                    alert.triggered = True
                    alert.triggered_at = timezone.now()
                    # Se preferir manter ativo para novo disparo futuro, não desative:
                    alert.is_active = False
                    alert.save(update_fields=["triggered", "triggered_at", "is_active"])
        except Exception:
            # Evita derrubar a task inteira por 1 erro; poderia logar aqui
            continue
