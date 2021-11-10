from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    login_admin,
    login_buyer,
    login_seller,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    add_coupon,
    add_new_item,
    AddNewItemView,
    signup_buyer,
    signup_seller,
    verify_buyer,
    verify_seller,
    model_form_upload,
    ViewDocument,
    decline_request,
    accept_request,
    ViewSellerProfile,
    SellerHome,
    siteadmin,
    deleteproduct,
    login_admin,
    adminhome,
    get_category_products
)


app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', add_coupon, name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    # path('add-new-item/', add_new_item, name='add-new-item')
    path('add-new-item/', AddNewItemView.as_view(), name='add-new-item'),
    path("login_buyer/",login_buyer, name='login_buyer'),
    path("signup_buyer/", signup_buyer, name='signup_buyer'),
    path("otp-buyer/<auth_token>/", verify_buyer, name="verify_buyer"),
    path("login_seller/",login_seller, name='login_seller'),
    path("signup_seller/", signup_seller, name='signup_seller'),
    path("otp-seller/<auth_token>/", verify_seller, name="verify_seller"),
    path('uploadfile/', model_form_upload, name='uploadfile'),
    path('viewfiles/', ViewDocument, name='viewfiles'),
    path('viewfiles/decline/<id>',decline_request, name='decline_request'),
    path('viewfiles/accept/<id>',accept_request, name='accept_request'),
    path('viewseller/',ViewSellerProfile, name='viewseller'),
    path('sellerhome/',SellerHome, name='sellerhome'),
    path("siteadmin/", siteadmin, name="siteadmin"),
    path("deleteproduct/", deleteproduct, name="deleteproduct"),
    path("login_admin/", login_admin, name="login_admin"),
    path("adminhome/", adminhome, name="adminhome"),
    path("home/<category>", get_category_products, name="get_category_products")
]