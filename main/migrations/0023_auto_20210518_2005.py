# Generated by Django 3.1.7 on 2021-05-18 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_auto_20210517_2200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='label_colour',
            field=models.CharField(blank=True, choices=[('danger', 'danger'), ('success', 'success'), ('primary', 'primary'), ('info', 'info'), ('warning', 'warning'), ('default', 'default')], max_length=15),
        ),
    ]
