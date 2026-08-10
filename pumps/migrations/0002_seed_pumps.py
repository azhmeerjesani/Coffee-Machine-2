# Seeds the 6 pumps wired to the relay board (BCM pins, same as the
# reference Smart Bartender hardware this project is based on).

from django.db import migrations

PUMP_PINS = [17, 27, 22, 23, 24, 25]


def seed_pumps(apps, schema_editor):
    Pump = apps.get_model("pumps", "Pump")
    for number, pin in enumerate(PUMP_PINS, start=1):
        Pump.objects.get_or_create(number=number, defaults={"gpio_pin": pin})


def remove_pumps(apps, schema_editor):
    Pump = apps.get_model("pumps", "Pump")
    Pump.objects.filter(gpio_pin__in=PUMP_PINS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pumps", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_pumps, remove_pumps),
    ]
