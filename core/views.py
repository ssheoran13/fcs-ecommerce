import stripe
import random

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
from django.views import generic
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login
from .forms import CheckoutForm, LoginForm, NewItemForm, SignUpForm, DocumentForm
from .models import Buyer, Item, OrderItem, Order, BillingAddress, Payment, Coupon, Item, Seller, Document, SellerItem, SiteAdmin
from ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

stripe.api_key = settings.STRIPE_SECRET_KEY


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "product.html", context)


def model_form_upload(request):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_seller')
        
        user = request.user
        seller=Seller.objects.filter(user=user).first()
        if seller == None:
            messages.info(request, "You are not a seller. Please sign up as a Seller.")
            return redirect('/')
        
        if request.method == 'POST':
            form = DocumentForm(request.POST, request.FILES)
            
            if form.is_valid():
                filename=str(form.cleaned_data['document'])
                if filename[-3:]=='pdf':
                    description = form.cleaned_data.get('description')
                    document = form.cleaned_data.get('document')

                    if seller.is_verified == True:
                        messages.info(request, "You are already verified.")
                        return redirect('core:add-new-item')
                        
                    uploaded_document = Document(description=description, document=document, user=user)
                    uploaded_document.save()
                    messages.success(request, 'Document Uploaded Successfully')
                    
                    return render(request, 'sellerhome.html')
                else:
                    messages.info(request, "Please upload a valid PDF file.")
                    return redirect('core:sellerhome')
                            
        else:
            form = DocumentForm()
        return render(request, 'core/model_form_upload.html', {
            'form': form
        })
    except Exception as e:
        print(e)
        messages.info(request, "Some Error Occurred")
        return redirect('core:sellerhome')

def decline_request(request,id):
    try:
        doc= Document.objects.get(id=id)
        user=doc.user
        doc.delete()
        messages.success(request, "Seller "+user.username+"'s request has been declined.")
                    
        return redirect('core:adminhome')
    except Exception as e:
        print(e)
        messages.info(request, "Some Error Occurred")
        return redirect('core:adminhome')

def accept_request(request,id):
    try:
        doc= Document.objects.get(id=id)
        user=doc.user
        doc.delete()
        seller=Seller.objects.get(user=user)
        seller.is_verified=True
        seller.save()
        print(seller.is_verified)
        messages.success(request, "Seller "+user.username+"'s request has been accepted.")
                    
        return redirect('core:adminhome')
    except Exception as e:
        print(e)
        messages.info(request, "Some Error Occurred")
        return redirect('core:adminhome')

def ViewSellerProfile(request):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_seller')

        user = request.user
        seller = Seller.objects.filter(user=user).first()
        if seller == None:
            messages.info(request, "You are not a seller. Please sign up as a Seller.")
            return redirect('/')

        seller=Seller.objects.filter(user=user).first()
        selleritems=SellerItem.objects.filter(user=seller)
        return render(request, 'view_seller_profile.html', {'seller': seller, 'selleritems': selleritems})
    except Exception as e:
        print(e)
        messages.info(request, "Some Error Occurred")
        return redirect('core:sellerhome')    
    

