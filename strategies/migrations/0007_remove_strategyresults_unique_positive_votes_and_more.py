# Generated by Django 4.2.2 on 2023-08-17 23:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('strategies', '0006_remove_strategyresults_votes_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='strategyresults',
            name='unique_positive_votes',
        ),
        migrations.RemoveConstraint(
            model_name='strategyresults',
            name='unique_negative_votes',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='votes',
        ),
    ]
