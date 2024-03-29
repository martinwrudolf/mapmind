# Generated by Django 4.1.7 on 2023-03-30 03:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notebook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('vocab', models.CharField(max_length=200, null=True)),
                ('corpus', models.CharField(max_length=200, null=True)),
                ('kv', models.CharField(max_length=200, null=True)),
                ('kv_vectors', models.CharField(max_length=200, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=200)),
                ('file_type', models.CharField(max_length=200)),
                ('vocab', models.CharField(max_length=200, null=True)),
                ('corpus', models.CharField(max_length=200, null=True)),
                ('notebooks', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='mmapp.notebook')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
