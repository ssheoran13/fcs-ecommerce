# Generated by Django 3.0 on 2021-11-11 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_siteadmin'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='image2',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
