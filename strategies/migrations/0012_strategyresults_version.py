# Generated by Django 4.2.10 on 2024-11-14 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategies', '0011_alter_strategy_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategyresults',
            name='version',
            field=models.CharField(default='1.0', max_length=10),
        ),
    ]
