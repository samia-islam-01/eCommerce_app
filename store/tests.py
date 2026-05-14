from decimal import Decimal

from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product, Review, Store


def make_vendor(user):
    group, _ = Group.objects.get_or_create(name='Vendors')
    user.groups.add(group)


class ProductListCreateTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user('customer', password='pass')
        self.vendor = User.objects.create_user('vendor', password='pass', email='v@test.com')
        make_vendor(self.vendor)
        self.store = Store.objects.create(name='Test Store', owner=self.vendor)
        self.product = Product.objects.create(
            store=self.store, name='Widget', description='A widget', price=Decimal('9.99'), stock=10
        )

    def test_unauthenticated_returns_403(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_products_authenticated(self):
        self.client.force_login(self.customer)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Widget')

    def test_list_products_includes_reviews_field(self):
        self.client.force_login(self.customer)
        response = self.client.get('/api/products/')
        self.assertIn('reviews', response.data[0])

    def test_create_product_as_vendor(self):
        self.client.force_login(self.vendor)
        response = self.client.post('/api/products/', {
            'store': self.store.id,
            'name': 'Gadget',
            'description': 'A gadget',
            'price': '4.99',
            'stock': 5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Gadget')

    def test_create_product_as_customer_returns_403(self):
        self.client.force_login(self.customer)
        response = self.client.post('/api/products/', {
            'store': self.store.id, 'name': 'X', 'price': '1.00', 'stock': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_wrong_store_returns_400(self):
        other_vendor = User.objects.create_user('other', password='pass')
        make_vendor(other_vendor)
        other_store = Store.objects.create(name='Other Store', owner=other_vendor)
        self.client.force_login(self.vendor)
        response = self.client.post('/api/products/', {
            'store': other_store.id, 'name': 'X', 'price': '1.00', 'stock': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductDetailTests(APITestCase):
    def setUp(self):
        self.vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(self.vendor)
        self.store = Store.objects.create(name='Store', owner=self.vendor)
        self.product = Product.objects.create(
            store=self.store, name='Widget', price=Decimal('9.99'), stock=10
        )
        self.other_vendor = User.objects.create_user('other_vendor', password='pass')
        make_vendor(self.other_vendor)
        self.other_store = Store.objects.create(name='Other', owner=self.other_vendor)

    def test_get_product_detail(self):
        self.client.force_login(self.vendor)
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Widget')

    def test_get_nonexistent_product_returns_404(self):
        self.client.force_login(self.vendor)
        response = self.client.get('/api/products/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_product_as_owner(self):
        self.client.force_login(self.vendor)
        response = self.client.patch(f'/api/products/{self.product.id}/', {'price': '14.99'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('14.99'))

    def test_patch_product_as_non_owner_returns_403(self):
        self.client.force_login(self.other_vendor)
        response = self.client.patch(f'/api/products/{self.product.id}/', {'price': '1.00'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_product_as_owner(self):
        self.client.force_login(self.vendor)
        response = self.client.delete(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_delete_product_as_non_owner_returns_403(self):
        self.client.force_login(self.other_vendor)
        response = self.client.delete(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MyProductsTests(APITestCase):
    def setUp(self):
        self.vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(self.vendor)
        self.store = Store.objects.create(name='Store', owner=self.vendor)
        Product.objects.create(store=self.store, name='Mine', price=Decimal('1.00'), stock=1)

        self.other_vendor = User.objects.create_user('other', password='pass')
        make_vendor(self.other_vendor)
        other_store = Store.objects.create(name='Other', owner=self.other_vendor)
        Product.objects.create(store=other_store, name='Theirs', price=Decimal('2.00'), stock=2)

        self.customer = User.objects.create_user('customer', password='pass')

    def test_vendor_sees_only_own_products(self):
        self.client.force_login(self.vendor)
        response = self.client.get('/api/products/mine/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.data]
        self.assertIn('Mine', names)
        self.assertNotIn('Theirs', names)

    def test_customer_returns_403(self):
        self.client.force_login(self.customer)
        response = self.client.get('/api/products/mine/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StoreTests(APITestCase):
    def setUp(self):
        self.vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(self.vendor)
        self.store = Store.objects.create(name='My Store', owner=self.vendor)
        self.customer = User.objects.create_user('customer', password='pass')

    def test_list_own_stores(self):
        self.client.force_login(self.vendor)
        response = self.client.get('/api/stores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'My Store')

    def test_create_store_as_vendor(self):
        self.client.force_login(self.vendor)
        response = self.client.post('/api/stores/', {'name': 'New Store'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Store')

    def test_create_store_as_customer_returns_403(self):
        self.client.force_login(self.customer)
        response = self.client.post('/api/stores/', {'name': 'Sneaky Store'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_store(self):
        self.client.force_login(self.vendor)
        response = self.client.patch(f'/api/stores/{self.store.id}/', {'name': 'Renamed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.store.refresh_from_db()
        self.assertEqual(self.store.name, 'Renamed')

    def test_delete_store(self):
        self.client.force_login(self.vendor)
        response = self.client.delete(f'/api/stores/{self.store.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Store.objects.filter(id=self.store.id).exists())

    def test_cannot_access_other_users_store(self):
        other = User.objects.create_user('other_vendor', password='pass')
        make_vendor(other)
        self.client.force_login(other)
        response = self.client.get(f'/api/stores/{self.store.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', password='pass')
        vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(vendor)
        store = Store.objects.create(name='Store', owner=vendor)
        self.product = Product.objects.create(
            store=store, name='Widget', price=Decimal('5.00'), stock=20
        )

    def test_empty_cart(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['total'], 0)

    def test_add_item_to_cart(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart']['Widget'], 3)

    def test_cart_view_returns_correct_subtotals(self):
        self.client.force_login(self.user)
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 2})
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data['items'][0]
        self.assertEqual(item['quantity'], 2)
        self.assertAlmostEqual(item['subtotal'], 10.0)
        self.assertAlmostEqual(response.data['total'], 10.0)

    def test_add_item_increments_existing_quantity(self):
        self.client.force_login(self.user)
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 1})
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 2})
        response = self.client.get('/api/cart/')
        self.assertEqual(response.data['items'][0]['quantity'], 3)

    def test_clear_cart(self):
        self.client.force_login(self.user)
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 1})
        response = self.client.delete('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.data['items'], [])

    def test_add_item_missing_name_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/cart/', {'quantity': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cart_returns_403(self):
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CheckoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', password='pass', email='user@test.com')
        vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(vendor)
        store = Store.objects.create(name='Store', owner=vendor)
        self.product = Product.objects.create(
            store=store, name='Widget', price=Decimal('5.00'), stock=10
        )

    def test_checkout_empty_cart_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/checkout/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_clears_cart_and_returns_total(self):
        self.client.force_login(self.user)
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 2})
        response = self.client.post('/api/checkout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertAlmostEqual(response.data['total'], 10.0)
        # Cart should be empty afterwards
        cart_response = self.client.get('/api/cart/')
        self.assertEqual(cart_response.data['items'], [])

    def test_checkout_marks_product_as_purchased(self):
        self.client.force_login(self.user)
        self.client.post('/api/cart/', {'item': 'Widget', 'quantity': 1})
        self.client.post('/api/checkout/')
        # Review should now be verified
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/', {'text': 'Great!'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['verified'])


class ReviewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', password='pass', email='u@test.com')
        vendor = User.objects.create_user('vendor', password='pass')
        make_vendor(vendor)
        store = Store.objects.create(name='Store', owner=vendor)
        self.product = Product.objects.create(
            store=store, name='Widget', price=Decimal('5.00'), stock=10
        )

    def test_review_unverified_without_purchase(self):
        self.client.force_login(self.user)
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/', {'text': 'Nice'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['verified'])

    def test_review_missing_text_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post(f'/api/products/{self.product.id}/reviews/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_nonexistent_product_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/products/9999/reviews/', {'text': 'Hi'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)