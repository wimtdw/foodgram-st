from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django.urls import reverse
from django.shortcuts import redirect
from recipes.models import Follow, Ingredient, Recipe, RecipeIngredient
from django.contrib.auth import get_user_model
from .permissions import IsAuthorOrReadOnly
from .utils import encode_id_to_base62, decode_base62_to_id
from .serializers import (
    CustomUserWithRecipesSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    UserAvatarSerializer,
)


User = get_user_model()


class IngredientSearchFilter(SearchFilter):
    search_param = "name"


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для работы с ингредиентами.
    Поиск по названию: /ingredients/?name=капуста
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для работы с пользователями.
    """

    def get_permissions(self):
        if self.action == "retrieve" or self.action == "list":
            return [AllowAny()]
        if self.action == "subscribe":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def subscribe(self, request, *args, **kwargs):
        user = request.user
        author = self.get_object()
        if request.method == "POST":
            serializer = FollowSerializer(
                data={
                    'user': user.id,
                    'following': author.id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = CustomUserWithRecipesSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                follow = user.following.get(following=author)
            except Follow.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def subscriptions(self, request):
        user = request.user
        following = User.objects.filter(followers__user=user)
        page = self.paginate_queryset(following)
        if page:
            serializer = CustomUserWithRecipesSerializer(
                page, context={"request": request}, many=True
            )
            return self.get_paginated_response(serializer.data)
        serializer = CustomUserWithRecipesSerializer(
            following, context={"request": request}, many=True
        )
        return Response(serializer.data)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.NumberFilter(method="filter_by_favorite")
    is_in_shopping_cart = filters.NumberFilter(method="filter_by_cart")

    class Meta:
        model = Recipe
        fields = ("author",)

    def filter_by_favorite(self, queryset, name, value):
        return self._filter_by_relation(queryset, value, "users_favorited")

    def filter_by_cart(self, queryset, name, value):
        return self._filter_by_relation(queryset, value, "who_added_to_cart")

    def _filter_by_relation(self, queryset, value, relation_name):
        user = self.request.user
        if not user.is_authenticated or value != 1:
            return queryset
        return queryset.filter(**{f"{relation_name}__id": user.id})


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    Поддерживает все стандартные операции CRUD.
    """

    queryset = Recipe.objects.prefetch_related(
        "ingredient_amounts__ingredient").all()
    serializer_class = RecipeSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_user_lists(self, request, relation_field, *args, **kwargs):
        user = request.user
        recipe = self.get_object()
        manager = getattr(user, relation_field)
        if request.method == "POST":
            if manager.filter(id=recipe.id).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            manager.add(recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            if not manager.filter(id=recipe.id).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            manager.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, *args, **kwargs):
        return self._handle_user_lists(request,
                                       "favorite_recipes", *args, **kwargs)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, *args, **kwargs):
        return self._handle_user_lists(request,
                                       "shopping_cart", *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_short_link(self, request, pk=None):
        """
        Генерирует короткую ссылку для рецепта.
        """
        recipe = self.get_object()
        short_code = encode_id_to_base62(recipe.id)
        relative_url = reverse("short-link-redirect",
                               kwargs={"short_code": short_code})
        full_short_url = request.build_absolute_uri(relative_url)

        return Response({"short-link": full_short_url})

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Формирует текстовый файл со списком покупок."""
        user = request.user
        shopping_cart = user.shopping_cart.all()
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=shopping_cart)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )
        content_lines = []
        for i, ingredient in enumerate(ingredients):
            line = (
                f'{i+1}. '
                f'{ingredient["ingredient__name"].title()} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' — {ingredient["total_amount"]}'
            )
            content_lines.append(line)
        text_content = "\n".join(content_lines)
        if text_content:
            text_content += "\n"
        filename = "shopping_cart.txt"
        response = HttpResponse(text_content, content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


def redirect_short_link(request, short_code):
    recipe_id = decode_base62_to_id(short_code)
    # api redirection
    # detail_url = reverse('recipe-detail', kwargs={'pk': recipe_id})
    # return redirect(detail_url)
    return redirect(f"/recipes/{recipe_id}")
