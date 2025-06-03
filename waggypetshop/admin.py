from django.contrib.auth.models import Group, Permission

# Register your models here.

bodeguero_group, created = Group.objects.get_or_create(name='Bodeguero')
contador_group, created = Group.objects.get_or_create(name='Contador')