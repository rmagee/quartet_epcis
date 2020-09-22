# Generated by Django 3.0.8 on 2020-09-02 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quartet_epcis', '0004_auto_20190812_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='entryevent',
            name='task_name',
            field=models.CharField(blank=True, help_text='The name of the Task that parsed this Entry and Event.', max_length=150, null=True, verbose_name='Task Name'),
        ),
        migrations.AlterField(
            model_name='documentidentification',
            name='multiple_type',
            field=models.BooleanField(default=False, help_text='A flag to indicate that there is more than one type of Document in the instance.', null=True, verbose_name='Multiple Type'),
        ),
    ]