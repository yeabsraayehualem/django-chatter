from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='object_id',
            field=models.CharField(max_length=255),
        ),
    ]
