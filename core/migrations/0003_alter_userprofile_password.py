# Generated by Django 5.1.6 on 2025-02-10 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='password',
            field=models.CharField(default='Anora2025*', max_length=100),
        ),
    ]
