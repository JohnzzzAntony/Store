from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Store(models.Model):
    THEME_CHOICES = [
        ('classic', 'Classic Luxury'),
        ('minimal', 'Modern Minimalist'),
        ('bold', 'Bold & Contemporary'),
    ]
    
    FONT_CHOICES = [
        ('serif', 'Classic Serif (Cormorant Garamond)'),
        ('sans', 'Modern Sans-Serif (Inter)'),
        ('playfair', 'Elegant Playfair Display'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(null=True, blank=True, upload_to='logos/')
    details = models.TextField(blank=True)
    
    # UI/UX Design Management
    primary_color = models.CharField(max_length=7, default='#2D5A5A') # Hex code
    secondary_color = models.CharField(max_length=7, default='#1E3E3E') # Hex code
    font_family = models.CharField(max_length=20, choices=FONT_CHOICES, default='serif')
    theme_style = models.CharField(max_length=20, choices=THEME_CHOICES, default='classic')
    custom_css = models.TextField(blank=True, help_text="Custom CSS overrides for this store")
    
    # Settings
    currency = models.CharField(max_length=10, default='AED')
    is_active = models.BooleanField(default=True)
    
    # Payment & Multi-Provider Settings
    enable_stripe = models.BooleanField(default=True)
    enable_tabby = models.BooleanField(default=False)
    enable_tamara = models.BooleanField(default=False)
    enable_cod = models.BooleanField(default=True)
    
    # Figma Integration
    figma_link = models.URLField(max_length=500, blank=True, null=True)
    figma_access_token = models.CharField(max_length=255, blank=True, null=True)
    figma_last_sync = models.DateTimeField(null=True, blank=True)
    figma_design_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/s/{self.slug}/"


class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else self.email


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(null=True, blank=True, upload_to='categories/')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    GENDER_CHOICES = [
        ('M', 'Men'),
        ('W', 'Women'),
        ('U', 'Unisex'),
    ]

    SCENT_CHOICES = [
        ('floral', 'Floral'),
        ('woody', 'Woody'),
        ('oriental', 'Oriental'),
        ('fresh', 'Fresh'),
        ('citrus', 'Citrus'),
        ('musky', 'Musky'),
        ('aquatic', 'Aquatic'),
    ]

    name = models.CharField(max_length=200)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    price = models.FloatField()
    digital = models.BooleanField(default=False, null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to='products/')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    scent_profile = models.CharField(max_length=20, choices=SCENT_CHOICES, default='floral')
    size_ml = models.IntegerField(default=100)
    in_stock = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.store:
            return f"/s/{self.store.slug}/product/{self.id}/"
        return f"/product/{self.id}/"

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url


class Order(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return str(self.id)

    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False)
    zipcode = models.CharField(max_length=200, null=False)
    country = models.CharField(max_length=100, default='UAE')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address


class BlogPost(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to='blog/')
    author = models.CharField(max_length=100, default='Perfumes')
    published_at = models.DateTimeField(auto_now_add=True)
    reading_time = models.IntegerField(default=5)

    def __str__(self):
        return self.title

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url


class ContactMessage(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"


class Wishlist(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        unique_together = [['customer', 'product']]

    def __str__(self):
        return f"Wishlist item: {self.product.name}"


class FrontendMedia(models.Model):
    SECTION_CHOICES = [
        ('hero_slide_1', 'Homepage Hero Slide 1'),
        ('hero_slide_2', 'Homepage Hero Slide 2'),
        ('hero_slide_3', 'Homepage Hero Slide 3'),
        ('men_collection', 'Men Collection Banner'),
        ('women_collection', 'Women Collection Banner'),
        ('about_hero', 'About Page Hero Banner'),
        ('contact_banner', 'Contact Page Background'),
        ('login_banner', 'Login/Registration Background'),
        ('nav_bg', 'Navigation Sidebar Background'),
    ]
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='media_assets')
    section_name = models.CharField(max_length=50, choices=SECTION_CHOICES)
    image = models.ImageField(upload_to='frontend/')
    title = models.CharField(max_length=200, blank=True, help_text="Optional overlay title")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Optional overlay subtitle")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Frontend Media Assets'
        unique_together = ['store', 'section_name']

    def __str__(self):
        return f"{self.get_section_name_display()} ({self.store.name})"