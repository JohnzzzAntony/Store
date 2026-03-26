from django.contrib import admin
from .models import (Store, Customer, Category, Brand, Product, Order, OrderItem,
                      ShippingAddress, BlogPost, ContactMessage, Wishlist, FrontendMedia,
                      PromoBanner, CategoryOffer, BOGOOffer)
from .core.figma_utils import fetch_figma_design_data, create_store_from_figma
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

# Branding Admin
admin.site.site_header = "Master Ecom Platform"
admin.site.site_title = "Platform Admin"
admin.site.index_title = "Store & Design Management"

class SingleStoreMixin:
    """Ensure all objects are linked to the default store without explicit selection."""
    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'store') and not obj.store:
            obj.store = getattr(request, 'current_store', None) or Store.objects.filter(is_active=True).first()
        super().save_model(request, obj, form, change)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'theme_style', 'currency']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'theme_style']
    search_fields = ['name']
    
    fieldsets = (
        ('Store Essentials', {
            'fields': ('name', 'slug', 'logo', 'image_external_url', 'details', 'is_active')
        }),
        ('Global Content (Ticker)', {
            'fields': ('promo_ticker_badge', 'promo_ticker_text', 'promo_ticker_url'),
            'description': 'Configure the scrolling promo bar at the top.'
        }),
        ('Heritage Section', {
            'fields': (
                'heritage_title', 'heritage_description',
                ('heritage_stat_1_value', 'heritage_stat_1_label'),
                ('heritage_stat_2_value', 'heritage_stat_2_label'),
                ('heritage_stat_3_value', 'heritage_stat_3_label'),
                ('heritage_stat_4_value', 'heritage_stat_4_label'),
            ),
            'description': 'Customize the Brand Heritage section near the bottom of the homepage.'
        }),
        ('Contact Info', {
            'fields': ('contact_email', 'contact_phone', 'contact_address'),
            'description': 'Global contact details for footer and contact page.'
        }),
        ('UI/UX Design Management', {
            'fields': ('primary_color', 'secondary_color', 'font_family', 'theme_style', 'custom_css'),
            'description': 'Configure the look and feel of the store.'
        }),
        ('General Settings', {
            'fields': (
                'currency', 
                'enable_stripe', 
                'enable_tabby', 
                'enable_tamara', 
                'enable_cod'
            )
        }),
    )


@admin.register(Customer)
class CustomerAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['get_user_display', 'name', 'email', 'phone', 'store']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['store']

    def get_user_display(self, obj):
        if obj.user:
            return obj.user.username
        return "Guest User"
    get_user_display.short_description = 'User'



@admin.register(Category)
class CategoryAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'image', 'image_external_url')


@admin.register(Brand)
class BrandAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'image', 'image_external_url', 'description')



from django.utils.text import slugify

class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name'))
    brand = fields.Field(
        column_name='brand',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, 'name'))

    store = fields.Field(
        column_name='store',
        attribute='store',
        widget=ForeignKeyWidget(Store, 'id'))

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'category', 'brand', 'store', 'price', 'in_stock', 'is_featured', 'image', 'image_external_url', 'description', 'gender', 'scent_profile', 'size_ml')
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        # Auto-generate slug if missing
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])
        
        # We don't have store in CSV, so we must add it here or in after_import_instance
        # Let's add a default store if not present
        from .models import Store
        store = Store.objects.filter(is_active=True).first()
        if store:
            row['store'] = store.id
        
        # Ensure name is present for matching
        if not row.get('name'):
            # This will likely fail anyway, but we ensure basic data is there
            pass


