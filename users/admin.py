from django.contrib import admin
from .models import CustomUser, Tweet

# Personalizando a exibição do CustomUser no Django Admin
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_active")
    ordering = ("id",)

# Personalizando a exibição do Tweet no Django Admin
@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "content", "created_at", "likes_count")
    search_fields = ("content", "author__username")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = "Curtidas"

# Exibir no console que os modelos foram registrados com sucesso
print("✅ Modelos registrados no Django Admin: CustomUser e Tweet.")
