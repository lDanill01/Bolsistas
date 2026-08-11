import secrets
from datetime import date, timedelta


def gerar_numero_serie(model, campo='numero_serie', tamanho=4):
    max_val = 10 ** tamanho - 1
    for _ in range(100):
        n = secrets.randbelow(max_val + 1)
        codigo = f'{n:0{tamanho}d}'
        if not model.objects.filter(**{campo: codigo}).exists():
            return codigo
    for i in range(max_val + 1):
        codigo = f'{i:0{tamanho}d}'
        if not model.objects.filter(**{campo: codigo}).exists():
            return codigo
    raise ValueError(
        f'Nao foi possivel gerar numero de serie unico de {tamanho} digitos para {model.__name__}'
    )


def _carregar_feriados():
    from django.conf import settings
    feriados = getattr(settings, 'FERIADOS_NACIONAIS', [])
    feriados_set = set()
    for f_str in feriados:
        try:
            partes = f_str.split('-')
            feriados_set.add(date(int(partes[0]), int(partes[1]), int(partes[2])))
        except (ValueError, IndexError):
            pass
    return feriados_set


def dias_uteis_entre(inicio, fim, feriados=None):
    if inicio > fim:
        return 0
    if feriados is None:
        feriados_set = _carregar_feriados()
    else:
        feriados_set = set(feriados)
    dias = 0
    atual = inicio
    while atual <= fim:
        if atual.weekday() < 5 and atual not in feriados_set:
            dias += 1
        atual += timedelta(days=1)
    return dias


def adicionar_dias_uteis(data_inicial, dias, feriados=None):
    if dias <= 0:
        return data_inicial
    if feriados is None:
        feriados_set = _carregar_feriados()
    else:
        feriados_set = set(feriados)
    atual = data_inicial + timedelta(days=1)
    contador = 0
    while contador < dias:
        if atual.weekday() < 5 and atual not in feriados_set:
            contador += 1
            if contador == dias:
                return atual
        atual += timedelta(days=1)
    return atual


def proximo_dia_util(data, feriados=None):
    if feriados is None:
        feriados_set = _carregar_feriados()
    else:
        feriados_set = set(feriados)
    while data.weekday() >= 5 or data in feriados_set:
        data += timedelta(days=1)
    return data


def proximo_dia_1_ou_15(data, feriados=None):
    if feriados is None:
        feriados_set = _carregar_feriados()
    else:
        feriados_set = set(feriados)
    ano = data.year
    mes = data.month
    try:
        dia_15 = date(ano, mes, 15)
        if dia_15 >= data:
            return proximo_dia_util(dia_15, feriados)
    except ValueError:
        pass
    if mes == 12:
        mes = 1
        ano += 1
    else:
        mes += 1
    dia_1 = date(ano, mes, 1)
    return proximo_dia_util(dia_1, feriados)
