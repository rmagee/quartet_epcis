# Generated by Django 2.0 on 2018-10-31 19:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quartet_epcis', '0002_auto_20180718_1528'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['-event_time'], 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
    ]
