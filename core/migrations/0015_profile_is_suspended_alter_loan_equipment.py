# Generated by Django 5.1.6 on 2025-04-30 00:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_equipment_current_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_suspended',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='loan',
            name='equipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan', to='core.equipment'),
        ),
    ]
