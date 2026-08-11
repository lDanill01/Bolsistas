# Generated manually - adiciona campo instituicao ao FormacaoAcademica

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='formacaoacademica',
            name='instituicao',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Instituição'),
        ),
    ]
