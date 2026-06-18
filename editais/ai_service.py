import json
import logging
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

logger = logging.getLogger(__name__)


class SummarizeState(TypedDict):
    edital_data: str
    summary: Optional[str]
    error: Optional[str]


def _build_edital_context(edital) -> str:
    cronograma = edital.cronograma.all()
    distribuicoes = edital.distribuicoes.all()

    ctx = f"""
DADOS DO EDITAL

Nome: {edital.nome_edital}
Area de Estudo: {edital.area_estudo}
Detalhes: {edital.detalhes_edital or 'Nao informado'}

INSTITUTO
Nome: {edital.get_nome_instituto_display()}
E-mail: {edital.email_solicitante}
Telefone: {edital.telefone}
Endereco: {edital.endereco}

BOLSA
Modalidade: {edital.get_modalidade_bolsa_display()}
Valor Total: R$ {float(edital.valor_total_bolsa):,.2f}
Valor da Bolsa: R$ {float(edital.valor_bolsa):,.2f}
Modalidade de Atuacao: {edital.get_modalidade_atuacao_display()}
Plataforma Tecnologica: {edital.plataforma_tecnologica}
Vigencia: {edital.vigencia} dias
Endereco de Atuacao: {edital.endereco_atuacao or 'Nao informado'}
Numero de Vagas: {edital.numero_vagas}
"""

    if distribuicoes:
        ctx += "\nDISTRIBUICAO DE BOLSISTAS\n"
        for d in distribuicoes:
            ctx += f"- {d.quantidade}x {d.experiencia}: R$ {float(d.valor_unitario):,.2f} cada (subtotal: R$ {float(d.subtotal):,.2f})\n"
        ctx += f"Total Distribuido: R$ {float(edital.total_distribuido):,.2f}\n"

    ctx += f"""
REQUISITOS
Qualificacao Minima: {edital.qualificacao_minima}
Qualificacao Minima em: {edital.detalhes_qualificacao_minima or 'Nao informado'}
Conhecimento Desejavel: {edital.conhecimento_desejavel or 'Nao informado'}

AVALIACAO
Conteudo da Prova Teorica: {edital.conteudo_prova_teorica}
Entrevista: {edital.entrevista}
Criterios de Desempate: {edital.criterios_desempate}
"""

    if cronograma:
        ctx += "\nCRONOGRAMA\n"
        for e in cronograma:
            ctx += f"- {e.get_evento_display()}: {e.data_referencia}"
            if e.observacao:
                ctx += f" ({e.observacao})"
            ctx += "\n"

    ctx += f"\nSTATUS: {edital.get_status_display()}\n"
    return ctx


SYSTEM_PROMPT = """Voce e um assistente que resume editais de bolsas de pesquisa do SENAI.
Seu resumo deve ser PRECISO, DIRETO e OBJETIVO.
Nao invente dados que nao estejam no edital.
Estruture o resumo em topicos curtos, um por linha.
Responda apenas em portugues brasileiro.

Formato obrigatorio:

**Resumo do Edital**

**Objetivo:** 1-2 linhas sobre o que e o edital
**Bolsa:** valor e modalidade
**Requisitos:** qualificacao minima
**Vagas:** quantidade e distribuicao (se houver)
**Etapas:** principais eventos do cronograma
**Instituto:** nome e contato
**Vigencia:** prazo da bolsa"""


def summarize_edital(edital) -> dict:
    ctx = _build_edital_context(edital)

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        max_tokens=600,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Resuma o seguinte edital de forma precisa e objetiva:\n\n{ctx}"),
    ]

    try:
        response = llm.invoke(messages)
        return {"summary": response.content, "error": None}
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        return {"summary": None, "error": str(e)}


def build_summarize_graph():
    workflow = StateGraph(SummarizeState)

    def summarize_node(state: SummarizeState) -> SummarizeState:
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.3,
            max_tokens=600,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Resuma o seguinte edital de forma precisa e objetiva:\n\n{state['edital_data']}"),
        ]
        try:
            response = llm.invoke(messages)
            state["summary"] = response.content
        except Exception as e:
            state["error"] = str(e)
        return state

    workflow.add_node("summarize", summarize_node)
    workflow.set_entry_point("summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()
