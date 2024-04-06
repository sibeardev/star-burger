from django.db.models.signals import post_save
from django.dispatch import receiver

from star_burger.settings import YANDEX_API_KEY

from .geocoder import fetch_coordinates
from .models import Restaurant


@receiver(post_save, sender=Restaurant)
def add_coordinates(sender, instance, created: bool, **kwargs):
    if created:
        lon, lat = fetch_coordinates(YANDEX_API_KEY, instance.address)
        instance.lon = lon
        instance.lat = lat
        instance.save()
