from django.urls import path
from .views import CoinsListView, CoinDetailView, CoinChartView

urlpatterns = [
    path("", CoinsListView.as_view()),
    path("<str:coin_id>/", CoinDetailView.as_view()),
    path("<str:coin_id>/chart/", CoinChartView.as_view()),
]
