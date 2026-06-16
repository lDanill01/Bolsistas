from django import forms
from django.forms import inlineformset_factory
from .models import EditalProvisorio, CronogramaEvento


class EditalProvisorioForm(forms.ModelForm):
    class Meta:
        model = EditalProvisorio
        fields = [
            'nome_instituto', 'email_solicitante', 'telefone', 'endereco',
            'numero_vagas', 'modalidade_bolsa', 'plataforma_tecnologica',
            'vigencia', 'endereco_atuacao',
            'qualificacao_minima', 'experiencia_minima', 'conhecimento_desejavel',
            'conteudo_prova_teorica', 'entrevista', 'criterios_desempate',
            'status',
        ]
        widgets = {
            'nome_instituto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do instituto'}),
            'email_solicitante': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'solicitante@instituto.br'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(67) 99999-9999'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rua, número, bairro, cidade - UF'}),
            'numero_vagas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'modalidade_bolsa': forms.Select(attrs={'class': 'form-select'}),
            'plataforma_tecnologica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Python, Django, React'}),
            'vigencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: De 01/07/2026 a 30/06/2027'}),
            'endereco_atuacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Local onde as atividades serão realizadas'}),
            'qualificacao_minima': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experiencia_minima': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conhecimento_desejavel': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conteudo_prova_teorica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'entrevista': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'criterios_desempate': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CronogramaEventoForm(forms.ModelForm):
    class Meta:
        model = CronogramaEvento
        fields = ['evento', 'data_referencia', 'observacao', 'ordem']
        widgets = {
            'evento': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'data_referencia': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ex: A partir da data de publicação deste edital',
            }),
            'observacao': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Observação (opcional)',
            }),
            'ordem': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
        }


CronogramaEventoFormSet = inlineformset_factory(
    EditalProvisorio,
    CronogramaEvento,
    form=CronogramaEventoForm,
    extra=1,
    can_delete=True,
)
