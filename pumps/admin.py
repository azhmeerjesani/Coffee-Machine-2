from django.contrib import admin

from .models import Pump, Recipe, RecipeIngredient

admin.site.register(Pump)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
