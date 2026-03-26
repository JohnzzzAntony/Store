from django.contrib import admin
from .models import (Store, Customer, Category, Brand, Product, Order, OrderItem,
                      ShippingAddress, BlogPost, ContactMessage, Wishlist, FrontendMedia,
                      PromoBanner, OfferSection, CategoryOffer, BOGOOffer)
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


# @admin.register(Store)
# class StoreAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug', 'is_active', 'theme_style', 'currency']
#     prepopulated_fields = {'slug': ('name',)}
#     list_filter = ['is_active', 'theme_style']
#     search_fields = ['name']
#     actions = ['sync_figma_design']
#     
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('create-from-figma/', self.admin_site.admin_view(self.create_from_figma_view), name='create_from_figma'),
#         ]
#         return custom_urls + urls
# 
#     def create_from_figma_view(self, request):
#         if request.method == 'POST':
#             figma_url = request.POST.get('figma_url')
#             access_token = request.POST.get('access_token')
#             
#             result = create_store_from_figma(figma_url, access_token)
#             
#             if result['status'] == 'success':
#                 messages.success(request, result['message'])
#                 return redirect('admin:store_store_changelist')
#             else:
#                 messages.error(request, f"Activation Failed: {result.get('message')}")
#         
#         context = dict(
#            self.admin_site.each_context(request),
#         )
#         return render(request, 'admin/store/create_from_figma.html', context)
# 
#     @admin.action(description="Sync design details from Figma")
#     def sync_figma_design(self, request, queryset):
#         for store in queryset:
#             result = fetch_figma_design_data(store)
#             if result.get("status") == "success":
#                 self.message_user(request, f"Successfully synced design for {store.name}")
#             else:
#                 self.message_user(request, f"Error syncing {store.name}: {result.get('error') or result.get('message')}", level='ERROR')
# 
#     fieldsets = (
#         ('Store Essentials', {
#             'fields': ('name', 'slug', 'logo', 'image_external_url', 'details', 'is_active')
#         }),
#         ('UI/UX Design Management', {
#             'fields': ('primary_color', 'secondary_color', 'font_family', 'theme_style', 'custom_css'),
#             'description': 'Configure the look and feel of the store.'
#         }),
#         ('Figma Integration', {
#             'fields': ('figma_link', 'figma_access_token', 'figma_last_sync', 'figma_design_data'),
#             'classes': ('collapse',),
#         }),
#         ('General Settings', {
#             'fields': (
#                 'currency', 
#                 'enable_stripe', 
#                 'enable_tabby', 
#                 'enable_tamara', 
#                 'enable_cod'
#             )
#         }),
#     )


@admin.register(Customer)
class CustomerAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'user']
    search_fields = ['name', 'email']


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

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'category', 'price', 'in_stock', 'is_featured', 'image', 'image_external_url', 'description', 'gender', 'scent_profile', 'size_ml')
        import_id_fields = ('name',)  # Match existing records by name if ID is missing
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        # Auto-generate slug if missing in the import row
        if not row.get('slug') and row.get('name'):
            row['slug'] = slugify(row['name'])
        
        # Ensure name is present for matching
        if not row.get('name'):
            # This will likely fail anyway, but we ensure basic data is there
            pass


@admin.register(Product)
class ProductAdmin(SingleStoreMixin, ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ['name', 'brand', 'price', 'category', 'in_stock', 'is_featured']
    list_filter = ['brand', 'category', 'gender', 'in_stock', 'is_featured']
    list_editable = ['in_stock', 'is_featured', 'price']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Essentials', {
            'fields': ('name', 'slug', 'brand', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'in_stock', 'is_featured', 'digital')
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
    list_display = ['section_name', 'is_active', 'title']
    list_filter = ['section_name', 'is_active']
    search_fields = ['title', 'subtitle']
    fields = ('section_name', 'title', 'subtitle', 'image', 'image_external_url', 'is_active')


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


# ─── OFFER SECTIONS ADMIN ────────────────────────────────────────────────────

@admin.register(OfferSection)
class OfferSectionAdmin(SingleStoreMixin, admin.ModelAdmin):
    list_display = ['title', 'offer_type', 'discount_value', 'promo_code', 'order', 'is_active', 'ends_at']
    list_filter = ['offer_type', 'is_active']
    list_editable = ['order', 'is_active', 'discount_value']
    search_fields = ['title', 'promo_code']
    ordering = ['order']

    fieldsets = (
        ('Offer Content', {
            'fields': ('title', 'description', 'badge_text')
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