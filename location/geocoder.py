import requests
from geopy import distance

from .models import Location


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        },
    )
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"][
        "featureMember"
    ]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return lon, lat


def calculate_distance(from_coordinates, to_coordinates):
    return round(distance.distance(from_coordinates, to_coordinates).km, 3)


def get_locations(addresses):
    return {
        location.address: (location.lat, location.lon)
        for location in Location.objects.filter(address__in=addresses)
    }


def calculate_restaurant_distances(restaurants, order_location):
    return sorted(
        [
            {
                "restaurant": restaurant,
                "distance": calculate_distance(
                    (restaurant.lat, restaurant.lon), order_location
                ),
            }
            for restaurant in restaurants
        ],
        key=lambda x: x["distance"],
    )
