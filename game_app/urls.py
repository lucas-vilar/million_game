from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('criarapelido/', views.JogadorCreateView.as_view(), name='criarapelido'),
    path('ranking/', views.ranking_jogador, name='ranking'),
    path('jogo/', views.jogo, name='jogo')
]