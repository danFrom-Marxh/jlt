from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('heart', '0017_contact_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_session_id', models.CharField(max_length=255, unique=True)),
                ('cart_id', models.PositiveIntegerField(blank=True, null=True)),
                ('amount_total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('currency', models.CharField(default='EUR', max_length=8)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('paid', 'Payé'), ('failed', 'Échoué'), ('refunded', 'Remboursé')], default='pending', max_length=20)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('inventory_applied', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SaleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.UUIDField()),
                ('product_name', models.CharField(max_length=200)),
                ('variant_id', models.PositiveIntegerField(blank=True, null=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='heart.paymentrecord')),
            ],
        ),
    ]
