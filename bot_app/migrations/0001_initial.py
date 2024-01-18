# Generated by Django 5.0.1 on 2024-01-18 02:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=80)),
                ("password", models.CharField(max_length=20)),
                ("role", models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Theme",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("light_mode", "light_mode"),
                            ("dark_mode", "dark_mode"),
                        ],
                        default="light_mode",
                        max_length=10,
                    ),
                ),
                (
                    "user_id",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="bot_app.user"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SessionDetails",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("session_id", models.CharField(max_length=60)),
                ("login_time", models.DateTimeField()),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="bot_app.user"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ImageQueries",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("question_text", models.CharField(max_length=200)),
                ("image", models.ImageField(upload_to="images/")),
                ("image_response", models.ImageField(upload_to="images/")),
                ("timestamp", models.TimeField(null=True)),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="bot_app.user"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserQueries",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("question_text", models.CharField(max_length=200)),
                ("query_response", models.CharField(max_length=1000)),
                ("timestamp", models.TimeField(null=True)),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="bot_app.user"
                    ),
                ),
            ],
        ),
    ]
