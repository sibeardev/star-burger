from collections import defaultdict
from functools import reduce

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from location.geocoder import calculate_restaurant_distances, get_locations


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )
    lat = models.FloatField("Широта", db_index=True, blank=True)
    lon = models.FloatField("Долгота", db_index=True, blank=True)

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(
            availability=True
        ).values_list("product")
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField(
        "в продаже", default=True, db_index=True
    )

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_order_cost(self):
        return self.annotate(
            cost=Sum(F("items__quantity") * F("items__product__price"))
        )

    def add_restaurants_with_products(self):
        menu_items = RestaurantMenuItem.objects.select_related(
            "restaurant", "product"
        )
        product_restaurants_map = defaultdict(list)
        for menu_item in menu_items:
            product_restaurants_map[menu_item.product].append(
                menu_item.restaurant
            )

        locations = get_locations(set([order.address for order in self]))

        for order in self:
            order_items = order.items.all()
            grouped_by_product_restaurants = [
                product_restaurants_map[product.product]
                for product in order_items
            ]
            restaurant_with_product = reduce(
                set.intersection, map(set, grouped_by_product_restaurants)
            )
            try:
                order_location = locations[order.address]
                order.restaurant_with_product = calculate_restaurant_distances(
                    restaurant_with_product, order_location
                )
            except KeyError:
                order.restaurant_with_product = [
                    {"restaurant": restaurant}
                    for restaurant in restaurant_with_product
                ]

        return self


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        NEW = "new", "Новый"
        PREPARING = "preparing", "Готовится"
        DELIVERING = "delivering", "Доставляется"
        COMPLETED = "completed", "Выполнен"

    class OrderPayments(models.TextChoices):
        CASH = "cash", "Наличные"
        CARD = "card", "Карта"
        ONLINE = "online", "Онлайн"

    firstname = models.CharField(
        "Имя",
        max_length=50,
        db_index=True,
    )
    lastname = models.CharField(
        "Фамилия",
        max_length=50,
        db_index=True,
    )
    address = models.CharField(
        "Адрес",
        max_length=150,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        "Телефон",
        region="RU",
        db_index=True,
    )
    created_at = models.DateTimeField("Создан", default=timezone.now)
    called_at = models.DateTimeField(
        "Согласован",
        blank=True,
        null=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        "Доставлен",
        blank=True,
        null=True,
        db_index=True,
    )
    status = models.CharField(
        "Статус",
        max_length=12,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
        db_index=True,
    )
    comment = models.TextField("Комментарий", blank=True)
    payments = models.CharField(
        "Способ оплаты",
        max_length=10,
        choices=OrderPayments.choices,
        blank=True,
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name="Ресторан",
        related_name="restaurants",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        db_index=True,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ № {self.pk}"


class OrderItem(models.Model):
    """Связывающая модель, которая отображает связь между заказом и продуктом,
    и количество каждого продукта в заказе"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество",
        validators=[MinValueValidator(1)],
    )
    price = models.DecimalField(
        "Цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def __str__(self):
        return f"{self.product.name} для заказа №{self.order.pk}"
