from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .permissions import IsAdminOrReadOnly
from .filters import ProductFilter
from .models import User, Category, Product, CartItem, Order, OrderItem
from .serializers import (
    UserRegistrationSerializers,
    CategorySerializer,
    ProductSerializer,
    CartItemSerializer,
    OrderSerializer
)


class IsVendorAndOwnerOrReadOnly(permissions.BasePermission):
    """
    Anyone can view products.
    Only authenticated vendors can create products.
    A vendor can only edit/delete their own products.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'vendor'
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.vendor == request.user


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializers


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsVendorAndOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
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
        if getattr(user, 'role', None) == 'admin':
            return Order.objects.all()
        return Order.objects.filter(customer=user)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        Atomic checkout with row-level locking to prevent overselling.
        """
        user = request.user
        cart_items = user.cart_items.all()

        if not cart_items.exists():
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                total_price = 0
                order_items_to_create = []

                for cart_item in cart_items:
                    # Lock the product row so concurrent requests wait
                    product = Product.objects.select_for_update().get(
                        id=cart_item.product.id
                    )

                    if product.stock < cart_item.quantity:
                        raise ValidationError(
                            f"Insufficient stock for '{product.title}'. "
                            f"Only {product.stock} left."
                        )

                    product.stock -= cart_item.quantity
                    product.save()

                    item_total = product.price * cart_item.quantity
                    total_price += item_total

                    order_items_to_create.append({
                        'product': product,
                        'quantity': cart_item.quantity,
                        'price': product.price
                    })

                order = Order.objects.create(
                    customer=user,
                    total_price=total_price,
                    status='pending'
                )

                for item_data in order_items_to_create:
                    OrderItem.objects.create(order=order, **item_data)

                # Clear the cart only after successful order creation
                cart_items.delete()

                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )