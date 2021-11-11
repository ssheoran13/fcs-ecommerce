from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.db.models import Sum 
from django_countries.fields import CountryField
from django.contrib.auth.models import User


CATEGORY_CHOICES = (
    ('S', 'Clothes'),
    ('SW', 'Electronics'),
    ('OW', 'Stationery')
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField()
    image2 = models.ImageField(blank=True, null=True)
    
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        }) 

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        }) 
    
    def category_url_clothes(self):
        return reverse("core:home") + '/S'
    
    def category_url_electronics(self):
        return reverse("core:home") + '/SW'
    
    def category_url_stationery(self):
        return reverse("core:home") + '/O'

        
class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100,null=True)
    apartment_address = models.CharField(max_length=100,null=True)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    
    def __str__(self):
        return self.code


class Buyer(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    otp_done = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Seller(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    otp_done = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
class SellerItem(models.Model):
    user=models.ForeignKey(Seller, on_delete=models.CASCADE)
    item=models.ForeignKey(Item, on_delete=models.CASCADE)


class SiteAdmin(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)


class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    
    def get_decline_url(self):
        return reverse("core:viewfiles")+'decline/'+str(self.id)


    def get_accept_url(self):
        return reverse("core:viewfiles")+'accept/'+str(self.id)