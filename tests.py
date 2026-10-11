from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from books.models import Genre, Author, Book, Review, BookInteraction
from recommendations.services.content_based import get_content_based_similar_books, get_content_based_user_recommendations
from recommendations.services.collaborative import get_user_collaborative_recommendations, get_item_collaborative_similar_books
from recommendations.services.hybrid import get_hybrid_recommendations_for_user, get_popular_trending_books
from recommendations.services.association import get_frequently_bought_together
from orders.models import Order, OrderItem


class RecommendationEngineTests(TestCase):
    def setUp(self):
        # Users
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')
        self.user_new = User.objects.create_user(username='usernew', password='password123')

        # Genres
        self.g_scifi = Genre.objects.create(name='Sci-Fi')
        self.g_fantasy = Genre.objects.create(name='Fantasy')

        # Authors
        self.author_1 = Author.objects.create(name='Arthur Clarke')
        self.author_2 = Author.objects.create(name='George Martin')

        # Books
        self.book_sf1 = Book.objects.create(
            title='2001: A Space Odyssey',
            author=self.author_1,
            price=Decimal('20.00'),
            synopsis='Space journey to Jupiter with AI HAL 9000.'
        )
        self.book_sf1.genres.add(self.g_scifi)

        self.book_sf2 = Book.objects.create(
            title='Rendezvous with Rama',
            author=self.author_1,
            price=Decimal('18.00'),
            synopsis='An alien cylindrical starship enters the solar system.'
        )
        self.book_sf2.genres.add(self.g_scifi)

        self.book_fan1 = Book.objects.create(
            title='A Game of Thrones',
            author=self.author_2,
            price=Decimal('25.00'),
            synopsis='Noble families fight for control of the Iron Throne of Westeros.'
        )
        self.book_fan1.genres.add(self.g_fantasy)

        self.book_fan2 = Book.objects.create(
            title='A Clash of Kings',
            author=self.author_2,
            price=Decimal('25.00'),
            synopsis='The war of the five kings rages across Westeros.'
        )
        self.book_fan2.genres.add(self.g_fantasy)

        # User A loves Sci-Fi
        Review.objects.create(book=self.book_sf1, user=self.user_a, rating=5, body='Brilliant space story')
        Review.objects.create(book=self.book_sf2, user=self.user_a, rating=5, body='Wonderful discovery')

        # User B loves Sci-Fi too
        Review.objects.create(book=self.book_sf1, user=self.user_b, rating=5, body='Loved it')

        # Order with multiple books together for Market Basket
        order = Order.objects.create(
            full_name='Test Buyer',
            email='buyer@test.com',
            total_amount=Decimal('43.00'),
            status='Delivered'
        )
        OrderItem.objects.create(order=order, book=self.book_sf1, book_title=self.book_sf1.title, price=Decimal('20.00'), quantity=1)
        OrderItem.objects.create(order=order, book=self.book_sf2, book_title=self.book_sf2.title, price=Decimal('18.00'), quantity=1)

    def test_content_based_similarity(self):
        # 2001: A Space Odyssey should be very similar to Rendezvous with Rama (same author + genre + space theme)
        similar_to_sf1 = get_content_based_similar_books(self.book_sf1, limit=2)
        self.assertTrue(len(similar_to_sf1) > 0)
        self.assertEqual(similar_to_sf1[0]['book'].id, self.book_sf2.id)

    def test_collaborative_filtering_user_similarity(self):
        # User B rated 2001 5★. User A also rated 2001 5★ and Rama 5★.
        # User B should be recommended Rendezvous with Rama via Collaborative Filtering.
        collab_for_b = get_user_collaborative_recommendations(self.user_b, limit=3)
        self.assertTrue(len(collab_for_b) > 0)
        recommended_ids = [item['book'].id for item in collab_for_b]
        self.assertIn(self.book_sf2.id, recommended_ids)

    def test_frequently_bought_together_basket_analysis(self):
        # Book SF1 was ordered with Book SF2 in the same order
        fbt = get_frequently_bought_together(self.book_sf1, limit=2)
        self.assertTrue(len(fbt) > 0)
        self.assertEqual(fbt[0]['book'].id, self.book_sf2.id)

    def test_hybrid_recommendations_and_cold_start(self):
        # Logged in User A gets hybrid recommendations
        hybrid_a = get_hybrid_recommendations_for_user(self.user_a, limit=4)
        self.assertTrue(len(hybrid_a) > 0)

        # Brand new user gets cold start popular recommendations
        cold_start = get_hybrid_recommendations_for_user(self.user_new, limit=4)
        self.assertTrue(len(cold_start) > 0)
