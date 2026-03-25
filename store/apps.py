from django.apps import AppConfig


class StoreConfig(AppConfig):
    name = 'store'

    def ready(self):
        import store.signals
        
        # Unregister Groups from admin
        from django.contrib import admin
        from django.contrib.auth.models import Group
        try:
            admin.site.unregister(Group)
        except Exception:
            pass
