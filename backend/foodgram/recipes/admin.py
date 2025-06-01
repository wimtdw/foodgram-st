from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Follow


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    fields = ('ingredient', 'amount', 'get_measurement_unit')
    readonly_fields = ('get_measurement_unit',)

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit if obj.ingredient else ''

    get_measurement_unit.short_description = 'Единица измерения'


class RecipesAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
    )
    fields = (
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
        'pub_date',
        'favorite_count',
    )
    readonly_fields = ('pub_date', 'favorite_count')

    def favorite_count(self, obj):
        return obj.users_favorited.count()

    favorite_count.short_description = 'В избранном'

    inlines = [RecipeIngredientInline]


class IngredientsAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(Recipe, RecipesAdmin)
admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(Follow)
