from rest_framework import serializers
from .models import Product, Review, Store


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'verified']
        read_only_fields = ['id', 'user', 'verified']


class ProductSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'store', 'store_name', 'name', 'description', 'image', 'price', 'stock', 'reviews']
        read_only_fields = ['id', 'store_name', 'reviews']


class StoreSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Store
        fields = ['id', 'name', 'description', 'logo', 'owner']
        read_only_fields = ['id', 'owner']