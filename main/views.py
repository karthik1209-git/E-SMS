from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, CartItems, Reviews
from django.contrib import messages
from .forms import ContactForm
from django.core.mail import send_mail, BadHeaderError
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
'''from django.conf import settings
from django.urls import reverse'''
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .decorators import *
from django.db.models import Sum

class MenuListView(ListView):
    model = Item
    template_name = 'main/home.html'
    context_object_name = 'menu_items'

def menuDetail(request, slug):
    item = Item.objects.filter(slug=slug).first()
    reviews = Reviews.objects.filter(rslug=slug).order_by('-id')[:7] 
    context = {
        'item' : item,
        'reviews' : reviews,
    }
    return render(request, 'main/services.html', context)

@login_required
def add_reviews(request):
    if request.method == "POST":
        user = request.user
        rslug = request.POST.get("rslug")
        item = Item.objects.get(slug=rslug)
        review = request.POST.get("review")

        reviews = Reviews(user=user, item=item, review=review, rslug=rslug)
        reviews.save()
        messages.success(request, "Thankyou for reviewing this product!!")
    return redirect(f"/services/{item.slug}")

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = ['title', 'image', 'description', 'price', 'hours', 'instructions', 'labels', 'label_colour', 'slug']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    fields = ['title', 'image', 'description', 'price', 'hours', 'instructions', 'labels', 'label_colour', 'slug']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def test_func(self):
        item = self.get_object()
        if self.request.user == item.created_by:
            return True
        return False

class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    success_url = '/item_list'

    def test_func(self):
        item = self.get_object()
        if self.request.user == item.created_by:
            return True
        return False

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    cart_item = CartItems.objects.create(
        item=item,
        user=request.user,
        ordered=False,
    )
    messages.info(request, "Added to Cart!!Continue Shopping!!")
    return redirect("main:cart")

@login_required
def get_cart_items(request):
    cart_items = CartItems.objects.filter(user=request.user,ordered=False)
    bill = cart_items.aggregate(Sum('item__price'))
    number = cart_items.aggregate(Sum('quantity'))
    hours = cart_items.aggregate(Sum('item__hours'))
    total = bill.get("item__price__sum")
    count = number.get("quantity__sum")
    total_hours = hours.get("item__hours__sum")
    context = {
        'cart_items':cart_items,
        'total': total,
        'count': count,
        'total_hours': total_hours
    }
    return render(request, 'main/cart.html', context)

class CartDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CartItems
    success_url = '/cart'

    def test_func(self):
        cart = self.get_object()
        if self.request.user == cart.user:
            return True
        return False

@login_required
def order_item(request):
    cart_items = CartItems.objects.filter(user=request.user,ordered=False)
    ordered_date=timezone.now()
    cart_items.update(ordered=True,ordered_date=ordered_date)
    messages.info(request, "Item Ordered")
    return redirect("main:order_details")

@login_required
def order_details(request):
    items = CartItems.objects.filter(user=request.user, ordered=True,status="Active").order_by('-ordered_date')
    cart_items = CartItems.objects.filter(user=request.user, ordered=True,status="Delivered").order_by('-ordered_date')
    bill = items.aggregate(Sum('item__price'))
    number = items.aggregate(Sum('quantity'))
    hours = items.aggregate(Sum('item__hours'))
    total = bill.get("item__price__sum")
    count = number.get("quantity__sum")
    total_hours = hours.get("item__hours__sum")
    context = {
        'items':items,
        'cart_items':cart_items,
        'total': total,
        'count': count,
        'total_hours': total_hours
    }
    return render(request, 'main/order_details.html', context)

@login_required(login_url='/accounts/login/')
@admin_required
def admin_view(request):
    cart_items = CartItems.objects.filter(item__created_by=request.user, ordered=True,status="Delivered").order_by('-ordered_date')
    context = {
        'cart_items':cart_items,
    }
    return render(request, 'main/admin_view.html', context)

