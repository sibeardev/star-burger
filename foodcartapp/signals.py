from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from location.geocoder import fetch_coordinates
from location.models import Location
from star_burger.settings import YANDEX_API_KEY

from .models import Order, Restaurant


@receiver(post_save, sender=Restaurant)
def add_coordinates(sender, instance, created: bool, **kwargs):
    if created:
        lon, lat = fetch_coordinates(YANDEX_API_KEY, instance.address)
        instance.lon = lon
        instance.lat = lat
        instance.save()


@receiver(pre_save, sender=Order)
def add_location(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Order.objects.get(pk=instance.pk)
        new_address = instance.address
        if new_address != old_instance.address:
            coordinates = fetch_coordinates(YANDEX_API_KEY, new_address)
            if coordinates:
                lon, lat = coordinates
                Location.objects.get_or_create(
                    address=new_address, lat=lat, lon=lon
                )
