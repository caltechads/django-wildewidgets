from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import migrations

measurement_fixture = 'measurements'
book_manager_fixture = 'book_manager'
user_fixture = 'users'


def load_fixture(apps, schema_editor):
    call_command('loaddata', measurement_fixture, app_label='core')
    call_command('loaddata', user_fixture, app_label='core')
    call_command('loaddata', book_manager_fixture, app_label='core')


def unload_fixture(apps, schema_editor):
    Measurement = apps.get_model("core", "Measurement")
    Measurement.objects.all().delete()
    Publisher = apps.get_model("book_manager", "Publisher")
    Publisher.objects.all().delete()
    Binding = apps.get_model("book_manager", "Binding")
    Binding.objects.all().delete()
    Book = apps.get_model("book_manager", "Book")
    Book.objects.all().delete()
    Author = apps.get_model("book_manager", "Author")
    Author.objects.all().delete()
    Shelf = apps.get_model("book_manager", "Shelf")
    Shelf.objects.all().delete()
    Reading = apps.get_model("book_manager", "Reading")
    Reading.objects.all().delete()
    User = get_user_model()
    User.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture),
    ]