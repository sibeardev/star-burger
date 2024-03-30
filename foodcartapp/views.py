from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

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


@api_view(["POST"])
def register_order(request: HttpRequest):

    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serialize_order = serializer.validated_data

    order = Order.objects.create(
        firstname=serialize_order.get("firstname"),
        lastname=serialize_order.get("lastname"),
        phonenumber=serialize_order.get("phonenumber"),
        address=serialize_order.get("address"),
    )

    order_items = [
        OrderItem(
            order=order,
            product=order_item.get("product"),
            quantity=order_item.get("quantity"),
            price=order_item.get("product").price,
        )
        for order_item in serialize_order.get("products")
    ]
    OrderItem.objects.bulk_create(order_items)

    return Response(
        data=OrderSerializer(order).data,
        status=status.HTTP_201_CREATED,
    )
