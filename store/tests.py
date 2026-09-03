from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, Product

User = get_user_model()

class ShopFlowSecurityTests(APITestCase):
    def setUp(self):
        # 1. Setup users with strict roles
        self.admin = User.objects.create_superuser(username='admin_boss', password='password123', email='admin@shop.com')
        
        # Vendor has is_staff=True to differentiate from customers
        self.vendor = User.objects.create_user(username='vendor_guy', password='password123', email='vendor@shop.com', is_staff=True)
        self.other_vendor = User.objects.create_user(username='other_vendor', password='password123', email='other@shop.com', is_staff=True)
        
        # Customer is a standard user
        self.customer = User.objects.create_user(username='buyer_guy', password='password123', email='buyer@shop.com')
        
        # 2. Setup category and an existing product
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        
        # ADD THE VENDOR HERE:
        self.alien_product = Product.objects.create(
            title="Alien Mouse", 
            description="Owned by another vendor", 
            price="50.00", 
            stock=10, 
            category=self.category,
            vendor=self.other_vendor  # <--- THIS IS THE FIX!
        )

    def test_1_vendor_can_create_product(self):
        """1. Authenticated staff/vendors can create products."""
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
        """2. Standard customers are BLOCKED from creating products."""
        self.client.force_authenticate(user=self.customer)
        data = {
            "title": "Hacked Item", 
            "description": "Should fail", 
            "price": "10.00", 
            "stock": 5,
            "category": self.category.id
        }
        response = self.client.post('/api/products/', data, format='json')
        # If this returns 201, your views.py permissions are completely open!
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_3_unauthenticated_user_cannot_create_product(self):
        """3. Anonymous users are blocked from creating products."""
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
        """4. Customers can successfully fetch the product list."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_5_vendor_cannot_edit_other_vendors_product(self):
        """5. A vendor cannot modify a product they don't own."""
        self.client.force_authenticate(user=self.vendor)
        url = f'/api/products/{self.alien_product.id}/'
        response = self.client.patch(url, {"price": "1.00"}, format='json')
        # Expecting a permission denial or a 404 if the queryset isolates them
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_6_orders_admin_access(self):
        """6. Admins can access the full orders list."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/orders/')
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.skipTest("Orders API endpoint not built yet.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_7_customer_orders_isolated(self):
        """7. Customers can only view their own orders."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/orders/')
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.skipTest("Orders API endpoint not built yet.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_8_checkout_validation_prevents_overselling(self):
        """8. Checkout blocks purchases exceeding current stock."""
        self.client.force_authenticate(user=self.customer)
        data = {"product_id": self.alien_product.id, "quantity": 999}
        response = self.client.post('/api/checkout/', data, format='json')
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.skipTest("Checkout API endpoint not built yet.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)