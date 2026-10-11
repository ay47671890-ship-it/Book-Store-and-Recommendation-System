from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from books.models import Book, Genre, Review
from orders.models import OrderItem
from .services.engine import RecommendationEngine
from .services.content_based import get_content_based_user_recommendations, get_content_based_similar_books
from .services.collaborative import get_user_collaborative_recommendations, get_item_collaborative_similar_books
from .services.hybrid import get_popular_trending_books, get_cold_start_recommendations


def for_you_hub(request):
    """
    Dedicated AI Recommendation Center showcasing all 4 recommendation dimensions
    with transparency badges and personalized insights.
    """
    user = request.user if request.user.is_authenticated else None

    # 1. Main Hybrid Feed
    hybrid_recs = RecommendationEngine.get_for_user(user, limit=8)

    # 2. Collaborative Feed (Users with similar taste)
    collab_recs = []
    if user:
        collab_recs = get_user_collaborative_recommendations(user, limit=6)

    # 3. Content-Based Feed (Because you read/liked X)
    content_recs = []
    reference_book = None
    if user:
        content_recs = get_content_based_user_recommendations(user, limit=6)
        # Find user's highest rated book for contextual display
        top_review = Review.objects.filter(user=user, rating__gte=4).select_related('book').order_by('-rating', '-created_at').first()
        if top_review:
            reference_book = top_review.book
        else:
            first_purchased = OrderItem.objects.filter(order__user=user).select_related('book').first()
            if first_purchased:
                reference_book = first_purchased.book

    # 4. Trending & Best Rated
    trending_recs = get_popular_trending_books(limit=8)

    # 5. User's Favorite Genres (if configured)
    genre_spotlights = []
    if user and hasattr(user, 'profile') and user.profile.favorite_genres.exists():
        for g in user.profile.favorite_genres.all()[:3]:
            genre_recs = RecommendationEngine.get_genre_highlights(g, limit=4)
            if genre_recs:
                genre_spotlights.append({
                    'genre': g,
                    'books': genre_recs
                })

    context = {
        'hybrid_recs': hybrid_recs,
        'collab_recs': collab_recs,
        'content_recs': content_recs,
        'reference_book': reference_book,
        'trending_recs': trending_recs,
        'genre_spotlights': genre_spotlights,
    }
    return render(request, 'recommendations/for_you.html', context)


def explain_recommendation(request, book_id):
    """
    Explainability endpoint: returns detailed metrics and logic for why a specific book is recommended.
    """
    book = get_object_or_404(Book.objects.prefetch_related('genres', 'author'), id=book_id)
    user = request.user if request.user.is_authenticated else None

    # Compute explanations
    reasons = []
    
    # Check genre match with user
    if user and hasattr(user, 'profile'):
        user_genres = set(user.profile.favorite_genres.values_list('name', flat=True))
        book_genres = set(book.genres.values_list('name', flat=True))
        matched = user_genres.intersection(book_genres)
        if matched:
            reasons.append({
                'title': 'Genre Affinity',
                'description': f"Direct match with your stated interest in {', '.join(matched)}."
            })

    # Check content similarity to previously reviewed books
    if user:
        user_reviews = Review.objects.filter(user=user, rating__gte=4).select_related('book')
        for r in user_reviews:
            if r.book.author_id == book.author_id:
                reasons.append({
                    'title': 'Author Match',
                    'description': f"Written by {book.author.name}, whom you rated highly in '{r.book.title}'."
                })
                break

    # General popularity / quality signals
    if book.is_bestseller:
        reasons.append({
            'title': 'Bestseller Status',
            'description': "Ranked among the top bestselling titles in the store."
        })
    
    if book.average_rating >= 4.5:
        reasons.append({
            'title': 'Critically Acclaimed',
            'description': f"Holds an outstanding {book.average_rating}★ rating based on reader reviews."
        })

    if not reasons:
        reasons.append({
            'title': 'Curated Selection',
            'description': f"Recommended based on popular demand and high engagement in the {book.genres.first().name if book.genres.exists() else 'catalog'} category."
        })

    return JsonResponse({
        'book_title': book.title,
        'author': book.author.name,
        'genres': [g.name for g in book.genres.all()],
        'rating': book.average_rating,
        'reasons': reasons,
    })
