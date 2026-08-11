import logging
from decimal import Decimal

from django.conf import settings

from base import ai_client

logger = logging.getLogger(__name__)


def _edital_texto(edital):
    """Monta uma descrição textual detalhada do edital."""
    linhas = [
        f"Nome do Edital: {edital.nome_edital or 'Não informado'}",
        f"Instituto: {edital.get_nome_instituto_display()}",
        f"Área de Estudo: {edital.area_estudo or 'Não informada'}",
        f"Detalhes: {edital.detalhes_edital or 'Não informado'}",
        f"Modalidade da Bolsa: {edital.get_modalidade_bolsa_display()}",
        f"Qualificação Mínima: {edital.qualificacao_minima or 'Não informada'}",
        f"Detalhes da Qualificação Mínima: {edital.detalhes_qualificacao_minima or 'Não informado'}",
        f"Conhecimento Desejável: {edital.conhecimento_desejavel or 'Não informado'}",
        f"Número de Vagas: {edital.numero_vagas}",
        f"Modalidade de Atuação: {edital.get_modalidade_atuacao_display()}",
        f"Plataforma Tecnológica: {edital.plataforma_tecnologica}",
        f"Vigência: {edital.vigencia} dias",
        f"Endereço de Atuação: {edital.endereco_atuacao or 'Não informado'}",
        f"Conteúdo da Prova Teórica: {edital.conteudo_prova_teorica or 'Não informado'}",
        f"Modalidade da Entrevista: {edital.get_modalidade_entrevista_display()}",
        f"Critérios de Desempate: {edital.criterios_desempate or 'Não informado'}",
        f"Status: {edital.get_status_display()}",
    ]

    cronograma = list(edital.cronograma.all())
    if cronograma:
        linhas.append("Cronograma:")
        for e in cronograma:
            linhas.append(f"- {e.get_evento_display()}: {e.data_evento.strftime('%d/%m/%Y')}")

    return "\n".join(linhas)


def _bolsistas_texto(bolsistas):
    """Monta uma descrição textual dos bolsistas cadastrados."""
    if not bolsistas:
        return "Nenhum bolsista cadastrado no momento."

    partes = []
    for b in bolsistas:
        formacoes = list(b.formacoes.all())
        formacao_str = "; ".join(
            f"{f.get_tipo_display()}{f' em {f.curso}' if f.curso else ''}{f' ({f.area})' if f.area else ''}"
            for f in formacoes
        ) or "Não informada"

        linhas = [
            f"Bolsista: {b.user.nome_completo}",
            f"- Formação: {formacao_str}",
            f"- Anos em projetos/pesquisa: {b.participacao_projetos_anos}",
            f"- Congressos/eventos: {'Sim' if b.participacao_congressos else 'Não'}",
            f"- Resumo em anais: {'Sim' if b.resumo_anais else 'Não'}",
            f"- Artigo completo em anais: {'Sim' if b.artigo_completo_anais else 'Não'}",
            f"- Artigo científico nacional: {'Sim' if b.artigo_cientifico_nacional else 'Não'}",
            f"- Artigo científico internacional: {'Sim' if b.artigo_cientifico_internacional else 'Não'}",
            f"- Livro/patente: {'Sim' if b.livro_patente else 'Não'}",
            f"- Minicurso: {'Sim' if b.participacao_minicurso else 'Não'}",
            f"- Treinamento: {'Sim' if b.treinamento else 'Não'}",
        ]
        partes.append("\n".join(linhas))
    return "\n\n".join(partes)


