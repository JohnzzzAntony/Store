from django.contrib.auth.models import User
try:
    u = User.objects.get(username='admin')
    u.set_password('Admin123$$')
    u.save()
    print("SUCCESS")
except User.DoesNotExist:
    User.objects.create_superuser('admin', 'admin@example.com', 'Admin123$$')
    print("CREATED")
