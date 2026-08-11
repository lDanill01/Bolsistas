from django.db import migrations, models


def gerar_numero_serie(apps, _schema_editor):
    import secrets
    EditalProvisorio = apps.get_model('editais', 'EditalProvisorio')
    CadastroBolsista = apps.get_model('cadastro', 'CadastroBolsista')
    AplicacaoEdital = apps.get_model('editais', 'AplicacaoEdital')

    existentes = set(EditalProvisorio.objects.values_list('numero_serie', flat=True))
    for edital in EditalProvisorio.objects.filter(numero_serie=''):
        for _ in range(100):
            n = secrets.randbelow(10000)
            codigo = f'{n:04d}'
            if codigo not in existentes:
                edital.numero_serie = codigo
                edital.save(update_fields=['numero_serie'])
                existentes.add(codigo)
                break

    existentes_cad = set(CadastroBolsista.objects.values_list('numero_serie', flat=True))
    for bolsista in CadastroBolsista.objects.filter(numero_serie=''):
        for _ in range(100):
            n = secrets.randbelow(10000)
            codigo = f'{n:04d}'
            if codigo not in existentes_cad:
                bolsista.numero_serie = codigo
                bolsista.save(update_fields=['numero_serie'])
                existentes_cad.add(codigo)
                break

    for aplicacao in AplicacaoEdital.objects.filter(numero_inscricao=''):
        if aplicacao.bolsista.numero_serie and aplicacao.edital.numero_serie:
            aplicacao.numero_inscricao = (
                f'{aplicacao.bolsista.numero_serie}-{aplicacao.edital.numero_serie}'
            )
            aplicacao.save(update_fields=['numero_inscricao'])


class Migration(migrations.Migration):

    dependencies = [
        ('editais', '0001_initial'),
        ('cadastro', '0002_formacaoacademica_instituicao'),
    ]

    operations = [
        migrations.AddField(
            model_name='editalprovisorio',
            name='numero_serie',
            field=models.CharField(blank=True, max_length=4, unique=True, verbose_name='Número de Série'),
        ),
        migrations.AddField(
            model_name='cronogramaevento',
            name='data_evento',
            field=models.DateField(blank=True, null=True, verbose_name='Data do Evento'),
        ),
        migrations.AddField(
            model_name='aplicacaoedital',
            name='numero_inscricao',
            field=models.CharField(blank=True, max_length=10, unique=True, verbose_name='Número de Inscrição'),
        ),
        migrations.RunPython(gerar_numero_serie, migrations.RunPython.noop),
    ]
