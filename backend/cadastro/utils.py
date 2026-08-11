from decimal import Decimal


def calcular_pontuacao_previa(bolsista, criterios):
    criterios = list(criterios)
    pontos_por_criterio = {}
    pontuacao_total = Decimal('0')

    has_graduacao = bolsista.formacoes.filter(tipo='graduacao').exists()
    has_mestrado = bolsista.formacoes.filter(tipo='mestrado').exists()
    has_doutorado = bolsista.formacoes.filter(tipo='doutorado').exists()
    has_pos_doutorado = bolsista.formacoes.filter(tipo='pos_doutorado').exists()

    for criterio in criterios:
        nota = Decimal('0')

        if criterio.tipo_criterio == 'graduacao' and has_graduacao:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'mestrado' and has_mestrado:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'doutorado' and (has_doutorado or has_pos_doutorado):
            nota = criterio.peso

        elif criterio.tipo_criterio == 'projetos_pesquisa':
            anos = Decimal(str(bolsista.participacao_projetos_anos))
            valor_bruto = anos * criterio.peso
            if criterio.peso_maximo > 0:
                nota = min(valor_bruto, criterio.peso_maximo)
            else:
                nota = valor_bruto

        elif criterio.tipo_criterio == 'congressos' and bolsista.participacao_congressos:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'resumo_anais' and bolsista.resumo_anais:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'artigo_completo_anais' and bolsista.artigo_completo_anais:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'artigo_nacional' and bolsista.artigo_cientifico_nacional:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'artigo_internacional' and bolsista.artigo_cientifico_internacional:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'livro_patente' and bolsista.livro_patente:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'minicurso' and bolsista.participacao_minicurso:
            nota = criterio.peso

        elif criterio.tipo_criterio == 'treinamento' and bolsista.treinamento:
            nota = criterio.peso

        if nota:
            pontos_por_criterio[criterio.tipo_criterio] = {
                'nome': criterio.nome,
                'nota': nota,
                'peso': criterio.peso,
                'peso_maximo': criterio.peso_maximo,
            }
            pontuacao_total += nota

    return pontos_por_criterio, pontuacao_total
