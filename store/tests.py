from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Category, Product, CartItem, Order

class ShopFlowTests(APITestCase):

    def setUp(self):
        # Create a vendor
        self.vendor = User.objects.create_user(
            username='vendor1', password='password123', role='vendor'
        )
        # Create a customer
        self.customer = User.objects.create_user(
            username='customer1', password='password123', role='customer'
        )
        # Create a category
        self.category = Category.objects.create(name='Electronics', slug='electronics')

        # Create a product owned by the vendor
        self.product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            title='Wireless Mouse',
            description='A great mouse',
            price=500.00,
            stock=10
        )
        
        self.cart_url = reverse('cart-list')
        self.checkout_url = reverse('orders-checkout')

    def test_customer_can_add_to_cart_and_checkout(self):
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)

        # 1. Add product to cart
        cart_data = {'product': self.product.id, 'quantity': 2}
        response = self.client.post(self.cart_url, cart_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Trigger atomic checkout
        checkout_response = self.client.post(self.checkout_url)
        self.assertEqual(checkout_response.status_code, status.HTTP_201_CREATED)

        # 3. Verify stock was reduced from 10 to 8
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # 4. Verify order was created
        self.assertEqual(Order.objects.filter(customer=self.customer).count(), 1)

    def test_checkout_fails_on_insufficient_stock(self):
        self.client.force_authenticate(user=self.customer)

        # Try to buy 15 items when only 10 are in stock
        CartItem.objects.create(user=self.customer, product=self.product, quantity=15)

        checkout_response = self.client.post(self.checkout_url)
        self.assertEqual(checkout_response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify stock remains unchanged (atomic rollback)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)


