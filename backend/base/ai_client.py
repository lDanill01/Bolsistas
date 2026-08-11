import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_provider():
    """Retorna o provedor de IA ativo ('groq' ou None)."""
    provider = getattr(settings, "IA_PROVIDER", None)
    if provider:
        return provider
    if getattr(settings, "GROQ_API_KEY", None):
        return "groq"
    return None


def _parse_json(resposta):
    """Tenta extrair JSON de uma resposta que pode vir envolta em markdown."""
    texto = resposta.strip()
    if texto.startswith("```"):
        linhas = texto.splitlines()
        if linhas[0].startswith("```"):
            linhas = linhas[1:]
        if linhas and linhas[-1].startswith("```"):
            linhas = linhas[:-1]
        texto = "\n".join(linhas).strip()
    return json.loads(texto)


def _groq_json(prompt, max_tokens):
    """GROQ expoe uma API compativel com OpenAI: reaproveita o SDK openai com base_url custom."""
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url=getattr(settings, "GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    )
    model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=max_tokens,
    )
    return _parse_json(response.choices[0].message.content)


def gerar_json(prompt, max_tokens):
    """Gera uma resposta em JSON usando o provedor configurado (GROQ)."""
    provider = get_provider()
    if provider == "groq":
        return _groq_json(prompt, max_tokens)
    raise RuntimeError("Nenhum provedor de IA configurado.")