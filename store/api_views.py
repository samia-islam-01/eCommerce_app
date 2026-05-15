from django.core.mail import send_mail

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Review, Store
from .serializers import ProductSerializer, ReviewSerializer, StoreSerializer


def _is_vendor(user):
    return user.groups.filter(name='Vendors').exists()


# Products

class ProductListCreateView(APIView):
    def get(self):
        products = Product.objects.prefetch_related('reviews').all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can create products.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        store_id = request.data.get('store')
        try:
            store = Store.objects.get(id=store_id, owner=request.user)
        except Store.DoesNotExist:
            return Response(
                {'error': 'Invalid or unauthorised store.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(store=store)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    def _get_product(self, product_id):
        try:
            return Product.objects.prefetch_related('reviews').get(id=product_id)
        except Product.DoesNotExist:
            return None

    def get(self, product_id):
        product = self._get_product(product_id)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    def patch(self, request, product_id):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can edit products.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        product = self._get_product(product_id)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not product.store or product.store.owner != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can delete products.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        product = self._get_product(product_id)
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not product.store or product.store.owner != request.user:
            return Response({'error': 'You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyProductsView(APIView):

    def get(self, request):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        products = Product.objects.filter(store__owner=request.user).prefetch_related('reviews')
        return Response(ProductSerializer(products, many=True).data)


# Stores

class StoreListCreateView(APIView):

    def get(self, request):
        stores = Store.objects.filter(owner=request.user)
        return Response(StoreSerializer(stores, many=True).data)

    def post(self, request):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can create stores.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDetailView(APIView):

    def _get_store(self, store_id, user):
        try:
            return Store.objects.get(id=store_id, owner=user)
        except Store.DoesNotExist:
            return None

    def get(self, request, store_id):
        store = self._get_store(store_id, request.user)
        if not store:
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StoreSerializer(store).data)

    def patch(self, request, store_id):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can edit stores.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        store = self._get_store(store_id, request.user)
        if not store:
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, store_id):
        if not _is_vendor(request.user):
            return Response(
                {'error': 'Only vendors can delete stores.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        store = self._get_store(store_id, request.user)
        if not store:
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Cart

class CartView(APIView):
    def get(self, request):
        cart = request.session.get('cart', {})
        items = []
        total = 0.0

        for name, quantity in cart.items():
            try:
                product = Product.objects.get(name=name)
                subtotal = float(product.price) * quantity
                items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': quantity,
                    'subtotal': subtotal,
                })
                total += subtotal
            except Product.DoesNotExist:
                pass

        return Response({'items': items, 'total': round(total, 2)})

    def post(self, request):
        name = request.data.get('item')
        if not name:
            return Response({'error': 'Item name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(request.data.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1

        cart = request.session.get('cart', {})
        cart[name] = cart.get(name, 0) + quantity
        request.session['cart'] = cart
        request.session.modified = True

        return Response({'cart': cart}, status=status.HTTP_200_OK)

    def delete(self, request):
        request.session['cart'] = {}
        request.session.modified = True
        return Response(status=status.HTTP_204_NO_CONTENT)


# Checkout

class CheckoutView(APIView):
    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        items = []
        total = 0.0

        for name, qty in cart.items():
            try:
                product = Product.objects.get(name=name)
            except Product.DoesNotExist:
                continue
            subtotal = float(product.price) * qty
            total += subtotal
            items.append({
                'name': product.name,
                'qty': qty,
                'price': float(product.price),
                'subtotal': round(subtotal, 2),
            })

        # Record purchased products for verified review eligibility
        purchased = request.session.get('purchased_products', [])
        for name in cart:
            if name not in purchased:
                purchased.append(name)
        request.session['purchased_products'] = purchased

        # Send invoice email
        message = "ORDER INVOICE\n\n"
        for item in items:
            message += f"{item['name']} x{item['qty']} - £{item['subtotal']:.2f}\n"
        message += f"\nTOTAL: £{total:.2f}"

        send_mail(
            'Your Order Invoice',
            message,
            'samia14islam@gmail.com',
            [request.user.email],
        )

        request.session['cart'] = {}
        request.session.modified = True

        return Response(
            {'items': items, 'total': round(total, 2)},
            status=status.HTTP_200_OK,
        )


# Reviews

class ReviewCreateView(APIView):
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        text = request.data.get('text')
        if not text:
            return Response({'error': 'Review text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        purchased = request.session.get('purchased_products', [])
        is_verified = product.name in purchased

        review = Review.objects.create(
            product=product,
            user=request.user,
            text=text,
            verified=is_verified,
        )
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)