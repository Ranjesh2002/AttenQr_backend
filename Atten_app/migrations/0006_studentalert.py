# Generated by Django 5.2.2 on 2025-06-22 16:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Atten_app', '0005_student_department_student_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('subject', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('created_at', models.TimeField()),
                ('is_read', models.BooleanField(default=False)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Atten_app.student')),
            ],
        ),
    ]
