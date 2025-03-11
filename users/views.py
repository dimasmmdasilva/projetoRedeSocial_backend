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

# Configuração do Logger
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """ Endpoint para registrar um novo usuário. """
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Tentativa de registro de usuário: {request.data}")
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Usuário registrado com sucesso: {user.username}")
            return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_201_CREATED)

        logger.warning(f"Erro no registro de usuário: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """ Endpoint para autenticação de usuários via username ou e-mail. """
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Tentativa de login com dados: {request.data}")
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
            logger.info(f"Login bem-sucedido para o usuário: {user.username}")
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data
            }, status=status.HTTP_200_OK)

        logger.warning("Falha no login: Credenciais inválidas")
        return Response({"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """ Endpoint para logout e blacklist de token. """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        logger.info(f"Tentativa de logout do usuário {request.user.username}")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Logout realizado com sucesso para {request.user.username}")
                return Response({"message": "Logout realizado com sucesso!"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Erro ao invalidar token: {e}")
                return Response({"error": "Erro ao invalidar o token"}, status=status.HTTP_400_BAD_REQUEST)

        logger.warning("Token inválido ou não fornecido para logout")
        return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileImageView(APIView):
    """ Endpoint para atualizar a imagem de perfil do usuário. """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        user = request.user
        profile_image = request.data.get("profile_image")

        if not profile_image:
            logger.warning(f"Usuário {user.username} tentou atualizar imagem de perfil sem fornecer um arquivo.")
            return Response({"error": "Imagem de perfil não fornecida"}, status=status.HTTP_400_BAD_REQUEST)

        user.profile_image = profile_image
        user.save()
        logger.info(f"Imagem de perfil atualizada com sucesso para {user.username}")
        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)


class UpdateBioView(APIView):
    """ Endpoint para atualizar a biografia do usuário. """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        bio = request.data.get("bio")

        if not bio:
            logger.warning(f"Usuário {user.username} tentou atualizar bio sem fornecer dados.")
            return Response({"error": "Biografia não fornecida"}, status=status.HTTP_400_BAD_REQUEST)

        user.bio = bio
        user.save()
        logger.info(f"Biografia atualizada com sucesso para {user.username}")
        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)


class TweetViewSet(ModelViewSet):
    """ CRUD para tweets, com filtragem por data de criação e curtidas. """
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retorna os tweets ordenados por data de criação. """
        return Tweet.objects.prefetch_related("likes").order_by("-created_at")

    def perform_create(self, serializer):
        tweet = serializer.save(author=self.request.user)
        logger.info(f"Novo tweet criado por {self.request.user.username}: {tweet.content[:50]}")


class FollowingTweetsView(ListAPIView):
    """ Lista de tweets apenas de usuários seguidos. """
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Retorna tweets de usuários seguidos. """
        user = self.request.user
        following = user.following.all()
        if not following.exists():
            logger.info(f"{user.username} não segue ninguém, retornando lista vazia de tweets.")
            return Tweet.objects.none()

        tweets = Tweet.objects.filter(author__in=following).select_related("author").order_by('-created_at')
        logger.info(f"{user.username} carregou {tweets.count()} tweets de usuários seguidos.")
        return tweets


class LikeTweetView(APIView):
    """ Endpoint para curtir um tweet. """
    permission_classes = [IsAuthenticated]

    def post(self, request, tweet_id):
        tweet = get_object_or_404(Tweet, id=tweet_id)

        if request.user in tweet.likes.all():
            logger.warning(f"Usuário {request.user.username} tentou curtir um tweet já curtido: {tweet_id}")
            return Response({"error": "Você já curtiu este tweet!"}, status=status.HTTP_400_BAD_REQUEST)

        tweet.likes.add(request.user)
        logger.info(f"Usuário {request.user.username} curtiu o tweet {tweet_id}")
        return Response({"message": "Tweet curtido com sucesso!"}, status=status.HTTP_200_OK)


class UnlikeTweetView(APIView):
    """ Endpoint para remover curtida de um tweet. """
    permission_classes = [IsAuthenticated]

    def post(self, request, tweet_id):
        tweet = get_object_or_404(Tweet, id=tweet_id)

        if request.user not in tweet.likes.all():
            logger.warning(f"Usuário {request.user.username} tentou remover curtida de um tweet não curtido: {tweet_id}")
            return Response({"error": "Você ainda não curtiu este tweet!"}, status=status.HTTP_400_BAD_REQUEST)

        tweet.likes.remove(request.user)
        logger.info(f"Usuário {request.user.username} removeu a curtida do tweet {tweet_id}")
        return Response({"message": "Curtida removida com sucesso!"}, status=status.HTTP_200_OK)
