import json

from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static

from .models import Order, OrderItem, Product


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
    return JsonResponse(
        dumped_products,
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


def register_order(request: HttpRequest):
    try:
        payload = json.loads(request.body)

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

        return JsonResponse(
            {"success": "Order created successfully"}, status=201
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
