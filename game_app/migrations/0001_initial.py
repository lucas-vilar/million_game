# Generated by Django 4.2 on 2023-07-18 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Jogador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apelido', models.CharField(max_length=25, unique=True)),
                ('pontos', models.CharField(max_length=15)),
                ('nivel', models.IntegerField()),
            ],
            options={
                'db_table': 'apelidos',
            },
        ),
    ]
