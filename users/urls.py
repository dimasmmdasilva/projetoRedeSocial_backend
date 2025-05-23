from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView,
    TweetViewSet, FollowingTweetsView, LikeTweetView, UnlikeTweetView,
    UpdateProfileImageView, UpdateBioView, UserDetailView, DeleteTweetView,
    UserListView, FollowToggleView
)

router = DefaultRouter()
router.register(r"tweets", TweetViewSet, basename="tweets")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),

    path("user/detail/", UserDetailView.as_view(), name="user-detail"),
    path("users/list/", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/follow/", FollowToggleView.as_view(), name="follow-toggle"),

    path("tweets/following/", FollowingTweetsView.as_view(), name="following-tweets"),
    path("tweets/<int:tweet_id>/like/", LikeTweetView.as_view(), name="like-tweet"),
    path("tweets/<int:tweet_id>/unlike/", UnlikeTweetView.as_view(), name="unlike-tweet"),
    path("tweets/<int:tweet_id>/delete/", DeleteTweetView.as_view(), name="delete-tweet"),

    path("user/update-profile-image/", UpdateProfileImageView.as_view(), name="update-profile-image"),
    path("user/update-bio/", UpdateBioView.as_view(), name="update-bio"),
]

urlpatterns += router.urls
