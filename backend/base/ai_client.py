import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

_THINK_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)


def get_provider():
    """Retorna o provedor de IA ativo ('groq' ou None)."""
    provider = getattr(settings, "IA_PROVIDER", None)
    if provider:
        return provider
    if getattr(settings, "GROQ_API_KEY", None):
        return "groq"
    return None


def _parse_json(resposta):
    """Tenta extrair JSON de uma resposta que pode vir envolta em markdown ou tags de raciocinio."""
    texto = resposta.strip()
    texto = _THINK_RE.sub("", texto).strip()
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
    from openai import BadRequestError

    client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url=getattr(settings, "GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    )
    model = getattr(settings, "GROQ_MODEL", "qwen/qwen3.6-27b")
    messages = [{"role": "user", "content": prompt}]
    # Desativa o raciocinio (modelos qwen3/thinking) para que o modo json_object funcione.
    extra = {"reasoning_effort": "none"}
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=max_tokens,
            extra_body=extra,
        )
        return _parse_json(response.choices[0].message.content)
    except BadRequestError as e:
        # Fallback: modelo pode nao suportar reasoning_effort ou json_object.
        # Refaz sem response_format e limpa possiveis tags <think> na resposta.
        logger.warning("IA: refazendo sem response_format/reasoning: %s", e)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
                max_tokens=max_tokens,
                extra_body=extra,
            )
        except BadRequestError:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
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