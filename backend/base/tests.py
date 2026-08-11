from datetime import date, timedelta
from django.test import TestCase
from .utils import gerar_numero_serie, dias_uteis_entre


class DiasUteisTests(TestCase):
    def test_dias_uteis_semana_completa(self):
        seg = date(2026, 7, 6)
        sex = date(2026, 7, 10)
        self.assertEqual(dias_uteis_entre(seg, sex), 5)

    def test_dias_uteis_com_fim_de_semana(self):
        seg = date(2026, 7, 6)
        dom = date(2026, 7, 12)
        self.assertEqual(dias_uteis_entre(seg, dom), 5)

    def test_dias_uteis_inicio_mesmo_dia(self):
        hoje = date(2026, 7, 10)
        self.assertEqual(dias_uteis_entre(hoje, hoje), 1)

    def test_dias_uteis_inicio_maior_que_fim(self):
        self.assertEqual(dias_uteis_entre(date(2026, 7, 10), date(2026, 7, 6)), 0)

    def test_dias_uteis_inicio_sabado(self):
        sab = date(2026, 7, 11)
        qua = date(2026, 7, 15)
        self.assertEqual(dias_uteis_entre(sab, qua), 3)

    def test_dias_uteis_com_feriados(self):
        seg = date(2026, 7, 6)
        sex = date(2026, 7, 10)
        feriados = ['2026-07-08']
        self.assertEqual(dias_uteis_entre(seg, sex, feriados=feriados), 4)

    def test_dias_uteis_feriado_invalido(self):
        seg = date(2026, 7, 6)
        sex = date(2026, 7, 10)
        feriados = ['invalido', '2026-07-08']
        self.assertEqual(dias_uteis_entre(seg, sex, feriados=feriados), 4)

    def test_dias_uteis_com_multiplos_feriados(self):
        seg = date(2026, 7, 6)
        sex = date(2026, 7, 10)
        feriados = ['2026-07-06', '2026-07-10']
        self.assertEqual(dias_uteis_entre(seg, sex, feriados=feriados), 3)
