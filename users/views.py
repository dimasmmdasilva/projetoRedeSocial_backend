import logging
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Tweet
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    TweetSerializer, 
    UpdateUserSerializer
)

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        user = None
        if username:
            user = authenticate(username=username, password=password)
        elif email:
            user = CustomUser.objects.filter(email=email).first()
            if user:
                user = authenticate(username=user.username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data
            }, status=status.HTTP_200_OK)

        return Response({"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Logout realizado com sucesso!"}, status=status.HTTP_200_OK)
            except Exception:
                return Response({"error": "Erro ao invalidar o token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)

class UpdateProfileImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        user = request.user
        if 'profile_image' not in request.FILES:
            return Response({"error": "Imagem de perfil não fornecida"}, status=status.HTTP_400_BAD_REQUEST)

        user.profile_image = request.FILES["profile_image"]
        user.save()
        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)

class UpdateBioView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        bio = request.data.get("bio")

        if not bio:
            return Response({"error": "Biografia não fornecida"}, status=status.HTTP_400_BAD_REQUEST)

        user.bio = bio
        user.save()
        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)

class TweetViewSet(ModelViewSet):
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tweet.objects.prefetch_related("likes").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class FollowingTweetsView(ListAPIView):
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following = user.following.all()
        if not following.exists():
            return Tweet.objects.none()

        return Tweet.objects.filter(author__in=following).select_related("author").order_by('-created_at')

class LikeTweetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tweet_id):
        tweet = get_object_or_404(Tweet, id=tweet_id)

        if request.user in tweet.likes.all():
            return Response({"error": "Você já curtiu este tweet!"}, status=status.HTTP_400_BAD_REQUEST)

        tweet.likes.add(request.user)
        return Response({"message": "Tweet curtido com sucesso!"}, status=status.HTTP_200_OK)

class UnlikeTweetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tweet_id):
        tweet = get_object_or_404(Tweet, id=tweet_id)

        if request.user not in tweet.likes.all():
            return Response({"error": "Você ainda não curtiu este tweet!"}, status=status.HTTP_400_BAD_REQUEST)

        tweet.likes.remove(request.user)
        return Response({"message": "Curtida removida com sucesso!"}, status=status.HTTP_200_OK)
