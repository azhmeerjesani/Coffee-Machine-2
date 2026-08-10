from django.urls import path

from . import views

app_name = "pumps"

urlpatterns = [
    path("", views.home, name="home"),
    path("recipes/new/", views.recipe_form, name="recipe_create"),
    path("recipes/<int:pk>/edit/", views.recipe_form, name="recipe_edit"),
    path("recipes/<int:pk>/delete/", views.recipe_delete, name="recipe_delete"),
    path("recipes/<int:pk>/brew/", views.recipe_brew, name="recipe_brew"),
    path("pumps/", views.pump_config, name="pump_config"),
    path("pumps/<int:pk>/test/", views.pump_test, name="pump_test"),
]
