from .models import Cart, Wishlist

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_context(request):
    cart = get_or_create_cart(request)
    wishlist_count = 0
    wishlist_book_ids = set()
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        wishlist_count = wishlist_items.count()
        wishlist_book_ids = set(wishlist_items.values_list('book_id', flat=True))

    return {
        'cart': cart,
        'cart_item_count': cart.total_items,
        'wishlist_count': wishlist_count,
        'wishlist_book_ids': wishlist_book_ids,
    }
