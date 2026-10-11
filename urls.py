from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('for-you/', views.for_you_hub, name='for_you'),
    path('explain/<int:book_id>/', views.explain_recommendation, name='explain'),
]
