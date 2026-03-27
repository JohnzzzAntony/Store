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
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for store logo")
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

    # Promo Ticker
    promo_ticker_badge = models.CharField(max_length=50, blank=True)
    promo_ticker_text = models.CharField(max_length=255, blank=True)
    promo_ticker_url = models.CharField(max_length=255, blank=True)

    # Heritage Section
    heritage_title = models.CharField(max_length=200, blank=True)
    heritage_description = models.TextField(blank=True)
    
    heritage_stat_1_value = models.CharField(max_length=20, blank=True)
    heritage_stat_1_label = models.CharField(max_length=50, blank=True)
    
    heritage_stat_2_value = models.CharField(max_length=20, blank=True)
    heritage_stat_2_label = models.CharField(max_length=50, blank=True)

    # Category Section Customization
    category_section_title = models.CharField(max_length=200, blank=True, default="Shop by Category")
    category_section_subtitle = models.CharField(max_length=500, blank=True)

    # Category Offers Header
    category_offers_title = models.CharField(max_length=200, blank=True, default="Category Offers")
    category_offers_subtitle = models.CharField(max_length=500, blank=True, default="Shop by Deal")

    # BOGO Section Header
    bogo_section_title = models.CharField(max_length=200, blank=True, default="Buy One, Get One Deals")
    bogo_section_subtitle = models.CharField(max_length=500, blank=True, default="Double the luxury without doubling the spend.")
    bogo_section_label = models.CharField(max_length=100, blank=True, default="Best Value")
    
    heritage_stat_3_value = models.CharField(max_length=20, blank=True)
    heritage_stat_3_label = models.CharField(max_length=50, blank=True)
    
    heritage_stat_4_value = models.CharField(max_length=20, blank=True)
    heritage_stat_4_label = models.CharField(max_length=50, blank=True)

    # Footer/Contact
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    contact_address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/s/{self.slug}/"

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.logo and hasattr(self.logo, 'url'):
                return self.logo.url
        except ValueError:
            pass
        return ''


class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else self.email


class Brand(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(null=True, blank=True, upload_to='brands/')
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for brand image")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Brands'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except ValueError:
            pass
        return ''


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(null=True, blank=True, upload_to='categories/')
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for category image")

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except ValueError:
            pass
        return ''


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
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for product image (if no file uploaded)")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    scent_profile = models.CharField(max_length=20, choices=SCENT_CHOICES, default='floral')
    size_ml = models.IntegerField(default=100)
    in_stock = models.BooleanField(default=True)
    top_notes = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Saffron, Rose")
    heart_notes = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Agarwood, Patchouli")
    base_notes = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Amber, Sandalwood")
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
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, RuntimeError):
            pass
        return ''


class Order(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, default='Pending')
    coupon = models.CharField(max_length=50, null=True, blank=True)
    discount = models.FloatField(default=0.0)

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
        # Apply discount
        total = total - self.discount
        return max(0, total)

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
        if self.product:
            total = self.product.price * self.quantity
        else:
            total = 0.0
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
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for blog image")
    author = models.CharField(max_length=100, default='Perfumes')
    published_at = models.DateTimeField(auto_now_add=True)
    reading_time = models.IntegerField(default=5)

    def __str__(self):
        return self.title

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except ValueError:
            pass
        return ''


class ContactMessage(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    subject = models.CharField(max_length=300, blank=True, null=True)
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
        ('collection_hero', 'Products Listing Hero Banner'),
        ('men_collection', 'Men Collection Banner'),
        ('women_collection', 'Women Collection Banner'),
        ('about_hero', 'About Page Hero Banner'),
        ('contact_banner', 'Contact Page Background'),
        ('login_banner', 'Login/Registration Background'),
        ('nav_bg', 'Navigation Sidebar Background'),
        ('heritage_bg', 'Heritage Section Background'),
        ('footer_bg', 'Footer Background'),
    ]
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='media_assets', null=True, blank=True)
    section_name = models.CharField(max_length=50, choices=SECTION_CHOICES)
    image = models.ImageField(upload_to='frontend/', null=True, blank=True)
    image_external_url = models.URLField(max_length=500, null=True, blank=True, help_text="External URL for this section's media")
    label = models.CharField(max_length=100, blank=True, help_text="Small label text (e.g. 'DISCOVER')")
    title = models.CharField(max_length=200, blank=True, help_text="Main heading text")
    subtitle = models.CharField(max_length=500, blank=True, help_text="Optional description or subheading")
    cta_text = models.CharField(max_length=50, blank=True, help_text="Button text")
    cta_url = models.CharField(max_length=500, blank=True, help_text="Button link URL")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Frontend Media Assets'
        unique_together = ['store', 'section_name']

    def save(self, *args, **kwargs):
        if not self.store:
            self.store = Store.objects.filter(is_active=True).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_section_name_display()} ({self.store.name if self.store else 'No Store'})"

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except ValueError:
            pass
        return ''


