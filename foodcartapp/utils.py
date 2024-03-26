import phonenumbers
from rest_framework import status
from rest_framework.response import Response


def validate_phonenumber(phonenumber):
    try:
        parsed_phonenumber = phonenumbers.parse(phonenumber, "RU")

        return phonenumbers.is_valid_number(parsed_phonenumber)

    except phonenumbers.phonenumberutil.NumberParseException:
        return False


def validate_products_list(payload):

    products = payload.get("products")

    if not isinstance(products, list):
        message = (
            "products: Ожидался list со значениями, "
            f"но был получен {type(products)}"
        )
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    if not products:
        message = "products: Этот список не может быть пустым."
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    for field in ["firstname", "lastname", "phonenumber", "address"]:

        if field not in payload or not payload.get(field):
            message = f"{field}: Это поле не может быть пустым"
            return Response(
                {"error": message}, status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(payload.get(field), str):
            message = (
                f"{field}: Ожидался str, "
                f"но был получен {type(payload.get(field))}"
            )
            return Response(
                {"error": message}, status=status.HTTP_400_BAD_REQUEST
            )

    if not validate_phonenumber(payload.get("phonenumber")):
        message = "phonenumber: Введен некорректный номер телефона."
        return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
