import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tweet

# Configuração do Logger
logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "confirm_password"]

    def validate(self, data):
        """ Valida os dados antes do registro do usuário. """
        logger.info(f"Tentativa de registro com dados: {data}")

        if data["password"] != data["confirm_password"]:
            logger.warning("As senhas não coincidem!")
            raise serializers.ValidationError({"password": "As senhas não coincidem!"})

        if User.objects.filter(username=data["username"]).exists():
            logger.warning(f"Nome de usuário '{data['username']}' já está em uso!")
            raise serializers.ValidationError({"username": "Nome de usuário já está em uso!"})

        if User.objects.filter(email=data["email"]).exists():
            logger.warning(f"Email '{data['email']}' já cadastrado!")
            raise serializers.ValidationError({"email": "Email já cadastrado!"})

        logger.info(f"Usuário '{data['username']}' validado com sucesso!")
        return data

    def create(self, validated_data):
        """ Cria um novo usuário sem os campos de confirmação. """
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        logger.info(f"Novo usuário criado: {user.username} (ID: {user.id})")
        return user


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile_image", "bio", "followers_count", "is_following"]

    def get_followers_count(self, obj):
        """ Retorna a contagem de seguidores ou 0 se o usuário não tiver seguidores. """
        return obj.followers.count() if obj.followers.exists() else 0

    def get_is_following(self, obj):
        """ Verifica se o usuário autenticado segue o usuário alvo. Evita erro caso não haja um request. """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        following = obj.followers.filter(id=request.user.id).exists()
        logger.debug(f"Usuário {request.user.username} está seguindo {obj.username}: {following}")
        return following


class UpdateUserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)
    bio = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["profile_image", "bio"]

    def validate(self, data):
        """ Valida se pelo menos um campo foi enviado para atualização. """
        logger.info(f"Tentativa de atualização de perfil: {data}")

        if "profile_image" not in data and "bio" not in data:
            logger.warning("Tentativa de atualização sem fornecer dados válidos!")
            raise serializers.ValidationError("Informe pelo menos um campo para atualizar (imagem de perfil ou biografia).")

        logger.info("Dados validados para atualização de perfil.")
        return data


class TweetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = ["id", "content", "created_at", "author", "likes_count", "is_liked"]

    def get_likes_count(self, obj):
        """ Retorna a quantidade de curtidas ou 0 se não houver curtidas. """
        return obj.likes.count() if obj.likes.exists() else 0

    def get_is_liked(self, obj):
        """ Verifica se o usuário autenticado curtiu o tweet. Evita erro caso não haja um request. """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        liked = obj.likes.filter(id=request.user.id).exists()
        logger.debug(f"Usuário {request.user.username} curtiu o tweet {obj.id}: {liked}")
        return liked
