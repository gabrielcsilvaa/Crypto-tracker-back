from rest_framework import generics, permissions, views, response, status
from django.db.models import Sum, F
from .models import Favorite, PortfolioHolding, PriceAlert, Notification
from .serializers import FavoriteSerializer, HoldingSerializer, PriceAlertSerializer, NotificationSerializer
from coins.services import coingecko


class PortfolioView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        holdings = PortfolioHolding.objects.filter(user=request.user)
        total_invested = sum([float(h.amount * h.purchase_price_usd) for h in holdings])
        total_current = 0.0
        for h in holdings:
            d = coingecko.coin_detail(h.coin_id)
            p = d.get("market_data", {}).get("current_price", {}).get("usd")
            if p:
                total_current += float(h.amount) * float(p)
        profit = total_current - total_invested
        pct = (profit / total_invested * 100.0) if total_invested else 0.0
        return response.Response({
            "total_value_usd": round(total_current, 2),
            "total_invested_usd": round(total_invested, 2),
            "total_profit_usd": round(profit, 2),
            "total_profit_percentage": round(pct, 2),
            "holdings": HoldingSerializer(holdings, many=True, context={"request": request}).data
        })

    def post(self, request):
        serializer = HoldingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

class FavoriteListCreate(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

class FavoriteDelete(generics.DestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

class HoldingListCreate(generics.ListCreateAPIView):
    serializer_class = HoldingSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return PortfolioHolding.objects.filter(user=self.request.user)

class HoldingUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HoldingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    def get_queryset(self):
        return PortfolioHolding.objects.filter(user=self.request.user)

class AlertListCreate(generics.ListCreateAPIView):
    serializer_class = PriceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user, is_active=True)

class AlertDelete(generics.DestroyAPIView):
    serializer_class = PriceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)

class NotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkRead(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request, id):
        n = Notification.objects.get(user=request.user, id=id)
        n.read = True
        n.save()
        return response.Response({"id": str(n.id), "read": True})
