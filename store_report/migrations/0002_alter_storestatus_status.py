# Generated by Django 5.1.1 on 2024-09-21 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_report', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storestatus',
            name='status',
            field=models.CharField(max_length=20),
        ),
    ]
