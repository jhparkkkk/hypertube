# Generated by Django 5.1.6 on 2025-04-19 17:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField()),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MovieFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField()),
                ('magnet_link', models.TextField()),
                ('file_path', models.CharField(blank=True, max_length=1000, null=True)),
                ('download_status', models.CharField(choices=[('PENDING', 'Pending'), ('DOWNLOADING', 'Downloading'), ('READY', 'Ready'), ('ERROR', 'Error'), ('CONVERTING', 'Converting')], default='PENDING', max_length=20)),
                ('download_progress', models.FloatField(default=0)),
                ('last_watched', models.DateTimeField(blank=True, null=True)),
                ('subtitles_path', models.CharField(blank=True, max_length=1000, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Movie',
        ),
    ]
