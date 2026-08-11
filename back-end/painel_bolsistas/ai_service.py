import logging
from decimal import Decimal

from base import ai_client

logger = logging.getLogger(__name__)


def _perfil_texto(bolsista):
    """Monta uma descrição textual resumida do perfil do candidato."""
    user = bolsista.user
    formacoes = list(bolsista.formacoes.order_by("-ano_conclusao"))
    experiencias = list(bolsista.experiencias.all())

    partes = [
        f"Nome: {user.nome_completo}",
        f"E-mail: {user.email}",
    ]

    if bolsista.telefone:
        partes.append(f"Telefone: {bolsista.telefone}")
    if bolsista.cidade or bolsista.estado:
        partes.append(f"Localização: {bolsista.cidade or ''} / {bolsista.get_estado_display() or ''}".strip(" /"))

    if formacoes:
        partes.append("Formação acadêmica:")
        for f in formacoes:
            linha = f"- {f.get_tipo_display()}"
            if f.curso:
                linha += f" em {f.curso}"
            if f.area:
                linha += f" (área: {f.area})"
            if f.ano_conclusao:
                linha += f", conclusão em {f.ano_conclusao}"
            if f.status:
                linha += f" - {f.get_status_display()}"
            partes.append(linha)
    else:
        partes.append("Formação acadêmica: não informada")

    if experiencias:
        partes.append("Experiência profissional:")
        for e in experiencias:
            partes.append(f"- {e.area_atuacao or 'Área não informada'}: {e.anos_experiencia} ano(s)")

    partes.append("Critérios curriculares:")
    partes.append(f"- Anos em projetos/pesquisa: {bolsista.participacao_projetos_anos}")
    partes.append(f"- Participação em congressos/eventos: {'Sim' if bolsista.participacao_congressos else 'Não'}")
    partes.append(f"- Resumo publicado em anais: {'Sim' if bolsista.resumo_anais else 'Não'}")
    partes.append(f"- Artigo completo em anais: {'Sim' if bolsista.artigo_completo_anais else 'Não'}")
    partes.append(f"- Artigo científico/capítulo nacional: {'Sim' if bolsista.artigo_cientifico_nacional else 'Não'}")
    partes.append(f"- Artigo científico/capítulo internacional: {'Sim' if bolsista.artigo_cientifico_internacional else 'Não'}")
    partes.append(f"- Livro/patente: {'Sim' if bolsista.livro_patente else 'Não'}")
    partes.append(f"- Minicurso: {'Sim' if bolsista.participacao_minicurso else 'Não'}")
    partes.append(f"- Treinamento: {'Sim' if bolsista.treinamento else 'Não'}")

    return "\n".join(partes)


def _editais_texto(editais):
    """Monta uma descrição textual dos editais disponíveis."""
    if not editais:
        return "Nenhum edital cadastrado no momento."

    partes = []
    for edital in editais:
        linhas = [
            f"Edital: {edital.nome_edital or edital.nome_instituto}",
            f"- Instituto: {edital.get_nome_instituto_display()}",
            f"- Modalidade: {edital.get_modalidade_bolsa_display()}",
            f"- Área de estudo: {edital.area_estudo or 'Não informada'}",
            f"- Qualificação mínima: {edital.qualificacao_minima or 'Não informada'}",
            f"- Conhecimento desejável: {edital.conhecimento_desejavel or 'Não informado'}",
            f"- Modalidade de atuação: {edital.get_modalidade_atuacao_display()}",
            f"- Vagas: {edital.numero_vagas}",
            f"- Status: {edital.get_status_display()}",
        ]
        partes.append("\n".join(linhas))
    return "\n\n".join(partes)


def resumir_bolsista(bolsista):
    """Gera um resumo curto e objetivo do candidato."""
    perfil = _perfil_texto(bolsista)
    prompt = (
        "Você é um assistente especializado em recursos humanos e bolsas de pesquisa. "
        "Com base no perfil abaixo, gere um resumo curto, objetivo e em português do Brasil "
        "sobre o candidato. O texto deve ter no máximo 3 linhas e destacar formação, "
        "experiência e pontos fortes.\n\n"
        f"{perfil}\n\n"
        "Responda APENAS com um objeto JSON no formato: {\"resumo\": \"texto aqui\"}"
    )

    if not ai_client.get_provider():
        return {"resumo": _resumo_fallback(bolsista)}

    try:
        dados = ai_client.gerar_json(prompt, max_tokens=250)
        return {"resumo": dados.get("resumo", _resumo_fallback(bolsista))}
    except Exception as e:
        logger.exception("Erro ao gerar resumo com IA: %s", e)
        return {"resumo": _resumo_fallback(bolsista), "erro": str(e)}


