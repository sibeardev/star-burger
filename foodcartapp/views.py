from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from location.geocoder import fetch_coordinates
from location.models import Location
from star_burger.settings import YANDEX_API_KEY

from .models import Order, OrderItem, Product
from .utils import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse(
        [
            {
                "title": "Burger",
                "src": static("burger.jpg"),
                "text": "Tasty Burger at your door step",
            },
            {
                "title": "Spices",
                "src": static("food.jpg"),
                "text": "All Cuisines",
            },
            {
                "title": "New York",
                "src": static("tasty.jpg"),
                "text": "Food is incomplete without a tasty dessert",
            },
        ],
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


@api_view(["GET"])
def product_list_api(request):
    products = Product.objects.select_related("category").available()

    dumped_products = []
    for product in products:
        dumped_product = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "special_status": product.special_status,
            "description": product.description,
            "category": (
                {
                    "id": product.category.id,
                    "name": product.category.name,
                }
                if product.category
                else None
            ),
            "image": product.image.url,
            "restaurant": {
                "id": product.id,
                "name": product.name,
            },
        }
        dumped_products.append(dumped_product)

    return Response(dumped_products)


@transaction.atomic
@api_view(["POST"])
def register_order(request: HttpRequest):

    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serialize_order = serializer.validated_data
    address = serialize_order.get("address")

    order = serializer.save()

    coordinates = fetch_coordinates(YANDEX_API_KEY, order.address)
    if coordinates:
        lon, lat = coordinates
        Location.objects.get_or_create(address=address, lat=lat, lon=lon)

    return Response(
        data=OrderSerializer(order).data,
        status=status.HTTP_201_CREATED,
    )
