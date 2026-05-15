from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from .models import Product, Review, Store
from .twitter_utils import tweet_new_product, tweet_new_store


def is_vendor(user):
    return user.groups.filter(name='Vendors').exists()


@login_required
def view_product_page(request):
    user = request.user

    # Check permissions to view products
    if user.has_perm('store.view_product') or user.has_perm('store.view_products'):
        if request.method == 'POST':
            product_name = request.POST.get('product')

            if not product_name:
                # If no product name given, show error on page
                return render(request, 'store/product_page.html', {
                    'error': 'No product name was given.'
                })

            try:
                product = Product.objects.get(name=product_name)
                return render(request, 'store/product_page.html', {'product': product})
            except ObjectDoesNotExist:
                # If product not found, show error
                return render(request, 'store/product_page.html', {
                    'error': 'Product not found.'
                })

        # If page is opened normally, just show empty form
        return render(request, 'store/product_page.html')

    # If user does not have permission to view products, show error
    return render(request, 'store/product_page.html', {
        'error': 'You do not have permission to view this product.'
    })


@login_required
def change_product_price(request):
    user = request.user

    # Check permissions to change products
    if user.has_perm('store.change_product') or user.has_perm('store.change_products'):
        if request.method == 'POST':
            product_name = request.POST.get('product')
            new_price = request.POST.get('new_price')

            # Check both fields were filled out
            if not product_name or not new_price:
                return render(request, 'store/change_price.html', {
                    'error': 'Please provide both product name and new price.'
                })

            try:
                product = Product.objects.get(name=product_name)

                if not product.store or product.store.owner != request.user:
                    return HttpResponse("Unauthorized")

                product.price = float(new_price)
                product.save()

                return HttpResponseRedirect(reverse('store:product_page'))
            except ValueError:
                # If new price isn't a valid number, show error
                return render(request, 'store/change_price.html', {
                    'error': 'Invalid price format.'
                })
            except ObjectDoesNotExist:
                # If product name does not exist in database, show error
                return render(request, 'store/change_price.html', {
                    'error': 'Product not found.'
                })

        return render(request, 'store/change_price.html')

    # If user does not have permission, show error
    return render(request, 'store/change_price.html', {
        'error': 'You do not have permission to change prices.'
    })


@login_required
def add_item_to_cart(request):
    item = request.POST.get('item')
    quantity = request.POST.get('quantity')

    # If either is missing, redirect to cart page without changing anything
    if not item or not quantity:
        return redirect('store:main_cart_page')

    try:
        # Set quantity to 1 if invalid or less than 1
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    cart = request.session.get('cart', {})

    if item in cart:
        cart[item] += quantity
    else:
        cart[item] = quantity

    request.session['cart'] = cart
    request.session.modified = True  # Mark session as changed

    return redirect(reverse('store:main_cart_page'))


@login_required
def retrieve_products(request):
    products = []
    session = request.session

    if 'cart' in session:
        for name, quantity in session['cart'].items():
            try:
                product = Product.objects.get(name=name)
                products.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                # Skip if product not found
                pass

    return products


@login_required
def show_user_cart(request):
    cart_items = retrieve_products(request)

    total_price = 0

    for item in cart_items:
        subtotal = item['product'].price * item['quantity']
        item['subtotal'] = subtotal
        total_price += subtotal

    return render(request, 'store/main_cart_page.html', {
        'cart': cart_items,
        'total_price': total_price,
    })


@login_required
def list_products(request):
    products = Product.objects.all()
    return render(request, 'store/products_list.html', {
        'products': products,
        'is_vendor': is_vendor(request.user),
    })


@login_required
def product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return redirect('store:products_list')

    reviews = product.reviews.all()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews
    })


@login_required
def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True  # Mark session as changed

    return redirect('store:main_cart_page')


