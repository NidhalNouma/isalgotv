# Generated by Django 4.2.10 on 2024-12-09 20:21

from django.db import migrations
import strategies.models


class Migration(migrations.Migration):

    dependencies = [
        ('strategies', '0013_strategyresults_performance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss_percentage',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss_percentage_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss_percentage_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_loss_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit_percentage',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit_percentage_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit_percentage_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='gross_profit_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='losing_total_trade',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='losing_total_trade_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='losing_total_trade_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='max_drawdown',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='max_drawdown_percentage',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit_percentage',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit_percentage_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit_percentage_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='net_profit_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profit_factor',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profit_factor_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profit_factor_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profitable_percentage',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profitable_percentage_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='profitable_percentage_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='total_trade',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='total_trade_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='total_trade_short',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='winning_total_trade',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='winning_total_trade_long',
        ),
        migrations.RemoveField(
            model_name='strategyresults',
            name='winning_total_trade_short',
        ),
        migrations.AlterField(
            model_name='strategyresults',
            name='performance',
            field=strategies.models.PerferenceJSONField(validators=[strategies.models.performance_validator_json]),
        ),
    ]
