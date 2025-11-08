from rest_framework import serializers
from .models import Favorite, PortfolioHolding, PriceAlert, Notification
from coins.services import coingecko

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = "__all__"
        read_only_fields = ("id","user","coin_name","coin_symbol","coin_image","created_at")

    def create(self, validated_data):
        # Enriquecer com dados da moeda
        d = coingecko.coin_detail(validated_data["coin_id"])
        validated_data["user"] = self.context["request"].user
        validated_data["coin_name"] = d.get("name")
        validated_data["coin_symbol"] = d.get("symbol")
        validated_data["coin_image"] = (d.get("image") or {}).get("small") or (d.get("image") or {}).get("thumb")
        return super().create(validated_data)

class HoldingSerializer(serializers.ModelSerializer):
    current_price_usd = serializers.SerializerMethodField()
    invested_value_usd = serializers.SerializerMethodField()
    current_value_usd = serializers.SerializerMethodField()
    profit_usd = serializers.SerializerMethodField()
    profit_percentage = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioHolding
        fields = "__all__"
        read_only_fields = ("id","user","coin_name","coin_symbol","coin_image","created_at","updated_at",
                            "current_price_usd","invested_value_usd","current_value_usd","profit_usd","profit_percentage")

    def _price(self, obj):
        d = coingecko.coin_detail(obj.coin_id)
        return d.get("market_data",{}).get("current_price",{}).get("usd")

    def get_current_price_usd(self, obj):
        p = self._price(obj); return float(p) if p else None

    def get_invested_value_usd(self, obj):
        return float(obj.amount * obj.purchase_price_usd)

    def get_current_value_usd(self, obj):
        p = self._price(obj); 
        return float(obj.amount) * float(p) if p else None

    def get_profit_usd(self, obj):
        cv = self.get_current_value_usd(obj); iv = self.get_invested_value_usd(obj)
        return None if cv is None else float(cv - iv)

    def get_profit_percentage(self, obj):
        iv = self.get_invested_value_usd(obj)
        prof = self.get_profit_usd(obj)
        return None if prof is None or iv == 0 else float(100.0 * prof / iv)

    def create(self, validated_data):
        d = coingecko.coin_detail(validated_data["coin_id"])
        validated_data["user"] = self.context["request"].user
        validated_data["coin_name"] = d.get("name")
        validated_data["coin_symbol"] = d.get("symbol")
        validated_data["coin_image"] = (d.get("image") or {}).get("small") or (d.get("image") or {}).get("thumb")
        return super().create(validated_data)

class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = "__all__"
        read_only_fields = ("id","user","triggered","triggered_at","created_at")

    def create(self, validated_data):
        d = coingecko.coin_detail(validated_data["coin_id"])
        validated_data["user"] = self.context["request"].user
        validated_data["coin_name"] = d.get("name")
        validated_data["coin_symbol"] = d.get("symbol")
        return super().create(validated_data)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ("id","user","created_at")