@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return HttpResponse("Cart is empty")

    # Preview cart
    if request.method == 'GET':
        cart_items = []

        for name, qty in cart.items():
            try:
                product = Product.objects.get(name=name)
                cart_items.append({
                    "product": product,
                    "quantity": qty
                })
            except Product.DoesNotExist:
                continue

        total = sum(
            item["product"].price * item["quantity"]
            for item in cart_items
        )

        return render(request, 'store/checkout.html', {
            'cart': cart_items,
            'total_price': total
        })

    cart_items = []
    stock_errors = []

    for name, qty in cart.items():
        # Validate product existence and stock
        try:
            product = Product.objects.get(name=name)
        except Product.DoesNotExist:
            continue
        if qty > product.stock:
            stock_errors.append(
                f"{product.name}: requested {qty}, only {product.stock} in stock."
            )
        cart_items.append({'product': product, 'quantity': qty})

    if stock_errors:
        total = sum(i['product'].price * i['quantity'] for i in cart_items)
        return render(request, 'store/checkout.html', {
            'cart': cart_items,
            'total_price': total,
            'stock_errors': stock_errors,
        })

    items = []
    total = 0

    for item in cart_items:
        product = item['product']
        qty = item['quantity']
        subtotal = product.price * qty
        total += subtotal

        product.stock -= qty
        product.save()

        items.append({
            "name": product.name,
            "qty": qty,
            "price": product.price,
            "subtotal": subtotal
        })

    purchased_products = request.session.get('purchased_products', [])

    for name in cart.keys():
        if name not in purchased_products:
            purchased_products.append(name)

    request.session['purchased_products'] = purchased_products

    message = "ORDER INVOICE\n\n"

    for item in items:
        message += (
            f"{item['name']} x{item['qty']} "
            f"- £{item['subtotal']}\n"
        )

    message += f"\nTOTAL: £{total}"

    send_mail(
        'Your Order Invoice',
        message,
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
    )

    request.session['cart'] = {}
    request.session.modified = True

    return render(request, 'store/checkout_success.html', {
        'total_price': total,
        'items': items
    })


@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        text = request.POST.get('text')

        if not text:
            return redirect('store:product_detail', product_id=product_id)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return redirect('store:products_list')

        purchased_products = request.session.get('purchased_products', [])

        is_verified = product.name in purchased_products

        Review.objects.create(
            product=product,
            user=request.user,
            text=text,
            verified=is_verified
        )

        return redirect('store:product_detail', product_id=product_id)


@login_required
def create_product(request):

    if not is_vendor(request.user):
        return HttpResponse("Only vendors can create products")

    stores = Store.objects.filter(owner=request.user)

    if request.method == 'POST':
        store_id = request.POST.get('store')

        try:
            store = Store.objects.get(id=store_id, owner=request.user)
        except Store.DoesNotExist:
            return HttpResponse("Invalid store selection")

        product = Product.objects.create(
            store=store,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            image=request.FILES.get('image') or None,
        )

        tweet_new_product(product)

        return redirect('store:my_products')

    return render(request, 'store/create_product.html', {'stores': stores})


@login_required
def delete_product(request, product_id):

    if not is_vendor(request.user):
        return HttpResponse("Only vendors can delete products")

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponse("Product not found")

    if not product.store or product.store.owner != request.user:
        return HttpResponse("Unauthorized")

    product.delete()
    return redirect('store:my_products')


@login_required
def edit_product(request, product_id):

    if not is_vendor(request.user):
        return HttpResponse("Only vendors can edit products")

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponse("Product not found")

    if not product.store or product.store.owner != request.user:
        return HttpResponse("Unauthorized")

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()

        return redirect('store:my_products')

    return render(request, 'store/edit_product.html', {'product': product})


@login_required
def my_stores(request):
    stores = Store.objects.filter(owner=request.user)
    return render(request, 'store/my_stores.html', {'stores': stores})


@login_required
def create_store(request):
    if not is_vendor(request.user):
        return HttpResponse("Only vendors can create stores")

    if request.method == 'POST':
        name = request.POST.get('name')

        if not name:
            return render(request, 'store/create_store.html', {
                'error': 'Store name is required'
            })

        description = request.POST.get('description', '')
        logo = request.FILES.get('logo') or None

        store = Store.objects.create(
            name=name,
            owner=request.user,
            description=description,
            logo=logo,
        )

        tweet_new_store(store)

        return redirect('store:my_stores')

    return render(request, 'store/create_store.html')


@login_required
def edit_store(request, store_id):
    if not is_vendor(request.user):
        return HttpResponse("Only vendors can manage stores")

    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return HttpResponse("Store not found")

    if store.owner != request.user:
        return HttpResponse("Unauthorized")

    if request.method == 'POST':
        store.name = request.POST.get('name')
        store.description = request.POST.get('description', '')
        if request.FILES.get('logo'):
            store.logo = request.FILES.get('logo')
        store.save()
        return redirect('store:my_stores')

    return render(request, 'store/edit_store.html', {'store': store})


@login_required
def delete_store(request, store_id):
    if not is_vendor(request.user):
        return HttpResponse("Only vendors can manage stores")

    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return HttpResponse("Store not found")

    if store.owner != request.user:
        return HttpResponse("Unauthorized")

    if request.method == 'POST':
        try:
            store.delete()
            return redirect('store:my_stores')
        except Exception as e:
            return HttpResponse(f"Error deleting store: {e}")

    return HttpResponse("Invalid request method")


@login_required
def my_products(request):

    # Only vendors can access
    if not is_vendor(request.user):
        return HttpResponse("Only vendors can view products")

    # Only show products owned by this user
    products = Product.objects.filter(store__owner=request.user)

    return render(request, 'store/my_products.html', {
        'products': products
    })