import logging
from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True,
        default="../media/profile_images/default.png"
    )
    bio = models.TextField(blank=True, null=True, max_length=100)
    followers = models.ManyToManyField("self", symmetrical=False, related_name="following", blank=True)

    def __str__(self):
        return self.username

    def follow(self, user):
        if user != self and not self.is_following(user):
            self.following.add(user)
            logger.info(f"{self.username} começou a seguir {user.username}")

    def unfollow(self, user):
        if user != self and self.is_following(user):
            self.following.remove(user)
            logger.info(f"{self.username} deixou de seguir {user.username}")

    def is_following(self, user):
        if not isinstance(user, CustomUser):
            logger.error(f"Tentativa de verificar seguimento de um objeto inválido: {user}")
            return False
        status = self.following.filter(id=user.id).exists()
        logger.debug(f"Verificação de seguimento: {self.username} -> {user.username}: {status}")
        return status

    def get_followers_count(self):
        return self.followers.count()

    def get_tweets_from_following(self):
        following = self.following.all()
        if not following.exists():
            logger.info(f"{self.username} não segue ninguém. Nenhum tweet carregado.")
            return Tweet.objects.none()
        
        tweets = Tweet.objects.filter(author__in=following).select_related("author").order_by('-created_at')
        logger.info(f"{self.username} carregou {tweets.count()} tweets de usuários que segue.")
        return tweets

class Tweet(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tweets")
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(CustomUser, related_name="liked_tweets", blank=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

    def like_tweet(self, user):
        if isinstance(user, CustomUser) and not self.is_liked_by(user):
            self.likes.add(user)
            logger.info(f"{user.username} curtiu o tweet {self.id} de {self.author.username}")

    def unlike_tweet(self, user):
        if isinstance(user, CustomUser) and self.is_liked_by(user):
            self.likes.remove(user)
            logger.info(f"{user.username} removeu a curtida do tweet {self.id} de {self.author.username}")

    def is_liked_by(self, user):
        if not isinstance(user, CustomUser):
            logger.error(f"Tentativa de verificar curtida de um objeto inválido: {user}")
            return False
        status = self.likes.filter(id=user.id).exists()
        logger.debug(f"Verificação de curtida: {user.username} -> Tweet {self.id}: {status}")
        return status

    def get_likes_count(self):
        return self.likes.count()
