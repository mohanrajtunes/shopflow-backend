from rest_framework import serializers
from .models import User, Category, Product, CartItem, Order, OrderItem

class UserRegistrationSerializers(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'phone_number')
    def create(self, validated_data):
        password = validated_data.pop('password')
        if validated_data.get('role') not in ['customer', 'vendor']:
            validated_data['role'] = 'customer'
            
        user = User.objects.create_user(password=password, **validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    vendor_username = serializers.ReadOnlyField(source='vendor.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['vendor']

class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')
    product_price = serializers.ReadOnlyField(source='product.price')
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem 
        fields = ('id', 'product', 'product_title', 'product_price', 'quantity', 'subtotal', 'created_at')
        read_only_fields = ['user']

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')

    class Meta:
        model = OrderItem
        fields = ('id', 'product_title', 'quantity', 'price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_username = serializers.ReadOnlyField(source='customer.username')

    class Meta:
        model = Order
        fields = ('id', 'customer_username', 'status', 'total_price', 'created_at', 'items')
        read_only_fields = ['customer', 'total_price', 'status']