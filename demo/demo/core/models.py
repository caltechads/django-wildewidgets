from django.db import models

class Measurement(models.Model):
    name = models.CharField(max_length=128)
    time = models.DateTimeField(
        'Time',
        help_text='The date and time the measurement was made.'
    )
    pressure = models.DecimalField(max_digits=8, decimal_places=2)
    temperature = models.DecimalField(max_digits=8, decimal_places=2)
    restricted = models.BooleanField(default=False)
    open = models.BooleanField(default=True)
