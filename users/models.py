import logging
from django.contrib.auth.models import AbstractUser
from django.db import models

# Configuração do Logger
logger = logging.getLogger(__name__)

class CustomUser(AbstractUser):
    """ Modelo de usuário personalizado, incluindo imagem de perfil, bio e sistema de seguidores. """
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True,
        default="profile_images/default.png"
    )
    bio = models.TextField(blank=True, null=True, max_length=300)
    followers = models.ManyToManyField("self", symmetrical=False, related_name="following", blank=True)

    def __str__(self):
        return self.username

    def follow(self, user):
        """ Permite que o usuário siga outro usuário, evitando duplicações. """
        if user != self and not self.is_following(user):
            self.following.add(user)
            logger.info(f"{self.username} começou a seguir {user.username}")

    def unfollow(self, user):
        """ Permite que o usuário pare de seguir outro usuário, evitando erros. """
        if user != self and self.is_following(user):
            self.following.remove(user)
            logger.info(f"{self.username} deixou de seguir {user.username}")

    def is_following(self, user):
        """ Verifica se o usuário está seguindo outro usuário. """
        if not isinstance(user, CustomUser):
            logger.error(f"Tentativa de verificar seguimento de um objeto inválido: {user}")
            return False
        status = self.following.filter(id=user.id).exists()
        logger.debug(f"Verificação de seguimento: {self.username} -> {user.username}: {status}")
        return status

    def get_followers_count(self):
        """ Retorna a quantidade de seguidores do usuário. """
        return self.followers.count()

    def get_tweets_from_following(self):
        """ Retorna os tweets dos usuários seguidos ou uma lista vazia se não seguir ninguém. """
        following = self.following.all()
        if not following.exists():
            logger.info(f"{self.username} não segue ninguém. Nenhum tweet carregado.")
            return Tweet.objects.none()
        
        tweets = Tweet.objects.filter(author__in=following).select_related("author").order_by('-created_at')
        logger.info(f"{self.username} carregou {tweets.count()} tweets de usuários que segue.")
        return tweets


class Tweet(models.Model):
    """ Modelo para armazenar tweets, incluindo autor, conteúdo, curtidas e data de criação. """
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tweets")
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(CustomUser, related_name="liked_tweets", blank=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

    def like_tweet(self, user):
        """ Permite que o usuário curta um tweet, evitando ações repetidas. """
        if isinstance(user, CustomUser) and not self.is_liked_by(user):
            self.likes.add(user)
            logger.info(f"{user.username} curtiu o tweet {self.id} de {self.author.username}")

    def unlike_tweet(self, user):
        """ Permite que o usuário remova sua curtida de um tweet, evitando erros. """
        if isinstance(user, CustomUser) and self.is_liked_by(user):
            self.likes.remove(user)
            logger.info(f"{user.username} removeu a curtida do tweet {self.id} de {self.author.username}")

    def is_liked_by(self, user):
        """ Verifica se um usuário já curtiu o tweet. """
        if not isinstance(user, CustomUser):
            logger.error(f"Tentativa de verificar curtida de um objeto inválido: {user}")
            return False
        status = self.likes.filter(id=user.id).exists()
        logger.debug(f"Verificação de curtida: {user.username} -> Tweet {self.id}: {status}")
        return status

    def get_likes_count(self):
        """ Retorna o número total de curtidas no tweet. """
        return self.likes.count()
