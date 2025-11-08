from rest_framework import views, permissions, response, status
from coins.tasks import update_coin_prices_cache

class TriggerTaskView(views.APIView):
    """
    Endpoint para disparar manualmente uma task Celery.
    Útil para testes e monitoramento.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        task = update_coin_prices_cache.delay()
        return response.Response(
            {"message": "Task enviada para execução", "task_id": str(task.id)},
            status=status.HTTP_202_ACCEPTED
        )