def ViewDocument(request):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "You are not Admin. Please login as Admin.")
            return redirect('core:home')

        user = request.user
        admin = SiteAdmin.objects.filter(user=user).first()
        if admin == None:
            messages.info(request, "You are not Admin. Please login as Admin.")
            return redirect('/')

        documents = Document.objects.all()
        for i in documents:
            print(i.document)    
        return render(request, 'view_document.html', {'documents': documents})
    except Exception as e:
        print(e)
        messages.info(request, "Some Error Occurred")
        return redirect('core:adminhome')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            user = self.request.user
            buyer = Buyer.objects.filter(user=user).first()
            if buyer == None:
                print("this 1")
                messages.info(self.request, "You are not a Buyer. Please login as Buyer.")
                return redirect('/')
            if user == None:
                return redirect('core:home')

            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:home')

            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'order': order
            }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order.")
            return redirect('core:checkout')

        return render(self.request, "checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            user = self.request.user
            buyer = Buyer.objects.filter(user=user).first()
            if buyer == None:
                print("this 2")
                messages.info(self.request, "You are not a Buyer. Please login as Buyer.")
                return redirect('/')
            if user == None:
                return redirect('core:home')

            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:home')
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                print(form.cleaned_data)
                street_address = form.cleaned_data['shipping_address']
                print(street_address)
                apartment_address = form.cleaned_data['shipping_address2']
                print(apartment_address)
                country = form.cleaned_data.get('shipping_country')
                zip = form.cleaned_data.get('shipping_zip')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip = zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected.")
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("core:order-summary")
        
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occoured")
            return redirect("core:home")


class PaymentView(View):
    def get(self, *args, **kwargs):
        try:
            user = self.request.user
            buyer = Buyer.objects.filter(user=user).first()
            if buyer == None:
                print("this 3")
                messages.info(self.request, "You are not a Buyer. Please login as Buyer.")
                return redirect('/')
            if user == None:
                return redirect('core:home')

            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:home')
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'order': order
            }
            return render(self.request, "payment.html", context)
        except Exception as e:
            print(e)
            messages.info(self.request, "Some Error Occurred")
            return redirect('core:home')

    def post(self, *args, **kwargs):
        
        user = self.request.user
        buyer = Buyer.objects.filter(user=user).first()
        if buyer == None:
            print("this 4")
            messages.info(self.request, "You are not a Buyer. Please login as Buyer.")
            return redirect('/')
        if user == None:
            return redirect('core:home')

        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(self.request, "Please Log In :D")
            return redirect('core:home')
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)
        print(order)
        print(token)
        print(amount)

        charge = stripe.Charge.create(
            amount=amount,  # cents
            currency="inr",
            source=token,
            description="my first charge"
        )
        try:
            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your order was successful!")
            return redirect("/")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate Limit Error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid Parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not Authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network Error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.error(
                self.request, "A serious error occured. We have been notified.")
            return redirect("/")


class HomeView(ListView):

    model = Item
    paginate_by = 12
    template_name = "home.html"
    search_query = ""
    @method_decorator(ratelimit(key='ip', rate='60/m', method='POST'))
    def post(self, *args, **kwargs):
        try:
            print(self.model)
            print(self.request.POST)
            search_query = self.request.POST.get("search")
            print("response:",search_query)
            obj = Item.objects.all().filter(title=search_query)
            for i in obj:
                print("test", i.title)
            self.search_query = search_query
            print(self.model)
            return render(self.request, "home.html", {'object_list': obj})
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occurred")
            return redirect('core:home')

    @method_decorator(ratelimit(key='ip', rate='60/m'))
    def get(self, *args, **kwargs):
        try:
            user = self.request.user
            was_limited = getattr(self.request, 'limited', False)
            if was_limited:
                messages.error(self.request, 'Too Many Requests')
                return redirect('core:ratelimit')
            print(was_limited)
            user_object = User.objects.filter(username=user.username).first()
            if user_object == None:
                if len(self.request.GET):
                    category = self.request.GET.get('category')
                    obj = Item.objects.filter(category=category)
                    print(len(obj))
                    return render(self.request, 'home.html', {'object_list':obj})

                return render(self.request, 'home.html', {'object_list':Item.objects.all()})
            
            seller = Seller.objects.filter(user=user).first()
            site_admin = SiteAdmin.objects.filter(user=user).first()
            buyer = Buyer.objects.filter(user=user).first()

            if seller != None:
                return redirect('core:sellerhome')
            
            elif site_admin != None:
                return redirect('core:adminhome')

            elif buyer != None:
                if len(self.request.GET):
                    category = self.request.GET.get('category')
                    obj = Item.objects.filter(category=category)
                    print(len(obj))
                    return render(self.request, 'home.html', {'object_list':obj})

                return render(self.request, 'home.html', {'object_list':Item.objects.all()})
            
            else:
                if len(self.request.GET):
                    category = self.request.GET.get('category')
                    obj = Item.objects.filter(category=category)
                    print(len(obj))
                    return render(self.request, 'home.html', {'object_list':obj})
                return render(self.request, 'home.html', {'object_list':Item.objects.all()})
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occurred")
            return redirect('core:home')

def get_category_products(request, category):
    obj = Item.objects.filter(category=category)
    return render(request, 'home.html', {'object_list':obj})


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            user = self.request.user
            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:home')

            buyer = Buyer.objects.filter(user=user).first()
            if buyer == None:
                print("this 5")
                messages.info(self.request, "You are not a buyer. Please login as Buyer.")
                return redirect('/')
            try:
                order = Order.objects.get(user=self.request.user, ordered=False)
                context = {
                    'object': order
                }
                return render(self.request, 'order_summary.html', context)
            
            except ObjectDoesNotExist:
                messages.error(self.request, "You do not have an active order")
                return redirect("/")
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occurred")
            return redirect('core:home')


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


