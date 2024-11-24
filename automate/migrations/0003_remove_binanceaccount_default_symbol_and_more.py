# Generated by Django 4.2.10 on 2024-11-23 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automate', '0002_binanceaccount_custom_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='binanceaccount',
            name='default_symbol',
        ),
        migrations.AddField(
            model_name='binanceaccount',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
