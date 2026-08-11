from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0002_numero_serie_data_evento_inscricao'),
    ]

    operations = [
        migrations.AddField(
            model_name='aplicacaoedital',
            name='data_entrevista',
            field=models.DateField(blank=True, null=True, verbose_name='Data da Entrevista'),
        ),
    ]