# @login_required
class AddNewItemView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            user = self.request.user
            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:login_seller')

            user = self.request.user
            seller=Seller.objects.filter(user=user).first()
            if seller == None:
                messages.info(self.request, "You are not a seller. Please sign up as a Seller.")
                return redirect('/')

            form = NewItemForm()
            context = {
                'form': form
            }
            return render(self.request, 'add-new-item.html', context)
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occurred")
            return redirect('core:sellerhome')

    def post(self, *args, **kwargs):
        try:
            user = self.request.user
            user_object = User.objects.filter(username=user.username).first()
            if user_object == None :
                messages.info(self.request, "Please Log In :D")
                return redirect('core:login_seller')

            user = self.request.user
            seller=Seller.objects.filter(user=user).first()
            if seller == None:
                messages.info(self.request, "You are not a seller. Please sign up as a Seller.")
                return redirect('/')

            form = NewItemForm(self.request.POST or None,self.request.FILES)
            if form.is_valid():
                user=self.request.user
                if user==None:
                    messages.error(self.request, "Please login first.")
                    return redirect("/")
                seller=Seller.objects.filter(user=user).first()
                if seller==None:
                    messages.error(self.request, "You are not a seller.")
                    return redirect("/")
                if seller.is_verified==False:
                    messages.error(self.request, "You are not verified as a seller yet.")
                    return render(self.request,'sellerhome.html')
                
                # print(self.request.POST['image'])
                # print(self.request.FILES)
                print(form.cleaned_data)
                title = form.cleaned_data.get('title')
                price = form.cleaned_data.get('price')
                label = 'P'
                description = form.cleaned_data.get('description')
                category = form.cleaned_data.get('category')
                slug = title.replace(' ', '-') + str(random.randint(1,100))
                image = form.cleaned_data.get('image')
                item = Item(title=title, price=price,
                            category=category, label=label, slug=slug, description=description, image=image)
                # item = form.save(commit=False)
                # print(item_data)
                
                
                item.user = self.request.user
                item.save()
                seller_item=SellerItem(user=seller,item=item)
                seller_item.save()
                messages.success(self.request, "Item added successfully")
                return render(self.request,'sellerhome.html')
            else:
                messages.error(self.request, "Item was not added")
                return redirect("core:add-new-item")
        except Exception as e:
            print(e)
            messages.error(self.request, "Some Error Occurred")
            return redirect('core:sellerhome')

@ratelimit(key='ip', rate='60/m')
def add_to_cart(request, slug):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_buyer')
        
        user = request.user
        buyer=Buyer.objects.filter(user=user).first()
        if buyer == None:
            messages.info(request, "You are not a Buyer. Please sign up as a Buyer.")
            return redirect('/')
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        print("cart",was_limited)
        item = get_object_or_404(Item, slug=slug)
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            user=request.user,
            ordered=False
        )
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart.")

                return redirect("core:order-summary")
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")

            return redirect("core:order-summary")
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


def add_new_item(request):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_seller')
        
        user = request.user
        seller=Seller.objects.filter(user=user).first()
        if seller == None:
            messages.info(request, "You are not a seller. Please sign up as a Seller.")
            return redirect('/')
        
        if request.method == "POST":
            form = NewItemForm(request.POST, request.FILES)
            if form.is_valid():
                item = form.save(commit=False)
                item.user = request.user
                item.save()
                messages.success(request, "Your item has been added successfully")
                return redirect("core:add-new-item")
        else:
            form = NewItemForm()
        return render(request, 'add_new_item.html', {'form': form})
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:sellerhome')


@login_required
def remove_from_cart(request, slug):
    try:
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
                order.items.remove(order_item)
                messages.info(request, "This item was removed to your cart.")
                return redirect("core:order-summary")
            else:
                messages.info(request, "This item was not in your cart.")
                return redirect("core:order-summary", slug=slug)
        else:
            messages.info(request, "You do not have an active order.")
            return redirect("core:order-summary", slug=slug)
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


@login_required
def remove_single_item_from_cart(request, slug):
    try:
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
                if order_item.quantity > 1:
                    order_item.quantity -= 1
                    order_item.save()
                else:
                    order.items.remove(order_item)
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                messages.info(request, "This item was not in your cart.")
                return redirect("core:product", slug=slug)
        else:
            messages.info(request, "You do not have an active order.")
            return redirect("core:product", slug=slug)
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


def get_coupon(request, code):
    try:
        coupon = Coupon.object.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist.")
        return redirect('core:checkout')


def add_coupon(request):
    try:
        order = Order.objects.get(user=request.user, ordered=False)
        order.coupon = get_coupon(request, code)
        order.save()
        messages.success(request, 'Successfully added coupon')
        return redirect('core:checkout')

    except ObjectDoesNotExist:
        messages.info(request, "You do not have an active order.")
        return redirect('core:checkout')


