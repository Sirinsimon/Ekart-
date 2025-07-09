from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ContactForm, RegisterForm
from .models import Product, Cart, CartItem, Order
from django.db.models import Q

def home(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login to view products.")
        return redirect('login')
    query = request.GET.get('q')
    products = Product.objects.all()
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, 'store/home.html', {'products': products})

def about(request):
    return render(request, 'store/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Thanks for contacting us!")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'store/dashboard.html')

def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            messages.success(request, 'Login successful')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'store/login.html')
def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"Added {product.title} to cart.")
    return redirect('view_cart')
@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = list(cart.items.all())
    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')
    order = Order.objects.create(user=request.user)
    order.items.set(items)
    order.save()
    cart.items.all().delete()
    messages.success(request, "Order placed successfully!")
    return redirect('dashboard')
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    bullet_specs = product.specs.split('\n') if product.specs else []
    return render(request, 'store/product_detail.html', {'product': product, 'bullet_specs': bullet_specs})



@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    return render(request, 'store/orders.html', {'orders': orders})
def increase_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.quantity += 1
    item.save()
    return redirect('view_cart')

@login_required
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('view_cart')
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('view_cart')
@login_required
def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        new_qty = int(request.POST.get('quantity', 1))
        item.quantity = new_qty if new_qty > 0 else 1
        item.save()
        messages.success(request, "Cart updated successfully.")
    return redirect('view_cart')
@login_required
def purchase_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=1)
    order = Order.objects.create(user=request.user)
    order.items.add(item)
    order.save()
    messages.success(request, "Product purchased successfully!")
    return redirect('dashboard')

