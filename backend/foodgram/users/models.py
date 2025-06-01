from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        blank=False,
    )

    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="users/", blank=True, null=True)
    favorite_recipes = models.ManyToManyField(
        "recipes.Recipe", related_name="users_favorited", blank=True
    )
    shopping_cart = models.ManyToManyField(
        "recipes.Recipe", related_name="who_added_to_cart", blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
