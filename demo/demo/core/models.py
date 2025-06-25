from django.db import models

F = models.Field


class Measurement(models.Model):
    name: F = models.CharField(max_length=128)
    time: F = models.DateTimeField(
        "Time", help_text="The date and time the measurement was made."
    )
    pressure: F = models.DecimalField(max_digits=8, decimal_places=2)
    temperature: F = models.DecimalField(max_digits=8, decimal_places=2)
    restricted: F = models.BooleanField(default=False)
    open: F = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Measurement({self.name}, {self.time})"
