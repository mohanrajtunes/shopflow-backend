from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .permissions import IsVendorOrReadOnly
from .filters import ProductFilter
from rest_framework import filters
from .models import User, Category, Product, CartItem, Order
from .serializers import(
    UserRegistrationSerializers,
    CategorySerializer,
    ProductSerializer,
    CartItemSerializer,
    OrderSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializers

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes =[AllowAny]
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsVendorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter  # <--- Use custom filter class here
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        return Order.objects.filter(customer=user)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        user = request.user
        cart_items = user.cart_items.all()
        
        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Atomic transaction & row-level locking to prevent race conditions
        try:
            with transaction.atomic():
                total_price = 0
                order_items_to_create = []

                for cart_item in cart_items:
                    # select_for_update locks the product row to handle concurrency safely
                    product = Product.objects.select_for_update().get(id=cart_item.product.id)

                    if product.stock < cart_item.quantity:
                        raise ValidationError(f"Insufficient stock for '{product.title}'. Only {product.stock} left.")

                    product.stock -= cart_item.quantity
                    product.save()

                    item_total = product.price * cart_item.quantity
                    total_price += item_total

                    order_items_to_create.append({
                        'product': product,
                        'quantity': cart_item.quantity,
                        'price': product.price
                    })

                order = Order.objects.create(customer=user, total_price=total_price, status='pending')

                for item_data in order_items_to_create:
                    from .models import OrderItem
                    OrderItem.objects.create(order=order, **item_data)

                # Clear cart after successful checkout
                cart_items.delete()

                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
