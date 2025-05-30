from rest_framework.response import Response
from rest_framework import status, viewsets, exceptions
from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.shortcuts import redirect
from recipes.models import Ingredient, Recipe
from .serializers import IngredientSerializer, RecipeSerializer, UserAvatarSerializer
import string


BASE62_ALPHABET = string.digits + string.ascii_letters
BASE62_LENGTH = len(BASE62_ALPHABET)

def encode_id_to_base62(pk: int) -> str:
    """Преобразует ID в строку base62"""
    if pk == 0:
        return BASE62_ALPHABET[0]
    
    result = []
    num = pk
    while num:
        num, rem = divmod(num, BASE62_LENGTH)
        result.append(BASE62_ALPHABET[rem])
    return ''.join(result[::-1])

def decode_base62_to_id(short_code: str) -> int:
    """Преобразует строку base62 обратно в ID"""
    num = 0
    for char in short_code:
        num = num * BASE62_LENGTH + BASE62_ALPHABET.index(char)
    return num

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для работы с ингредиентами.
    Поиск по названию: /ingredients/?search=капуста
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            return queryset.filter(name__icontains=search_query)
        return queryset
    
class CustomUserViewSet(UserViewSet):
    
    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        

class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    Поддерживает все стандартные операции CRUD.
    """
    queryset = Recipe.objects.prefetch_related(
        'ingredient_amounts__ingredient'
    ).all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """
        Генерирует короткую ссылку для рецепта.
        """
        recipe = self.get_object()
        short_code = encode_id_to_base62(recipe.id)
        relative_url = reverse('short-link-redirect', kwargs={'short_code': short_code})
        full_short_url = request.build_absolute_uri(relative_url)

        return Response({
            "short-link": full_short_url
        })

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Изменение чужого контента запрещено!')
        serializer.save(author=self.request.user)

    def perform_destroy(self, serializer):
        instance = self.get_object()
        if instance.author != self.request.user:
            raise exceptions.PermissionDenied(
                'Удаление чужого контента запрещено!')
        instance.delete()


def redirect_short_link(request, short_code):
    recipe_id = decode_base62_to_id(short_code)
    detail_url = reverse('recipe-detail', kwargs={'pk': recipe_id})
    return redirect(detail_url)