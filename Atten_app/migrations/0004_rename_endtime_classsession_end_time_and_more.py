# Generated by Django 5.2.2 on 2025-06-14 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Atten_app', '0003_classsession'),
    ]

    operations = [
        migrations.RenameField(
            model_name='classsession',
            old_name='endtime',
            new_name='end_time',
        ),
        migrations.RenameField(
            model_name='classsession',
            old_name='startime',
            new_name='start_time',
        ),
        migrations.RenameField(
            model_name='classsession',
            old_name='totalStu',
            new_name='total_students',
        ),
    ]