def _resumo_fallback(bolsista):
    formacao = bolsista.ultima_formacao
    formacao_str = formacao.get_tipo_display() if formacao else "formação não informada"
    experiencia = f"{bolsista.participacao_projetos_anos} ano(s) em projetos/pesquisa"
    publicacoes = []
    if bolsista.artigo_cientifico_internacional:
        publicacoes.append("artigo internacional")
    elif bolsista.artigo_cientifico_nacional:
        publicacoes.append("artigo nacional")
    elif bolsista.artigo_completo_anais:
        publicacoes.append("artigo em anais")
    elif bolsista.resumo_anais:
        publicacoes.append("resumo em anais")
    if bolsista.livro_patente:
        publicacoes.append("livro/patente")

    partes = [
        f"{bolsista.user.nome_completo} possui {formacao_str} e {experiencia}.",
    ]
    if publicacoes:
        partes.append(f"Possui publicações/produções: {', '.join(publicacoes)}.")
    if bolsista.participacao_congressos:
        partes.append("Participou de congressos, feiras ou eventos na área.")
    return " ".join(partes)


def analisar_bolsista(bolsista, editais):
    """Gera resumo e análise comparativa do candidato frente aos editais, com dados para radar."""
    perfil = _perfil_texto(bolsista)
    editais_texto = _editais_texto(editais)

    prompt = (
        "Você é um assistente especializado em recursos humanos e bolsas de pesquisa. "
        "Analise o perfil do candidato abaixo e compare-o com os editais disponíveis. "
        "Responda APENAS com um objeto JSON no seguinte formato:\n"
        "{\n"
        '  "resumo": "texto breve e objetivo sobre o candidato",\n'
        '  "analise": "texto com a análise do perfil frente aos editais, destacando compatibilidades e gaps",\n'
        '  "radar": [\n'
        '    {"edital": "nome do edital 1", "score": 78},\n'
        '    {"edital": "nome do edital 2", "score": 45}\n'
        '  ]\n'
        "}\n"
        "Regras para o radar:\n"
        "- cada item representa um edital disponível;\n"
        "- o score deve ser um inteiro de 0 a 100 representando o quanto o perfil do candidato se aproxima dos requisitos daquele edital (100 = muito adequado);\n"
        "- se não houver editais, retorne uma lista vazia.\n\n"
        "Perfil do candidato:\n"
        f"{perfil}\n\n"
        "Editais disponíveis:\n"
        f"{editais_texto}"
    )

    if not ai_client.get_provider():
        return _analise_fallback(bolsista, editais)

    try:
        dados = ai_client.gerar_json(prompt, max_tokens=1200)
        return {
            "resumo": dados.get("resumo", _resumo_fallback(bolsista)),
            "analise": dados.get("analise", "Não foi possível gerar a análise comparativa."),
            "radar": _normalizar_radar(dados.get("radar", [])),
        }
    except Exception as e:
        logger.exception("Erro ao analisar candidato com IA: %s", e)
        resultado = _analise_fallback(bolsista, editais)
        resultado["erro"] = str(e)
        return resultado


def _analise_fallback(bolsista, editais):
    resumo = _resumo_fallback(bolsista)
    if not editais:
        return {
            "resumo": resumo,
            "analise": "Não há editais cadastrados para comparação no momento.",
            "radar": [],
        }

    radar = []
    for edital in editais:
        score = _score_heuristico(bolsista, edital)
        radar.append({"edital": edital.nome_edital or str(edital), "score": score})

    return {
        "resumo": resumo,
        "analise": (
            "Análise preliminar baseada nos critérios cadastrados. "
            "Verifique o radar para identificar quais editais possuem maior aderência ao perfil do candidato."
        ),
        "radar": radar,
    }


def _score_heuristico(bolsista, edital):
    """Calcula um score simples quando a IA não está disponível."""
    score = 30  # base

    # Pontuação por formação em relação à qualificação mínima
    formacoes = [f.tipo for f in bolsista.formacoes.all()]
    qualificacao = (edital.qualificacao_minima or "").lower()
    if "doutorado" in qualificacao and "doutorado" in formacoes:
        score += 25
    elif "mestrado" in qualificacao and ("mestrado" in formacoes or "doutorado" in formacoes):
        score += 20
    elif "graduação" in qualificacao and ("graduacao" in formacoes or "mestrado" in formacoes or "doutorado" in formacoes):
        score += 15
    elif "técnico" in qualificacao and ("curso_tecnico" in formacoes or "graduacao" in formacoes):
        score += 10

    # Experiência em projetos
    if bolsista.participacao_projetos_anos >= 2:
        score += 15
    elif bolsista.participacao_projetos_anos >= 1:
        score += 10

    # Critérios curriculares
    if bolsista.artigo_cientifico_internacional:
        score += 10
    elif bolsista.artigo_cientifico_nacional:
        score += 8
    elif bolsista.artigo_completo_anais:
        score += 5

    if bolsista.participacao_congressos:
        score += 5
    if bolsista.livro_patente:
        score += 5
    if bolsista.treinamento:
        score += 5
    if bolsista.participacao_minicurso:
        score += 3

    return min(score, 100)


def _normalizar_radar(radar):
    """Garante que o radar tenha a estrutura esperada e scores válidos."""
    if not isinstance(radar, list):
        return []
    normalizado = []
    for item in radar:
        if not isinstance(item, dict):
            continue
        nome = item.get("edital") or "Edital"
        try:
            score = int(Decimal(str(item.get("score", 0))))
        except Exception:
            score = 0
        score = max(0, min(100, score))
        normalizado.append({"edital": nome, "score": score})
    return normalizado
