from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cadastro', '0004_alter_cadastrobolsista_curriculo')]

    operations = [
        migrations.AddField(
            model_name='experienciaprofissional',
            name='cargo',
            field=models.CharField(default='', max_length=255, verbose_name='Cargo'),
        ),
    ]