def resumir_edital(edital):
    """Gera um resumo curto e objetivo do edital."""
    descricao = _edital_texto(edital)
    prompt = (
        "Você é um assistente especializado em recursos humanos e bolsas de pesquisa. "
        "Com base no edital abaixo, gere um resumo curto, objetivo e em português do Brasil. "
        "O texto deve ter no máximo 3 linhas e destacar instituto, área, vagas, modalidade e requisitos principais.\n\n"
        f"{descricao}\n\n"
        "Responda APENAS com um objeto JSON no formato: {\"resumo\": \"texto aqui\"}"
    )

    if not ai_client.get_provider():
        return {"resumo": _resumo_fallback(edital)}

    try:
        dados = ai_client.gerar_json(prompt, max_tokens=250)
        return {"resumo": dados.get("resumo", _resumo_fallback(edital))}
    except Exception as e:
        logger.exception("Erro ao gerar resumo de edital com IA: %s", e)
        return {"resumo": _resumo_fallback(edital), "erro": str(e)}


def _resumo_fallback(edital):
    partes = [
        f"Edital {edital.get_nome_instituto_display()} - {edital.get_modalidade_bolsa_display()}",
        f"Área: {edital.area_estudo or 'Não informada'}.",
        f"Vagas: {edital.numero_vagas}.",
        f"Qualificação mínima: {edital.qualificacao_minima or 'Não informada'}.",
    ]
    return " ".join(partes)


def analisar_edital(edital, bolsistas):
    """Gera resumo e análise comparativa do edital frente aos bolsistas, com dados para radar."""
    descricao = _edital_texto(edital)
    bolsistas_texto = _bolsistas_texto(bolsistas)

    prompt = (
        "Você é um assistente especializado em recursos humanos e bolsas de pesquisa. "
        "Analise o edital abaixo e compare-o com os bolsistas cadastrados. "
        "Responda APENAS com um objeto JSON no seguinte formato:\n"
        "{\n"
        '  "resumo": "texto breve e objetivo sobre o edital",\n'
        '  "analise": "texto com a análise do edital frente aos bolsistas disponíveis, destacando compatibilidades e gaps",\n'
        '  "radar": [\n'
        '    {"bolsista": "nome do bolsista 1", "score": 78},\n'
        '    {"bolsista": "nome do bolsista 2", "score": 45}\n'
        '  ]\n'
        "}\n"
        "Regras para o radar:\n"
        "- cada item representa um bolsista cadastrado;\n"
        "- o score deve ser um inteiro de 0 a 100 representando o quanto o perfil do bolsista se aproxima dos requisitos do edital (100 = muito adequado);\n"
        "- se não houver bolsistas, retorne uma lista vazia.\n\n"
        "Edital:\n"
        f"{descricao}\n\n"
        "Bolsistas cadastrados:\n"
        f"{bolsistas_texto}"
    )

    if not ai_client.get_provider():
        return _analise_fallback(edital, bolsistas)

    try:
        dados = ai_client.gerar_json(prompt, max_tokens=1500)
        return {
            "resumo": dados.get("resumo", _resumo_fallback(edital)),
            "analise": dados.get("analise", "Não foi possível gerar a análise comparativa."),
            "radar": _normalizar_radar(dados.get("radar", [])),
        }
    except Exception as e:
        logger.exception("Erro ao analisar edital com IA: %s", e)
        resultado = _analise_fallback(edital, bolsistas)
        resultado["erro"] = str(e)
        return resultado


def _analise_fallback(edital, bolsistas):
    resumo = _resumo_fallback(edital)
    if not bolsistas:
        return {
            "resumo": resumo,
            "analise": "Não há bolsistas cadastrados para comparação no momento.",
            "radar": [],
        }

    radar = []
    for bolsista in bolsistas:
        score = _score_heuristico(bolsista, edital)
        radar.append({"bolsista": bolsista.user.nome_completo, "score": score})

    return {
        "resumo": resumo,
        "analise": (
            "Análise preliminar baseada nos critérios cadastrados. "
            "Verifique o radar para identificar quais bolsistas possuem maior aderência ao edital."
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
        nome = item.get("bolsista") or "Bolsista"
        try:
            score = int(Decimal(str(item.get("score", 0))))
        except Exception:
            score = 0
        score = max(0, min(100, score))
        normalizado.append({"bolsista": nome, "score": score})
    return normalizado
