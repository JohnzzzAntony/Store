"""
Management command to seed the database with initial Saleel Parfums data.
Run with: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from store.models import Category, Product, BlogPost
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed the database with initial Saleel Parfums data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Saleel Parfums database...')

        # Clear existing data (optional)
        # Category, Product, BlogPost — keep existing if any

        # ---- Categories ----
        cat_signatures, _ = Category.objects.get_or_create(
            name='Signature Collection', defaults={'slug': 'signature-collection'}
        )
        cat_oud, _ = Category.objects.get_or_create(
            name='Oud & Oriental', defaults={'slug': 'oud-oriental'}
        )
        cat_fresh, _ = Category.objects.get_or_create(
            name='Fresh & Aquatic', defaults={'slug': 'fresh-aquatic'}
        )
        cat_floral, _ = Category.objects.get_or_create(
            name='Floral', defaults={'slug': 'floral'}
        )

        # ---- Products ----
        products_data = [
            {
                'name': 'Swim By The Beach',
                'description': 'A refreshing aquatic fragrance that captures the essence of sun, sea and warm sand. Bright citrus top notes give way to a heart of marine accord and coconut, resting on a base of driftwood and white musk.',
                'price': 165,
                'gender': 'U',
                'scent_profile': 'aquatic',
                'size_ml': 100,
                'category': cat_fresh,
                'is_featured': True,
            },
            {
                'name': 'Aqua Marine',
                'description': 'Deep oceanic notes with a heart of driftwood and white musk. This unisex fragrance evokes the feeling of standing at the bow of a ship, salt breeze in your hair.',
                'price': 195,
                'gender': 'U',
                'scent_profile': 'aquatic',
                'size_ml': 100,
                'category': cat_fresh,
                'is_featured': True,
            },
            {
                'name': 'Solaris',
                'description': 'Warm amber and precious oud with a radiant solar accord. A bold, confident fragrance for those who leave an impression.',
                'price': 285,
                'gender': 'M',
                'scent_profile': 'woody',
                'size_ml': 100,
                'category': cat_oud,
                'is_featured': True,
            },
            {
                'name': 'Rose Noir',
                'description': 'An intoxicating blend of Bulgarian rose and dark patchouli, with a warm base of black vanilla and Tonka bean. Feminine, daring, unforgettable.',
                'price': 245,
                'gender': 'W',
                'scent_profile': 'floral',
                'size_ml': 100,
                'category': cat_floral,
                'is_featured': False,
            },
            {
                'name': 'Oud Royale',
                'description': 'Our most prestigious composition — rich agarwood sourced from the forests of Cambodia, blended with rose absolute and a touch of saffron. A true statement of luxury.',
                'price': 450,
                'gender': 'U',
                'scent_profile': 'oriental',
                'size_ml': 100,
                'category': cat_oud,
                'is_featured': False,
            },
            {
                'name': 'Citrus Garden',
                'description': 'A vibrant burst of Sicilian bergamot and Amalfi lemon, softened with neroli and white tea. Light, fresh and perfect for warm days.',
                'price': 145,
                'gender': 'U',
                'scent_profile': 'citrus',
                'size_ml': 100,
                'category': cat_fresh,
                'is_featured': False,
            },
            {
                'name': 'Amber Musk',
                'description': 'A sensual blend of warm amber, cashmere musk and sandalwood. Subtle and skin-like, this fragrance becomes uniquely yours.',
                'price': 215,
                'gender': 'W',
                'scent_profile': 'musky',
                'size_ml': 100,
                'category': cat_signatures,
                'is_featured': False,
            },
            {
                'name': 'Cedar Storm',
                'description': 'Inspired by the Atlas Mountains after rain — fresh juniper, crisp cedarwood and a touch of violet leaf over a mossy, earthy base.',
                'price': 175,
                'gender': 'M',
                'scent_profile': 'woody',
                'size_ml': 100,
                'category': cat_signatures,
                'is_featured': False,
            },
        ]

        for pd in products_data:
            slug = slugify(pd['name'])
            counter = 1
            orig_slug = slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{orig_slug}-{counter}"
                counter += 1

            product, created = Product.objects.get_or_create(
                name=pd['name'],
                defaults={
                    'description': pd['description'],
                    'price': pd['price'],
                    'gender': pd['gender'],
                    'scent_profile': pd['scent_profile'],
                    'size_ml': pd['size_ml'],
                    'category': pd['category'],
                    'is_featured': pd['is_featured'],
                    'in_stock': True,
                    'digital': False,
                    'slug': slug,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Product created: {product.name}')
            else:
                self.stdout.write(f'  — Product exists: {product.name}')

        # ---- Blog Posts ----
        blogs_data = [
            {
                'title': 'The Art of Layering Fragrances',
                'slug': 'art-of-layering-fragrances',
                'excerpt': 'Discover how to combine two or more perfumes to create a unique, personal scent signature that is entirely your own.',
                'content': '''Fragrance layering is one of the most creative ways to express your personality through scent. Rather than wearing a single perfume, you combine two or more fragrances to create something entirely unique — a signature scent that belongs only to you.

Start with a base fragrance — something warm and deep, like our Amber Musk or Oud Royale. Apply this first, directly on the skin, to your pulse points: wrists, neck, and behind the ears.

Then, layer a lighter, fresher fragrance on top. Our Citrus Garden or Swim By The Beach work beautifully as a second layer. The citrus notes will lift the warmer base, creating an interesting tension between depth and lightness.

The key to successful layering is contrast. Combine a heavy oriental with a light floral, or a musky base with a fresh aquatic top. Experiment freely — there are no rules in perfumery.

At Saleel Parfums, our bottles are designed to encourage exploration. Visit our boutique and speak with our fragrance consultants to discover your perfect combination.''',
                'author': 'Saleel Parfums',
                'reading_time': 5,
            },
            {
                'title': 'Understanding Oud: The Liquid Gold of Perfumery',
                'slug': 'understanding-oud-liquid-gold',
                'excerpt': 'Oud has been treasured for thousands of years. We explore the origins, extraction and magic of this precious ingredient at the heart of Middle Eastern perfumery.',
                'content': '''Oud — also known as agarwood — is perhaps the most revered ingredient in the world of perfumery. It has been burned as incense, extracted for oil, and woven into the cultural fabric of the Arabian Peninsula for over a thousand years.

The oud tree (Aquilaria) produces this precious resin only when under stress, typically from a fungal infection. The infected heartwood slowly transforms into a dark, fragrant substance over decades — sometimes centuries. This rarity is what gives oud its extraordinary value. Pure oud oil can sell for more per gram than gold.

At Saleel Parfums, we source our oud from sustainable agarwood plantations in Cambodia, Vietnam, and Indonesia. We work directly with farmers who practice ethical harvesting, ensuring the longevity of this precious resource.

In our Oud Royale, you will discover oud in its most refined form — blended with our master perfumer's signature rose absolute and a whisper of saffron. The result is a fragrance of extraordinary depth, warmth and character.

Oud is not just an ingredient. It is a journey through history, culture and craft.''',
                'author': 'Saleel Parfums',
                'reading_time': 6,
            },
            {
                'title': 'The Science of Scent Memory',
                'slug': 'science-of-scent-memory',
                'excerpt': 'Why does a fragrance instantly transport you back to a specific moment? We explore the profound connection between smell and memory.',
                'content': '''Of all the human senses, smell is the most powerful trigger of memory and emotion. A single whiff of a familiar fragrance can transport you instantly to a specific place, time, or person — with an emotional immediacy that no photograph or piece of music can match.

This is not mere sentiment. It is neuroscience.

The olfactory nerve connects directly to the limbic system — the part of the brain responsible for emotional processing and long-term memory. Unlike all other senses, which first pass through the thalamus before reaching the limbic system, smell takes a direct route. This direct connection explains why scent triggers memories with such speed, vividness and emotional weight.

At Saleel Parfums, we think deeply about the memories our fragrances might create. When you wear Swim By The Beach and close your eyes, where do you go? Perhaps to a summer holiday, to laughter on warm sand, to freedom.

Choosing a fragrance is choosing what memories you want to make, and what emotions you want to carry with you through the day. Choose thoughtfully. Choose Saleel.''',
                'author': 'Saleel Parfums',
                'reading_time': 4,
            },
        ]

        for bd in blogs_data:
            blog, created = BlogPost.objects.get_or_create(
                slug=bd['slug'],
                defaults=bd
            )
            if created:
                self.stdout.write(f'  ✓ Blog created: {blog.title}')
            else:
                self.stdout.write(f'  — Blog exists: {blog.title}')

        self.stdout.write(self.style.SUCCESS('\n✅ Seed complete! Run the server and visit the admin to add product images.'))
