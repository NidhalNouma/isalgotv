# Generated by Django 4.2.10 on 2025-02-15 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automate', '0015_alter_tradedetails_custom_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tradedetails',
            name='custom_id',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='tradedetails',
            name='order_id',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='tradedetails',
            name='symbol',
            field=models.CharField(max_length=30),
        ),
    ]
