# Generated by Django 4.2.18 on 2025-04-19 19:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_librarianrequests'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowrequest',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_requests', to='core.equipment'),
        ),
    ]
