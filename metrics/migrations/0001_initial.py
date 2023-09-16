# Generated by Django 4.2.4 on 2023-09-01 12:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active_listing', models.IntegerField(default=0)),
                ('pending_listing', models.IntegerField(default=0)),
                ('settled_listing', models.IntegerField(default=0)),
                ('active_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('pending_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('settled_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('delivery_order', models.IntegerField(default=0)),
                ('meetup_order', models.IntegerField(default=0)),
                ('delivery_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('meetup_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('uk_waste', models.DecimalField(decimal_places=2, default=22220000.0, max_digits=20)),
                ('contribution_ratio', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='UserMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active_listing', models.IntegerField(default=0)),
                ('pending_listing', models.IntegerField(default=0)),
                ('settled_listing', models.IntegerField(default=0)),
                ('active_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('pending_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('settled_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('delivery_order', models.IntegerField(default=0)),
                ('meetup_order', models.IntegerField(default=0)),
                ('delivery_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('meetup_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('contribution_ratio', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CityMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_listing', models.IntegerField(default=0)),
                ('total_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_order', models.IntegerField(default=0)),
                ('delivery_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('meetup_weight', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('contribution_ratio', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('city', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='user.city')),
            ],
        ),
    ]
