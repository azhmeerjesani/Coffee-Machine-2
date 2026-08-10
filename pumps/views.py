from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .gpio_backend import run_pump, run_pumps_concurrently
from .models import Pump, Recipe, RecipeIngredient

MAX_TEST_SECONDS = 15


def home(request):
    recipes = Recipe.objects.prefetch_related("ingredients__pump")
    return render(request, "pumps/home.html", {"recipes": recipes})


def pump_config(request):
    pumps = Pump.objects.all()
    if request.method == "POST":
        bad_rates = []
        for pump in pumps:
            pump.ingredient_name = request.POST.get(f"ingredient_{pump.id}", "").strip()
            try:
                pump.ml_per_second = max(float(request.POST.get(f"rate_{pump.id}")), 0.01)
            except (TypeError, ValueError):
                bad_rates.append(str(pump))
            pump.save()
        if bad_rates:
            messages.error(request, f"Ignored invalid flow rate for: {', '.join(bad_rates)}.")
        messages.success(request, "Pump configuration saved.")
        return redirect("pumps:pump_config")
    return render(request, "pumps/pump_config.html", {"pumps": pumps})


def pump_test(request, pk):
    pump = get_object_or_404(Pump, pk=pk)
    if request.method == "POST":
        try:
            seconds = float(request.POST.get("seconds", 3))
        except ValueError:
            seconds = 3
        seconds = max(0.5, min(seconds, MAX_TEST_SECONDS))
        try:
            run_pump(pump.gpio_pin, seconds)
        except Exception as exc:
            messages.error(request, f"Couldn't run {pump}: {exc}")
        else:
            messages.success(request, f"Ran {pump} for {seconds:g}s.")
    return redirect("pumps:pump_config")


def recipe_form(request, pk=None):
    recipe = get_object_or_404(Recipe, pk=pk) if pk else None
    pumps = Pump.objects.all()
    existing = {}
    if recipe:
        existing = {ri.pump_id: ri for ri in recipe.ingredients.all()}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        notes = request.POST.get("notes", "").strip()
        if not name:
            messages.error(request, "Recipe needs a name.")
        else:
            if recipe is None:
                recipe = Recipe(name=name)
            else:
                recipe.name = name
            recipe.notes = notes
            recipe.save()
            recipe.ingredients.all().delete()
            skipped = []
            for pump in pumps:
                raw = request.POST.get(f"amount_{pump.id}", "").strip()
                if not raw:
                    continue
                try:
                    amount = float(raw)
                except ValueError:
                    skipped.append(str(pump))
                    continue
                if amount <= 0:
                    continue
                try:
                    step = max(int(request.POST.get(f"step_{pump.id}") or 1), 1)
                except ValueError:
                    step = 1
                RecipeIngredient.objects.create(recipe=recipe, pump=pump, amount_ml=amount, step=step)
            if skipped:
                messages.error(request, f"Ignored invalid amount for: {', '.join(skipped)}.")
            messages.success(request, f"Saved recipe '{recipe.name}'.")
            return redirect("pumps:home")

    pump_rows = [
        (pump, existing[pump.id].amount_ml if pump.id in existing else "", existing[pump.id].step if pump.id in existing else 1)
        for pump in pumps
    ]
    return render(
        request,
        "pumps/recipe_form.html",
        {"recipe": recipe, "pump_rows": pump_rows},
    )


def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.delete()
        messages.success(request, f"Deleted recipe '{recipe.name}'.")
    return redirect("pumps:home")


def recipe_brew(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        steps = {}
        for ri in recipe.ingredients.select_related("pump"):
            steps.setdefault(ri.step, []).append((ri.pump.gpio_pin, ri.pump.seconds_for(ri.amount_ml)))
        if not steps:
            messages.error(request, f"'{recipe.name}' has no ingredients configured -- nothing to brew.")
        else:
            try:
                # steps run in order; pumps within a step run in parallel
                for step_number in sorted(steps):
                    run_pumps_concurrently(steps[step_number])
            except Exception as exc:
                messages.error(request, f"Brewing '{recipe.name}' failed partway through: {exc}")
            else:
                messages.success(request, f"Brewed '{recipe.name}'.")
    return redirect("pumps:home")
