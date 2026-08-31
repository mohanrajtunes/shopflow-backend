from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, CategoryViewSet, ProductViewSet, CartItemViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'cart', CartItemViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]