# Generated by Django 2.2.6 on 2019-12-19 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0012_auto_20191219_1605'),
    ]

    operations = [
        migrations.RenameField(
            model_name='predictionrace',
            old_name='itra_race_result_id',
            new_name='itra_race_event_id',
        ),
        migrations.AlterField(
            model_name='predictionrace',
            name='itra_race_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