@login_required(login_url='/accounts/login/')
@admin_required
def item_list(request):
    print("request.user")
    items = Item.objects.filter(created_by=request.user)
    context = {
        'items':items
    }
    return render(request, 'main/item_list.html', context)

@login_required
@admin_required
def update_status(request,pk):
    if request.method == 'POST':
        status = request.POST['status']
    cart_items = CartItems.objects.filter(item__created_by=request.user, ordered=True,status="Active",pk=pk)
    delivery_date=timezone.now()
    if status == 'Delivered':
        cart_items.update(status=status, delivery_date=delivery_date)
    return render(request, 'main/pending_orders.html')

@login_required(login_url='/accounts/login/')
@admin_required
def pending_orders(request):
    items = CartItems.objects.filter(item__created_by=request.user, ordered=True,status="Active").order_by('-ordered_date')
    context = {
        'items':items,
    }
    return render(request, 'main/pending_orders.html', context)

@login_required(login_url='/accounts/login/')
@admin_required
def admin_dashboard(request):
    cart_items = CartItems.objects.filter(item__created_by=request.user, ordered=True)
    pending_total = CartItems.objects.filter(item__created_by=request.user, ordered=True,status="Active").count()
    Delivered_total = CartItems.objects.filter(item__created_by=request.user, ordered=True,status="Delivered").count()
    count1 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="1").count()
    count2 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="2").count()
    count3 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="3").count()    
    count4 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="4").count()
    count5 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="5").count()
    count6 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="6").count()
    count7 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="7").count()    
    count8 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="8").count()    
    count9 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="9").count()
    count10 = CartItems.objects.filter(item__created_by=request.user, ordered=True,item="10").count()
    total = CartItems.objects.filter(item__created_by=request.user, ordered=True).aggregate(Sum('item__price'))
    income = total.get("item__price__sum")
    context = {
        'pending_total' : pending_total,
        'Delivered_total' : Delivered_total,
        'income' : income,
        'count1' : count1,
        'count2' : count2,
        'count3' : count3,
        'count4' : count4,
        'count5' : count5,
        'count6' : count6,
        'count7' : count7,
        'count8' : count8,
        'count9' : count9,
        'count10' : count10,

    }
    return render(request, 'main/admin_dashboard.html', context)

def homepage(request):
	return render(request, "main/home.html")

def aboutus(request):
	return render(request, "main/aboutus.html")

@csrf_exempt
def success(request):
    return render(request,"main/success.html")
    
def contact(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			subject = "Website Inquiry" 
			body = {
			'first_name': form.cleaned_data['first_name'], 
			'last_name': form.cleaned_data['last_name'], 
			'email': form.cleaned_data['email_address'], 
			'message':form.cleaned_data['message'], 
			}
			message = "\n".join(body.values())

			try:
				send_mail(subject, message, '190031252@kluniversity.in', ['190031252@kluniversity.in']) 
			except BadHeaderError:
				return HttpResponse('Invalid header found.')
			return redirect ("main:home")
      
	form = ContactForm()
	return render(request, "main/contact.html", {'form':form})

'''def index(request):
    stripe.api.key = settings.STRIPE_PRIVATE_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price' : '',
            'quantity' : 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('thanks')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('index')),
    )

    context = {
        'session_id' : session.id,
        'stripe_public_key' : settings.STRIPE_PUBLIC_KEY
    }
    return render(request, 'index.html')

def thanks(request):
    return render(request, 'thanks.html')'''


def home1(request):
    if request.method == "POST":
        name = request.POST.get('name')
        amount = total.get("item__price__sum")

        client = razorpay.Client(
            auth=("rzp_test_U5GXgLZ1TqzKJ5", "LIdxtlpZkFYPOefoozROPbwr"))

        payment = client.order.create({'amount': amount, 'currency': 'INR',
                                       'payment_capture': '0'})
    return render(request, 'success.html')

    