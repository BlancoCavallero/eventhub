# Generated by Django 5.2 on 2025-05-02 18:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_rating_event_alter_rating_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.event'),
        ),
    ]