# ─── PROMOTIONAL BANNERS ─────────────────────────────────────────────────────

class PromoBanner(models.Model):
    """Hero/promo carousel banners configurable from the admin."""
    POSITION_CHOICES = [
        ('top', 'Top Banner (Full Width)'),
        ('mid', 'Mid-Page Banner'),
        ('bottom', 'Bottom Banner'),
    ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='promo_banners', null=True, blank=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    badge_text = models.CharField(max_length=50, blank=True, help_text="E.g. 'NEW', 'HOT DEAL'")
    cta_text = models.CharField(max_length=80, default='Shop Now')
    cta_url = models.CharField(max_length=500, default='/products/', help_text="Link for the CTA button")
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    image_external_url = models.URLField(max_length=500, null=True, blank=True)
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='top')
    bg_color = models.CharField(max_length=7, default='#1E3E3E', help_text="Fallback background hex color")
    text_color = models.CharField(max_length=7, default='#FFFFFF')
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower = first)")
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Promo Banner'
        verbose_name_plural = 'Promo Banners'

    def save(self, *args, **kwargs):
        if not self.store:
            self.store = Store.objects.filter(is_active=True).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.store.name if self.store else 'No Store'})"

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, RuntimeError):
            pass
        return ''





# ─── CATEGORY LEVEL OFFERS ───────────────────────────────────────────────────

class CategoryOffer(models.Model):
    """Per-category promotional banners/offers shown in a special section."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='category_offers', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    discount_label = models.CharField(max_length=60, blank=True, help_text="E.g. 'Up to 25% Off'")
    image = models.ImageField(upload_to='category_offers/', null=True, blank=True)
    image_external_url = models.URLField(max_length=500, null=True, blank=True)
    cta_text = models.CharField(max_length=80, default='Shop Now')
    badge_text = models.CharField(max_length=50, blank=True)
    bg_color = models.CharField(max_length=7, default='#1a3535')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Category Offer'
        verbose_name_plural = 'Category Offers'

    def save(self, *args, **kwargs):
        if not self.store:
            self.store = Store.objects.filter(is_active=True).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.category.name} ({self.store.name if self.store else 'No Store'})"

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, RuntimeError):
            pass
        return ''


# ─── BUY ONE GET ONE OFFERS ──────────────────────────────────────────────────

class BOGOOffer(models.Model):
    """Buy-One-Get-One style offers, optionally linked to specific products."""
    BOGO_TYPE_CHOICES = [
        ('b1g1_free', 'Buy 1 Get 1 Free'),
        ('b2g1', 'Buy 2 Get 1 Free'),
        ('b1g1_half', 'Buy 1 Get 1 at 50% Off'),
        ('b3g1', 'Buy 3 Get 1 Free'),
        ('b2g2', 'Buy 2 Get 2 Free'),
    ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='bogo_offers', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    bogo_type = models.CharField(max_length=20, choices=BOGO_TYPE_CHOICES, default='b1g1_free')
    applicable_products = models.ManyToManyField(Product, blank=True, related_name='bogo_offers',
                                                  help_text="Leave blank to apply to all products")
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='bogo_offers',
                                                    help_text="Leave blank to apply to all categories")
    image = models.ImageField(upload_to='bogo/', null=True, blank=True)
    image_external_url = models.URLField(max_length=500, null=True, blank=True)
    promo_code = models.CharField(max_length=30, blank=True)
    cta_text = models.CharField(max_length=80, default='Shop Now')
    cta_url = models.CharField(max_length=500, default='/products/')
    bg_color = models.CharField(max_length=7, default='#0d2626')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'BOGO Offer'
        verbose_name_plural = 'BOGO Offers'

    def save(self, *args, **kwargs):
        if not self.store:
            self.store = Store.objects.filter(is_active=True).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.get_bogo_type_display()}] ({self.store.name if self.store else 'No Store'})"

    @property
    def imageURL(self):
        if self.image_external_url:
            return self.image_external_url
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, RuntimeError):
            pass
        return ''