@admin.register(Product)
class ProductAdmin(SingleStoreMixin, ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['name', 'brand', 'price', 'category', 'in_stock']
    list_filter = ['brand', 'category', 'gender', 'in_stock']
    list_editable = ['in_stock', 'price']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Essentials', {
            'fields': ('name', 'slug', 'brand', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'in_stock', 'digital')
        }),
        ('Product Characteristics', {
            'fields': ('gender', 'scent_profile', 'size_ml')
        }),
        ('Media', {
            'fields': ('image', 'image_external_url'),
            'description': 'Upload an image file OR enter an external image URL. The external URL takes precedence if provided.'
        }),
        ('Additional Notes', {
            'fields': ('top_notes', 'heart_notes', 'base_notes'),
            'classes': ('collapse',),
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'get_total']

class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0
    can_delete = False
    readonly_fields = ['full_name', 'address', 'city', 'state', 'zipcode', 'country']

@admin.register(Order)
class OrderAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['id', 'display_customer', 'payment_method', 'status', 'complete', 'date_ordered', 'get_cart_total']
    list_filter = ['complete', 'payment_method', 'status', 'date_ordered']
    list_editable = ['status', 'complete']
    search_fields = ['id', 'transaction_id', 'customer__name', 'customer__email']
    inlines = [OrderItemInline, ShippingAddressInline]
    
    fieldsets = (
        ('Order & Customer', {
            'fields': ('customer', 'status', 'complete')
        }),
        ('Payment Infomation', {
            'fields': ('payment_method', 'transaction_id'),
            'description': 'View and manage internal payment IDs and provider methods.'
        }),
    )

    def display_customer(self, obj):
        if obj.customer:
            return f"{obj.customer.name} ({obj.customer.email})"
        return "Guest"
    display_customer.short_description = "Customer"


# OrderItem is now managed as an inline in OrderAdmin
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ['product', 'order', 'quantity']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'address', 'city', 'country', 'customer']


@admin.register(BlogPost)
class BlogPostAdmin(SingleStoreMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']
    fields = ('title', 'slug', 'author', 'excerpt', 'content', 'image', 'image_external_url', 'reading_time')


@admin.register(ContactMessage)
class ContactMessageAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']
    list_display = ['name', 'email', 'phone', 'subject', 'created_at']
    list_filter = ['created_at']
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product']


@admin.register(FrontendMedia)
class FrontendMediaAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['section_name', 'label', 'title', 'subtitle', 'is_active']
    list_filter = ['section_name', 'is_active']
    search_fields = ['section_name', 'title', 'subtitle', 'label']
    fields = ('section_name', 'label', 'title', 'subtitle', 'image', 'image_external_url', 'cta_text', 'cta_url', 'is_active')


# ─── PROMOTIONAL BANNERS ADMIN ───────────────────────────────────────────────

@admin.register(PromoBanner)
class PromoBannerAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['title', 'position', 'order', 'is_active', 'ends_at']
    list_filter = ['position', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'subtitle']
    ordering = ['order']

    fieldsets = (
        ('Banner Content', {
            'fields': ('title', 'subtitle', 'badge_text')
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
        ('Media', {
            'fields': ('image', 'image_external_url'),
            'description': 'Upload a banner image or provide an external URL.'
        }),
        ('Display Settings', {
            'fields': ('position', 'bg_color', 'text_color', 'order', 'is_active')
        }),
        ('Scheduling', {
            'fields': ('starts_at', 'ends_at'),
            'classes': ('collapse',),
        }),
    )





# ─── CATEGORY OFFER ADMIN ────────────────────────────────────────────────────

@admin.register(CategoryOffer)
class CategoryOfferAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['title', 'category', 'discount_label', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'subtitle', 'discount_label']
    ordering = ['order']

    fieldsets = (
        ('Offer Content', {
            'fields': ('category', 'title', 'subtitle', 'discount_label', 'badge_text')
        }),
        ('Call to Action', {
            'fields': ('cta_text',)
        }),
        ('Media', {
            'fields': ('image', 'image_external_url')
        }),
        ('Display Settings', {
            'fields': ('bg_color', 'order', 'is_active', 'ends_at')
        }),
    )


# ─── BOGO OFFER ADMIN ────────────────────────────────────────────────────────

@admin.register(BOGOOffer)
class BOGOOfferAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['title', 'bogo_type', 'promo_code', 'order', 'is_active']
    list_filter = ['bogo_type', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description', 'promo_code']
    filter_horizontal = ['applicable_products', 'applicable_categories']
    ordering = ['order']

    fieldsets = (
        ('BOGO Content', {
            'fields': ('title', 'description')
        }),
        ('Offer Configuration', {
            'fields': ('bogo_type', 'promo_code'),
            'description': 'Select the deal type. Products/categories are optional — leave blank to apply store-wide.'
        }),
        ('Applicable To (Optional)', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',),
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
        ('Media', {
            'fields': ('image', 'image_external_url')
        }),
        ('Display Settings', {
            'fields': ('bg_color', 'order', 'is_active', 'ends_at')
        }),
    )