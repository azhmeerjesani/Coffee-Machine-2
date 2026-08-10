from django.db import models

# Matches the hardware default: ~100mL per 60 seconds.
DEFAULT_ML_PER_SECOND = 100 / 60.0


class Pump(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    gpio_pin = models.PositiveSmallIntegerField(unique=True)
    ingredient_name = models.CharField(max_length=100, blank=True, default="")
    ml_per_second = models.FloatField(default=DEFAULT_ML_PER_SECOND)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Pump {self.number} ({self.ingredient_name or 'unassigned'})"

    def seconds_for(self, amount_ml):
        return amount_ml / self.ml_per_second


class Recipe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """One pump's contribution to a recipe. Ingredients that share a `step`
    run at the same time (in parallel); steps run one after another in
    ascending order."""

    recipe = models.ForeignKey(Recipe, related_name="ingredients", on_delete=models.CASCADE)
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE)
    amount_ml = models.FloatField()
    step = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ("recipe", "pump")
        ordering = ["step", "pump__number"]

    def __str__(self):
        return f"Step {self.step}: {self.amount_ml}mL via {self.pump}"