@ratelimit(key='ip', rate='2/s')
def login_buyer(request):
    try:
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user_obj = User.objects.filter(username=username).first()

                if user_obj is None:
                    messages.error(request, 'User Does Not Exist')
                    return redirect('core:login_buyer')

                profile = Buyer.objects.filter(user=user_obj).first()
                if profile is None:
                    messages.error(request, 'Buyer Does Not Exist')
                    return redirect('core:login_buyer')

                if profile.otp_done!=True:
                    messages.info(request, "Please verify your Email ID")
                    return redirect('core:login_buyer')
                
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    messages.success(request, 'Successfully logged in')
                    return redirect('core:home')
                else:
                    messages.error(request, 'Invalid username or password')
                    return redirect('core:login_buyer')
        return render(request, 'login_buyer.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

@ratelimit(key='ip', rate='2/s')
def signup_buyer(request):
    try:

        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                email = form.cleaned_data.get('email')

                if User.objects.filter(username=username).first():
                    messages.success(request, 'Username Taken')
                    return redirect('core:signup_buyer')
                
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.save()
                auth_token = str(uuid.uuid4())
                buyer = Buyer.objects.create(user=user, auth_token=auth_token)
                buyer.save()
                messages.success(request, 'Account Created Successfully. Please Check Your Email To Verify Your Account.')
                link = request.build_absolute_uri()
                print(link)
                send_email(email,build_link(link,auth_token,"buyer"))
                return redirect('core:signup_buyer')
        return render(request, 'signup_buyer.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

def verify_buyer(request,auth_token):
    try:
        buyer = Buyer.objects.get(auth_token=auth_token)
        buyer.otp_done = True
        buyer.save()
        messages.success(request, 'Account Verified Successfully')
        return redirect('core:login_buyer')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')
def build_link_forgot_password(path):
    count = 0
    ans = ""
    i = 0
    while count<3:
        if path[i] == '/':
            count += 1
        ans += path[i]
        i += 1
    ans+="reset_password"
    return ans

def build_link(path,auth_token,type):
    count = 0
    ans = ""
    i = 0
    while count<3:
        if path[i] == '/':
            count += 1
        ans += path[i]
        i += 1
    ans+="otp-"+type+"/"+auth_token
    return ans

def send_email_forgot_password(email,link):
    subject = 'Reset Password'
    message = 'Click on the link to reset your password \n'+link
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail( subject, message, email_from, recipient_list )     

def send_email(email,link):
    subject = 'Activate your account'
    message = 'Activate your account by clicking the following link: ' + link
    from_email = settings.EMAIL_HOST_USER
    to_list = [email]
    send_mail(subject, message, from_email, to_list, fail_silently=True)

def SellerHome(request):
    try:
        user = request.user
        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_seller')
        seller = Seller.objects.filter(user=user_object).first()
        return render(request,'sellerhome.html', {'seller':seller})
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

@ratelimit(key='ip', rate='2/s')
def login_seller(request):
    try:
   
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
        
                user_obj = User.objects.filter(username=username).first()
                
                if user_obj is None:
                    messages.error(request, 'User Does Not Exist')
                    return redirect('core:login_buyer')

                profile = Seller.objects.filter(user=user_obj).first()

                if profile is None:
                    messages.error(request, 'You Are Not Registered As A Seller')
                    return redirect('core:login_seller')
                if profile.otp_done!=True:
                    messages.info(request, "Please verify your Email ID")
                    return redirect('core:login_seller')
                
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    messages.success(request, 'Successfully logged in')
                    return redirect('core:sellerhome')
                else:
                    messages.error(request, 'Invalid username or password')
                    return redirect('core:login_seller')
        return render(request, 'login_seller.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


@ratelimit(key='ip', rate='2/s')
def signup_seller(request):
    try:

        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                email = form.cleaned_data.get('email')

                if User.objects.filter(username=username).first():
                    messages.success(request, 'Username Taken')
                    return redirect('core:signup_buyer')
                
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.save()
                auth_token = str(uuid.uuid4())
                buyer = Seller.objects.create(user=user, auth_token=auth_token)
                buyer.save()
                messages.success(request, 'Account Created Successfully. Please Check Your Email To Verify Your Account.')
                link = request.build_absolute_uri()
                print(link)
                send_email(email,build_link(link,auth_token,"seller"))
                return redirect('core:signup_seller')
        return render(request, 'signup_seller.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

def verify_seller(request,auth_token):
    try:
        seller = Seller.objects.get(auth_token=auth_token)
        seller.otp_done = True
        seller.save()
        messages.success(request, 'Account Verified Successfully')
        return redirect('core:login_seller')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


def siteadmin(request):
    try:
        user = request.user
        if user == None :
            messages.error(request, 'User does not exist')
            return redirect('core:login_admin')

        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            return redirect('core:login_admin')

        site_admin = SiteAdmin.objects.filter(user=user).first()
        if site_admin is None:
            messages.error(request, 'You Are Not Registered As A Site Admin')
            return redirect('core:login_admin')

        if request.method == 'POST':
            user_name = request.POST.get('user_name')
            user = User.objects.get(username = user_name)
            user.delete()
            return redirect('core:siteadmin')

        buyer_list = Buyer.objects.all()
        seller_list = Seller.objects.all()
        user_list = User.objects.all()

        listy = [["Buyer", buyer_list], ["Seller", seller_list]]

        return render(request, 'siteadmin.html', {'object_list': listy})
    
    except ObjectDoesNotExist:
        messages.error(request, 'The user you entered does not exist.')
        return redirect('core:adminhome')

    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')


def deleteproduct(request):
    try:
        user = request.user
        if user == None :
            messages.error(request, 'User does not exist')
            return redirect('core:login_admin')

        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_admin')

        site_admin = SiteAdmin.objects.filter(user=user).first()
        if site_admin is None:
            messages.error(request, 'You Are Not Registered As A Site Admin')
            return redirect('core:login_admin')

        if request.method == 'POST':
            title_ = request.POST.get('title_')
            print(title_)
            title = Item.objects.get(title = title_)

            print(title)
            title.delete()
            return redirect('core:deleteproduct')
    

        product_list = Item.objects.all()
        item_owner_list = []
        for item in product_list:
            seller_item = SellerItem.objects.filter(item=item).first()
            user = seller_item.user
            item_owner_list.append([item, user.user.username])


        return render(request, 'deleteproduct.html', {'object_list': item_owner_list})
    except ObjectDoesNotExist:
        messages.error(request, "The product you entered does not exist.")
        return redirect('core:adminhome')

    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')




@ratelimit(key='ip', rate='2/s')
def login_admin(request):
    try:
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'Too Many Requests')
            return redirect('core:ratelimit')
        if request.method == 'POST':
            form = LoginForm(request.POST)

            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user_obj = User.objects.filter(username=username).first()

                if user_obj is None:
                    messages.error(request, 'User Does Not Exist')
                    return redirect('core:login_admin')

                profile = SiteAdmin.objects.filter(user=user_obj).first()

                if profile is None:
                    messages.error(request, 'You Are Not Registered As A SiteAdmin')
                    return redirect('core:login_admin')
                else:
                    user = authenticate(request, username=username, password=password)

                    if user is not None:
                        login(request, user)
                        messages.success(request, 'Successfully logged in')
                        return redirect('core:adminhome')
                    else:
                        messages.error(request, 'Invalid username or password')
                        return redirect('core:login_admin')

        return render(request, 'login_admin.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')



def adminhome(request):
    try:
        user = request.user
        
        user_object = User.objects.filter(username=user.username).first()
        if user_object == None :
            messages.info(request, "Please Log In :D")
            return redirect('core:login_admin')
        
        siteadmin = SiteAdmin.objects.filter(user=user).first()
        if siteadmin == None:
            messages.info(request, "You are not Admin. Please login as Admin.")
            return redirect('/')
        # user = request.user
        if user == None:
            return redirect('core:login_admin')


        return render(request,'adminhome.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

def rate_limit(request):
    return render(request, 'rate_limit.html')

def forgot_password(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            user = User.objects.filter(username=username).first()
            if user is None:
                messages.error(request, 'User Does Not Exist')
                return redirect('core:home')
            else:
                link = request.build_absolute_uri()
                link = build_link_forgot_password(link)
                send_email_forgot_password(user.email,link)
                messages.success(request, 'Email Sent to reset your password')
                return redirect('core:home')
        return render(request, 'forgot_password.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')

def reset_password(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = User.objects.filter(username=username).first()
            if user is None:
                messages.error(request, 'User Does Not Exist')
                return redirect('core:home')
            else:
                user.set_password(password)
                user.save()
                messages.success(request, 'Password Changed Successfully')
                return redirect('core:home')
        return render(request, 'reset_password.html')
    except Exception as e:
        print(e)
        messages.error(request, "Some Error Occurred")
        return redirect('core:home')