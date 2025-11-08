from django.urls import path
from .views import (
  FavoriteListCreate, FavoriteDelete,
  HoldingListCreate, HoldingUpdateDelete, PortfolioView,
  AlertListCreate, AlertDelete,
  NotificationList, NotificationMarkRead,
)

urlpatterns = [
  path("favorites/", FavoriteListCreate.as_view()),
  path("favorites/<uuid:id>/", FavoriteDelete.as_view()),
  path("", PortfolioView.as_view()),
  path("holdings/", HoldingListCreate.as_view()),
  path("holdings/<uuid:id>/", HoldingUpdateDelete.as_view()),
  path("alerts/", AlertListCreate.as_view()),
  path("alerts/<uuid:id>/", AlertDelete.as_view()),
  path("notifications/", NotificationList.as_view()),
  path("notifications/<uuid:id>/read/", NotificationMarkRead.as_view()),
]
