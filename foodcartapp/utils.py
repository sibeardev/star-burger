from rest_framework import status
from rest_framework.response import Response


def validate_products_list(products):

    if not isinstance(products, list):
        message = (
            "products: Ожидался list со значениями, "
            f"но был получен {type(products)}"
        )

        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    if not products:
        message = "products: Этот список не может быть пустым."

        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
