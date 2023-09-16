# Generated by Django 4.2.4 on 2023-09-01 12:24

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('listing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogisticsOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ShippingFeeWeight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=6)),
                ('logistics_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.logisticsoption')),
            ],
            options={
                'ordering': ['logistics_option', 'fee', 'weight'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('completed_date', models.DateTimeField(blank=True, null=True)),
                ('buyer_confirmed', models.BooleanField(default=False)),
                ('seller_confirmed', models.BooleanField(default=False)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_orders', to=settings.AUTH_USER_MODEL)),
                ('listing', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='listing.listing')),
                ('logistics_option', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.logisticsoption')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_orders', to=settings.AUTH_USER_MODEL)),
                ('shipping_fee_weight', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.shippingfeeweight')),
            ],
        ),
    ]