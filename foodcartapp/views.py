from django.db.utils import IntegrityError
from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product
from .utils import validate_products_list


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
    try:
        payload = request.data

        validation_payload = validate_products_list(payload)
        if validation_payload:
            return validation_payload

        order = Order.objects.create(
            firstname=payload.get("firstname"),
            lastname=payload.get("lastname"),
            phonenumber=payload.get("phonenumber"),
            address=payload.get("address"),
        )
        order_items = [
            OrderItem(
                order=order,
                product_id=product.get("product"),
                quantity=product.get("quantity"),
            )
            for product in payload.get("products")
        ]

        OrderItem.objects.bulk_create(order_items)

        return Response(
            {"success": "Order created successfully"},
            status=status.HTTP_201_CREATED,
        )

    except IntegrityError:
        order.delete()
        return Response(
            {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
