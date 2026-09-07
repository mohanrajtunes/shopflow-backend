from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, Product, CartItem, Order

User = get_user_model()


class ShopFlowSecurityTests(APITestCase):

    def setUp(self):
        # Users
        self.admin = User.objects.create_superuser(
            username='admin_boss', password='password123', email='admin@shop.com', role='admin'
        )
        self.vendor = User.objects.create_user(
            username='vendor_guy', password='password123', email='vendor@shop.com', role='vendor'
        )
        self.other_vendor = User.objects.create_user(
            username='other_vendor', password='password123', email='other@shop.com', role='vendor'
        )
        self.customer = User.objects.create_user(
            username='buyer_guy', password='password123', email='buyer@shop.com', role='customer'
        )

        # Category + Product
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            title="Alien Mouse",
            description="Owned by another vendor",
            price="50.00",
            stock=10,
            category=self.category,
            vendor=self.other_vendor
        )

    def test_1_vendor_can_create_product(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "title": "Mechanical Keyboard",
            "description": "RGB gaming keyboard",
            "price": "150.00",
            "stock": 10,
            "category": self.category.id
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_2_customer_cannot_create_product(self):
        self.client.force_authenticate(user=self.customer)
        data = {
            "title": "Hacked Item",
            "description": "Should fail",
            "price": "10.00",
            "stock": 5,
            "category": self.category.id
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_3_unauthenticated_user_cannot_create_product(self):
        data = {
            "title": "Ghost Item",
            "description": "Anonymous post",
            "price": "5.00",
            "stock": 1,
            "category": self.category.id
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_4_anyone_can_view_products(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_5_vendor_cannot_edit_other_vendors_product(self):
        self.client.force_authenticate(user=self.vendor)
        url = f'/api/products/{self.product.id}/'
        response = self.client.patch(url, {"price": "1.00"}, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_6_orders_admin_access(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_7_customer_orders_isolated(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_8_checkout_prevents_overselling(self):
        """Checkout should fail when quantity > available stock"""
        self.client.force_authenticate(user=self.customer)

        # First add an item to cart with quantity higher than stock
        CartItem.objects.create(
            user=self.customer,
            product=self.product,
            quantity=999
        )

        response = self.client.post('/api/orders/checkout/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Stock should remain unchanged because of atomic rollback
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_9_successful_checkout_reduces_stock(self):
        """Happy path: checkout should reduce stock and create order"""
        self.client.force_authenticate(user=self.customer)

        CartItem.objects.create(
            user=self.customer,
            product=self.product,
            quantity=3
        )

        response = self.client.post('/api/orders/checkout/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(Order.objects.filter(customer=self.customer).count(), 1)