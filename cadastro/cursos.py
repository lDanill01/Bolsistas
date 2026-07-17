import json
from pathlib import Path

_CURSOS_JSON = Path(__file__).resolve().parent.parent / 'docs' / 'lista_cursos.json'
_INSTITUICOES_DIR = Path(__file__).resolve().parent.parent / 'docs' / 'universidades'

_cache = None
_instituicoes_cache = None


def _carregar():
    global _cache
    if _cache is not None:
        return _cache
    with open(_CURSOS_JSON, encoding='utf-8') as f:
        _cache = json.load(f)
    return _cache


def get_areas():
    dados = _carregar()
    areas = []
    seen = set()
    for item in dados:
        area = item['Area Geral']
        if area not in seen:
            seen.add(area)
            areas.append((area, area))
    areas.sort(key=lambda x: x[0])
    return areas


def get_cursos_por_area():
    dados = _carregar()
    resultado = {}
    for item in dados:
        area = item['Area Geral']
        curso = item['Nome do Curso']
        resultado.setdefault(area, []).append(curso)
    for cursos in resultado.values():
        cursos.sort()
    return resultado


def get_todos_cursos():
    dados = _carregar()
    cursos = []
    seen = set()
    for item in dados:
        curso = item['Nome do Curso']
        if curso not in seen:
            seen.add(curso)
            cursos.append((curso, curso))
    cursos.sort(key=lambda x: x[0])
    return cursos


def get_instituicoes():
    global _instituicoes_cache
    if _instituicoes_cache is not None:
        return _instituicoes_cache

    nomes = []
    seen = set()
    for arq in sorted(_INSTITUICOES_DIR.glob('*.json')):
        with open(arq, encoding='utf-8') as f:
            dados = json.load(f)
        for inst in dados.get('instituicoes', []):
            nome = inst['nome'].strip()
            if nome and nome not in seen:
                seen.add(nome)
                nomes.append(nome)

    nomes.sort()
    _instituicoes_cache = nomes
    return nomes
