from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView,
    TweetViewSet, FollowingTweetsView, LikeTweetView, UnlikeTweetView,
    UpdateProfileImageView, UpdateBioView, UserDetailView
)

# Criando o roteador de URLs para ViewSets
router = DefaultRouter()
router.register(r"tweets", TweetViewSet, basename="tweets")

urlpatterns = [
    # Autenticação
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),

    # Dados do usuário autenticado
    path("user/detail/", UserDetailView.as_view(), name="user-detail"),

    # Tweets e interações
    path("tweets/following/", FollowingTweetsView.as_view(), name="following-tweets"),
    path("tweets/<int:tweet_id>/like/", LikeTweetView.as_view(), name="like-tweet"),
    path("tweets/<int:tweet_id>/unlike/", UnlikeTweetView.as_view(), name="unlike-tweet"),

    # Perfil do usuário
    path("user/update-profile-image/", UpdateProfileImageView.as_view(), name="update-profile-image"),
    path("user/update-bio/", UpdateBioView.as_view(), name="update-bio"),
]

# Adicionando as rotas do DefaultRouter sem duplicar o "api/"
urlpatterns += router.urls
