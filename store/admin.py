from django.contrib import admin
from .models import (Store, Customer, Category, Product, Order, OrderItem,
                      ShippingAddress, BlogPost, ContactMessage, Wishlist, FrontendMedia,
                      PromoBanner, OfferSection, CategoryOffer, BOGOOffer)
from .figma_utils import fetch_figma_design_data, create_store_from_figma
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


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'theme_style', 'currency']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'theme_style']
    search_fields = ['name']
    actions = ['sync_figma_design']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-figma/', self.admin_site.admin_view(self.create_from_figma_view), name='create_from_figma'),
        ]
        return custom_urls + urls

    def create_from_figma_view(self, request):
        if request.method == 'POST':
            figma_url = request.POST.get('figma_url')
            access_token = request.POST.get('access_token')
            
            result = create_store_from_figma(figma_url, access_token)
            
            if result['status'] == 'success':
                messages.success(request, result['message'])
                return redirect('admin:store_store_changelist')
            else:
                messages.error(request, f"Activation Failed: {result.get('message')}")
        
        context = dict(
           self.admin_site.each_context(request),
        )
        return render(request, 'admin/store/create_from_figma.html', context)

    @admin.action(description="Sync design details from Figma")
    def sync_figma_design(self, request, queryset):
        for store in queryset:
            result = fetch_figma_design_data(store)
            if result.get("status") == "success":
                self.message_user(request, f"Successfully synced design for {store.name}")
            else:
                self.message_user(request, f"Error syncing {store.name}: {result.get('error') or result.get('message')}", level='ERROR')

    fieldsets = (
        ('Store Essentials', {
            'fields': ('name', 'slug', 'logo', 'details', 'is_active')
        }),
        ('UI/UX Design Management', {
            'fields': ('primary_color', 'secondary_color', 'font_family', 'theme_style', 'custom_css'),
            'description': 'Configure the look and feel of the store.'
        }),
        ('Figma Integration', {
            'fields': ('figma_link', 'figma_access_token', 'figma_last_sync', 'figma_design_data'),
            'classes': ('collapse',),
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
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'store', 'user']
    list_filter = ['store']
    search_fields = ['name', 'email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'store']
    list_filter = ['store']
    prepopulated_fields = {'slug': ('name',)}



class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name'))
    
    store = fields.Field(
        column_name='store',
        attribute='store',
        widget=ForeignKeyWidget(Store, 'name'))

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'store', 'category', 'price', 'in_stock', 'is_featured', 'description', 'gender', 'scent_profile', 'size_ml')
        export_order = fields


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['name', 'store', 'price', 'category', 'in_stock', 'is_featured']
    list_filter = ['store', 'category', 'gender', 'in_stock', 'is_featured']
    list_editable = ['in_stock', 'is_featured', 'price']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Essentials', {
            'fields': ('name', 'slug', 'store', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'in_stock', 'is_featured', 'digital')
        }),
        ('Product Characteristics', {
            'fields': ('gender', 'scent_profile', 'size_ml')
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'get_total']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'store', 'customer', 'complete', 'date_ordered', 'get_cart_total']
    list_filter = ['store', 'complete', 'date_ordered']
    list_editable = ['complete']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Details', {
            'fields': ('store', 'customer', 'complete')
        }),
        ('Status info', {
            'fields': ('transaction_id',)
        }),
    )


# OrderItem is now managed as an inline in OrderAdmin
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ['product', 'order', 'quantity']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'address', 'city', 'country', 'customer']


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'author', 'published_at']
    list_filter = ['store', 'published_at']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    readonly_fields = ['name', 'email', 'message', 'created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product']


@admin.register(FrontendMedia)
class FrontendMediaAdmin(admin.ModelAdmin):
    list_display = ['section_name', 'store', 'is_active', 'title']
    list_filter = ['store', 'section_name', 'is_active']
    search_fields = ['title', 'subtitle']


# ─── PROMOTIONAL BANNERS ADMIN ───────────────────────────────────────────────

@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'position', 'order', 'is_active', 'ends_at']
    list_filter = ['store', 'position', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'subtitle']
    ordering = ['store', 'order']

    fieldsets = (
        ('Banner Content', {
            'fields': ('store', 'title', 'subtitle', 'badge_text')
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


# ─── OFFER SECTIONS ADMIN ────────────────────────────────────────────────────

@admin.register(OfferSection)
class OfferSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'offer_type', 'discount_value', 'promo_code', 'order', 'is_active', 'ends_at']
    list_filter = ['store', 'offer_type', 'is_active']
    list_editable = ['order', 'is_active', 'discount_value']
    search_fields = ['title', 'promo_code']
    ordering = ['store', 'order']

    fieldsets = (
        ('Offer Content', {
            'fields': ('store', 'title', 'description', 'badge_text')
        }),
        ('Offer Details', {
            'fields': ('offer_type', 'discount_value', 'promo_code'),
            'description': 'Set the offer type and discount value.'
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
        ('Media', {
            'fields': ('image', 'image_external_url')
        }),
        ('Display Settings', {
            'fields': ('bg_color', 'order', 'is_active')
        }),
        ('Countdown Timer', {
            'fields': ('ends_at',),
            'description': 'Set an end date/time to show a countdown timer on the frontend.',
            'classes': ('collapse',),
        }),
    )


# ─── CATEGORY OFFER ADMIN ────────────────────────────────────────────────────

@admin.register(CategoryOffer)
class CategoryOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'store', 'discount_label', 'order', 'is_active']
    list_filter = ['store', 'category', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'subtitle', 'discount_label']
    ordering = ['store', 'order']

    fieldsets = (
        ('Offer Content', {
            'fields': ('store', 'category', 'title', 'subtitle', 'discount_label', 'badge_text')
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
class BOGOOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'bogo_type', 'promo_code', 'order', 'is_active']
    list_filter = ['store', 'bogo_type', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description', 'promo_code']
    filter_horizontal = ['applicable_products', 'applicable_categories']
    ordering = ['store', 'order']

    fieldsets = (
        ('BOGO Content', {
            'fields': ('store', 'title', 'description')
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