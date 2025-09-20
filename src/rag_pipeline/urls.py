from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.QueryView.as_view(), name='query'),
    path('health/', views.HealthView.as_view(), name='health'),
    path('stats/', views.StatsView.as_view(), name='stats'),
]
