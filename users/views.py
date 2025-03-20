import logging
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView, DestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Tweet
from .serializers import RegisterSerializer, UserSerializer, TweetSerializer

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

        user = authenticate(username=username, password=password) if username else None
        if not user and email:
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

class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        data = UserSerializer(user, context={"request": request}).data
        data["followers"] = [{"id": u.id, "username": u.username} for u in user.followers.all()]
        data["following"] = [{"id": u.id, "username": u.username} for u in user.following.all()]
        data["followers_count"] = user.followers.count()
        data["following_count"] = user.following.count()
        return Response(data, status=status.HTTP_200_OK)

class UserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.exclude(id=self.request.user.id).order_by("username")

class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user_to_follow = get_object_or_404(CustomUser, id=user_id)

        if user_to_follow == request.user:
            return Response({"error": "Você não pode seguir a si mesmo."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.following.filter(id=user_to_follow.id).exists():
            request.user.following.remove(user_to_follow)
            return Response({"message": f"Você deixou de seguir {user_to_follow.username}."}, status=status.HTTP_200_OK)
        else:
            request.user.following.add(user_to_follow)
            return Response({"message": f"Agora você está seguindo {user_to_follow.username}."}, status=status.HTTP_200_OK)

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

class DeleteTweetView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, tweet_id):
        tweet = get_object_or_404(Tweet, id=tweet_id)
        if tweet.author != request.user:
            return Response({"error": "Você não tem permissão para excluir este tweet."}, status=status.HTTP_403_FORBIDDEN)

        tweet.delete()
        logger.info(f"Tweet {tweet_id} excluído por {request.user.username}")
        return Response({"message": "Tweet excluído com sucesso!"}, status=status.HTTP_200_OK)

class FollowingTweetsView(ListAPIView):
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following = user.following.all()
        return Tweet.objects.filter(author__in=following | CustomUser.objects.filter(id=user.id)).select_related("author").order_by('-created_at')

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
