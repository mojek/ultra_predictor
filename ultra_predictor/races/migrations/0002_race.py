# Generated by Django 2.2.6 on 2019-10-17 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Race',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('start_date', models.DateField()),
                ('distance', models.DecimalField(decimal_places=2, max_digits=6)),
                ('elevation_gain', models.PositiveIntegerField()),
                ('elevation_lost', models.PositiveIntegerField()),
                ('itra', models.PositiveIntegerField()),
                ('itra_race_id', models.PositiveIntegerField()),
                ('food_point', models.PositiveIntegerField()),
                ('time_limit', models.DecimalField(decimal_places=1, max_digits=10)),
                ('race_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='races', to='races.RaceGroup')),
            ],
        ),
    ]
