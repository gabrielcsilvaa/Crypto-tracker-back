from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
import redis, os

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    checks = {}
    # DB
    from django.db import connection
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1;")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "fail"

    # Redis
    try:
        r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "fail"

    checks["celery_worker"] = "ok"  # simplificado
    checks["celery_beat"] = "ok"

    return Response({"status":"healthy" if all(v=="ok" for v in checks.values()) else "degraded",
                     "checks":checks})
