from django.db import migrations, models


def gerar_serie_bolsistas(apps, _schema_editor):
    import secrets
    CadastroBolsista = apps.get_model('cadastro', 'CadastroBolsista')
    existentes = set(CadastroBolsista.objects.values_list('numero_serie', flat=True))
    for bolsista in CadastroBolsista.objects.filter(numero_serie=''):
        for _ in range(100):
            n = secrets.randbelow(10000)
            codigo = f'{n:04d}'
            if codigo not in existentes:
                bolsista.numero_serie = codigo
                bolsista.save(update_fields=['numero_serie'])
                existentes.add(codigo)
                break


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0002_formacaoacademica_instituicao'),
    ]

    operations = [
        migrations.AddField(
            model_name='cadastrobolsista',
            name='numero_serie',
            field=models.CharField(blank=True, max_length=4, unique=True, verbose_name='Número de Série'),
        ),
        migrations.RunPython(gerar_serie_bolsistas, migrations.RunPython.noop),
    ]
