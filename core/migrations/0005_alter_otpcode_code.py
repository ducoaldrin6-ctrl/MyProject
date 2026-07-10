from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_alter_scholar_year_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpcode',
            name='code',
            field=models.CharField(max_length=128),
        ),
    ]
