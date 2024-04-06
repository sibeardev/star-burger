from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
        "Адрес", max_length=150, unique=True, db_index=True
    )
    lat = models.FloatField("Широта", db_index=True, blank=True)
    lon = models.FloatField("Долгота", db_index=True, blank=True)
    created_at = models.DateTimeField("Создан", default=timezone.now)

    class Meta:
        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"

    def __str__(self):
        return self.address
