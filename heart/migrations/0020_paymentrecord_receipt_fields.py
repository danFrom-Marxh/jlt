from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("heart", "0019_newslettersubscriber"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentrecord",
            name="receipt_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="paymentrecord",
            name="receipt_error",
            field=models.TextField(blank=True),
        ),
    ]
