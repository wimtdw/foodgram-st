from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewSet
from django.urls import include, path
from .views import CustomUserViewSet


router = DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
