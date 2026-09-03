from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .permissions import IsVendorOrReadOnly
from .filters import ProductFilter
from rest_framework import filters
from .permissions import IsAdminOrReadOnly
from .models import User, Category, Product, CartItem, Order, OrderItem
from .serializers import(
    UserRegistrationSerializers,
    CategorySerializer,
    ProductSerializer,
    CartItemSerializer,
    OrderSerializer
)
from rest_framework.views import APIView

class IsVendorAndOwnerOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        # Allow anyone to view the product list (GET)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Block customers: Only allow authenticated staff/vendors to POST/PUT/DELETE
        return bool(
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, 'role', None) == 'vendor'
    )

    def has_object_permission(self, request, view, obj):
        # Allow anyone to view a specific product details (GET)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Block other vendors: You can only edit if you are the vendor who created it
        return obj.vendor == request.user
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializers

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes =[IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # Apply our new strict security rules:
    permission_classes = [IsVendorAndOwnerOrReadOnly]
    
    # Auto-assign the product's vendor to the user who is logged in making the request
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

class CheckoutView(APIView):
    # Only logged-in customers can checkout
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        
        # Safely convert quantity to an integer
        try:
            quantity = int(request.data.get('quantity', 1))
        except ValueError:
            return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. The Validation Wall: If they try to buy more than we have, BLOCK IT (400)
        if quantity > product.stock:
            return Response({"error": "Insufficient stock!"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. The Atomic Checkout: Lock the database row, deduct stock, and save
        with transaction.atomic():
            # select_for_update() prevents race conditions if 2 people buy at the exact same millisecond
            locked_product = Product.objects.select_for_update().get(id=product_id)
            
            if quantity > locked_product.stock:
                return Response({"error": "Insufficient stock!"}, status=status.HTTP_400_BAD_REQUEST)
            
            locked_product.stock -= quantity
            locked_product.save()

            # (Later, you can add your Order and OrderItem creation here)

        return Response({"message": "Checkout successful!"}, status=status.HTTP_200_OK)