# Generated by Django 5.1.6 on 2025-04-02 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_passwordresettoken'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PasswordResetToken',
        ),
    ]
