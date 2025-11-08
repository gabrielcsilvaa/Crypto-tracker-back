from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from utils.health_check import health
from core.views import TriggerTaskView

urlpatterns = [
    path("admin/", admin.site.urls),

    # health check
    path("api/health/", health),

    # documentação da API
    path("api/docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # endpoint para disparar task celery manualmente
    path("api/tasks/trigger/", TriggerTaskView.as_view(), name="trigger-task"),

    # apps
    path("api/auth/", include("authentication.urls")),
    path("api/coins/", include("coins.urls")),
    path("api/portfolio/", include("portfolio.urls")),
]
