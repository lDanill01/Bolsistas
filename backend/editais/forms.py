from django import forms
from django.core.validators import MaxLengthValidator
from django.forms import inlineformset_factory, BaseInlineFormSet
from decimal import Decimal, InvalidOperation
from .models import EditalProvisorio, CronogramaEvento, AplicacaoEdital, NIVEL_BOLSA_CONFIG


class EditalProvisorioForm(forms.ModelForm):
    vigencia_meses = forms.IntegerField(
        label='Vigência (meses)',
        min_value=1,
        max_value=36,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 36,
            'placeholder': 'Ex: 12',
        }),
    )

    class Meta:
        model = EditalProvisorio
        fields = [
            'nome_edital', 'area_estudo', 'detalhes_edital',
            'nome_instituto', 'email_solicitante',
            'documento_anexo',
            'modalidade_bolsa', 'qualificacao_minima', 'detalhes_qualificacao_minima',
            'experiencia',
            'modalidade_atuacao', 'plataforma_tecnologica', 'vigencia',
            'numero_vagas', 'valor_bolsa',
            'endereco_atuacao',
            'modalidade_entrevista', 'conhecimento_desejavel',
            'conteudo_prova_teorica', 'criterios_desempate',
            'comentarios',
            'valor_minimo', 'valor_maximo',
            'status',
        ]
        widgets = {
            'nome_edital':                  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Edital de Inovação Tecnológica 2026'}),
            'area_estudo':                  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Biotecnologia'}),
            'detalhes_edital':              forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 1500, 'placeholder': 'Detalhes adicionais sobre o edital (opcional)'}),
            'nome_instituto':               forms.Select(attrs={'class': 'form-select'}),
            'email_solicitante':            forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'solicitante@instituto.br', 'readonly': True}),
            'documento_anexo':              forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'modalidade_bolsa':             forms.Select(attrs={'class': 'form-select'}),
            'qualificacao_minima':          forms.Select(attrs={'class': 'form-select'}),
            'detalhes_qualificacao_minima': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Engenharia, ...'}),
            'modalidade_atuacao':           forms.Select(attrs={'class': 'form-select'}),
            'plataforma_tecnologica':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Insira a plataforma tecnológica utilizada'}),
            'vigencia':                     forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'max': 1095,'placeholder': 'Ex: 180',}),
            'numero_vagas':                 forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1}),
            'valor_bolsa': forms.Select(attrs={'class': 'form-select'}),
            'endereco_atuacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'maxlength': 1500, 'placeholder': 'Local onde as atividades serão realizadas'}),
            'modalidade_entrevista': forms.Select(attrs={'class': 'form-select'}),
            'conhecimento_desejavel': forms.Textarea(attrs={'class': 'form-control auto-grow', 'rows': 4, 'maxlength': 1500}),
            'conteudo_prova_teorica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 1500}),
            'criterios_desempate': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 1500}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 1500, 'placeholder': 'Comentários diversos (opcional)'}),
            'valor_minimo': forms.HiddenInput(),
            'valor_maximo': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['valor_minimo'].required = False
        self.fields['valor_maximo'].required = False
        self.fields['documento_anexo'].required = False
        self.fields['status'].required = False
        self.fields['vigencia'].required = False
        self.fields['vigencia'].widget = forms.HiddenInput()
        self.fields['conteudo_prova_teorica'].required = False
        self.fields['criterios_desempate'].required = False
        self.fields['experiencia'].required = False
        self.fields['experiencia'].widget.attrs.update({'class': 'form-select'})
        self.fields['modalidade_entrevista'].required = False

        cap_fields = ['detalhes_edital', 'conhecimento_desejavel', 'conteudo_prova_teorica',
                      'criterios_desempate', 'comentarios', 'endereco_atuacao']
        for fname in cap_fields:
            self.fields[fname].validators.append(MaxLengthValidator(1500))

        if self._user:
            if not self.is_bound and not self.initial.get('email_solicitante'):
                self.initial['email_solicitante'] = self._user.email

        if not (self._user and self._user.is_superuser):
            self.fields['status'].disabled = True
            if not self.is_bound and not self.initial.get('status'):
                self.initial['status'] = 'em_analise'

        if not self.is_bound and self.instance and self.instance.pk and self.instance.vigencia:
            self.initial['vigencia_meses'] = max(1, self.instance.vigencia // 30)
        elif not self.is_bound and not self.initial.get('vigencia_meses'):
            self.initial['vigencia_meses'] = 6

        self._update_dynamic_fields()

    def _update_dynamic_fields(self):
        nivel = self.initial.get('modalidade_bolsa') or self.data.get('modalidade_bolsa')
        if not nivel or nivel not in NIVEL_BOLSA_CONFIG:
            self.fields['qualificacao_minima'].choices = [('', '--- Selecione a modalidade primeiro ---')]
            return

        config = NIVEL_BOLSA_CONFIG[nivel]
        self.fields['qualificacao_minima'].choices = [('', '--- Selecione ---')] + config['qualificacao']

        if self.instance and self.instance.pk and self.instance.valor_bolsa is not None:
            val_str = str(self.instance.valor_bolsa)
            val_label = 'R$ {:,.2f}'.format(self.instance.valor_bolsa).replace(',', 'X').replace('.', ',').replace('X', '.')
            widget = self.fields['valor_bolsa'].widget
            widget_choices = list(getattr(widget, '_choices', None) or [])
            existing = {c[0] for c in widget_choices}
            if val_str not in existing:
                widget_choices.append((val_str, val_label))
                widget.choices = widget_choices

    def clean(self):
        cleaned_data = super().clean()

        novo_status = cleaned_data.get('status')

        if novo_status in ('cancelado', 'encerrado'):
            cleaned_data['status'] = novo_status
            if self.instance and self.instance.pk:
                cleaned_data['vigencia'] = getattr(self.instance, 'vigencia', None)
            return cleaned_data

        nivel = cleaned_data.get('modalidade_bolsa')
        config = NIVEL_BOLSA_CONFIG.get(nivel)

        if nivel and config:
            cleaned_data['valor_minimo'] = config.get('valor_minimo', 0)
            cleaned_data['valor_maximo'] = config.get('valor_maximo', 0)

        experiencia = cleaned_data.get('experiencia') or ''
        valor_bolsa_str = cleaned_data.get('valor_bolsa') or ''
        if isinstance(valor_bolsa_str, str) and valor_bolsa_str:
            try:
                cleaned_data['valor_bolsa'] = Decimal(valor_bolsa_str)
            except (ValueError, InvalidOperation):
                self.add_error('valor_bolsa', 'Valor da bolsa inválido.')

        if nivel == 'nivel_1':
            cleaned_data['experiencia'] = 'Sem Experiência'
        elif nivel and experiencia not in dict(self._experiencia_choices_for_nivel(nivel)):
            self.add_error('experiencia', 'Selecione uma experiência válida para o nível escolhido.')

        if nivel and config and cleaned_data.get('valor_bolsa'):
            valor = cleaned_data['valor_bolsa']
            if nivel == 'nivel_1':
                min_v = config.get('valor_minimo', 0)
                max_v = config.get('valor_maximo', 0)
            else:
                exp_valores = config.get('experiencia_valores', {})
                faixa = exp_valores.get(experiencia or 'Sem Experiência', (0, 0))
                min_v, max_v = faixa
            if valor < Decimal(str(min_v)) or valor > Decimal(str(max_v)):
                self.add_error('valor_bolsa', f'Valor da bolsa fora do range permitido: R$ {min_v:.2f} a R$ {max_v:.2f}.')

        modalidade_atuacao = cleaned_data.get('modalidade_atuacao')
        endereco_atuacao = cleaned_data.get('endereco_atuacao')
        if modalidade_atuacao == 'remota' and not endereco_atuacao:
            self.add_error('endereco_atuacao', 'Endereço de atuação é obrigatório para modalidade remota.')

        vigencia_meses = cleaned_data.get('vigencia_meses')
        if vigencia_meses is not None:
            cleaned_data['vigencia'] = vigencia_meses * 30
        elif self.instance and self.instance.pk:
            cleaned_data['vigencia'] = getattr(self.instance, 'vigencia', 180)

        vigencia = cleaned_data.get('vigencia')
        if vigencia is not None:
            try:
                vigencia_int = int(vigencia)
                if vigencia_int < 15:
                    self.add_error('vigencia_meses', 'A vigência mínima é de 15 dias.')
                elif vigencia_int > 1095:
                    self.add_error('vigencia_meses', 'A vigência máxima é de 36 meses (1095 dias).')
            except (ValueError, TypeError):
                if self.instance and self.instance.pk:
                    cleaned_data['vigencia'] = getattr(self.instance, 'vigencia', 180)
                else:
                    cleaned_data['vigencia'] = 180

        if not (self._user and self._user.is_superuser):
            if cleaned_data.get('status') and cleaned_data['status'] != 'em_analise':
                self.add_error('status', 'Apenas superusuários podem alterar o status. O status será mantido como "Em Análise".')
                cleaned_data['status'] = 'em_analise'
            else:
                cleaned_data['status'] = 'em_analise'

        return cleaned_data

    def _experiencia_choices_for_nivel(self, nivel):
        config = NIVEL_BOLSA_CONFIG.get(nivel, {})
        return config.get('experiencia', [('Sem Experiência', 'Sem Experiência')])


class BaseCronogramaFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        datas = []
        tem_outorga_com_data = False
        for idx, form in enumerate(self.forms):
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue
            evento = form.cleaned_data.get('evento')
            data_evento = form.cleaned_data.get('data_evento')
            if evento and data_evento:
                datas.append((idx, data_evento))
                if evento == 'outorga':
                    tem_outorga_com_data = True

        if not tem_outorga_com_data:
            raise forms.ValidationError(
                'Informe o evento "Outorga das bolsas" com a data do evento preenchida '
                'para definir a data final do edital.'
            )

        if len(datas) >= 2:
            for i in range(1, len(datas)):
                if datas[i][1] <= datas[i - 1][1]:
                    raise forms.ValidationError(
                        'As datas dos eventos devem estar estritamente crescentes '
                        '(cada data deve ser maior que a data do evento anterior).'
                    )

    def save(self, commit=True):
        instances = super().save(commit=False)
        ordem = 0
        for obj in instances:
            if not getattr(obj, 'pk', None) or not obj.DELETE:
                ordem += 1
                obj.ordem = ordem
            if commit:
                obj.save()
        return instances


class CronogramaEventoForm(forms.ModelForm):
    data_evento = forms.DateField(
        label='Data do Evento',
        required=True,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control form-control-sm',
            },
            format='%Y-%m-%d',
        ),
    )

    class Meta:
        model = CronogramaEvento
        fields = ['evento', 'data_evento', 'observacao']
        widgets = {
            'evento': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'maxlength': 1500,
                'placeholder': 'Observação (opcional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['evento'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data or cleaned_data.get('DELETE'):
            return cleaned_data
        evento = cleaned_data.get('evento')
        data_evento = cleaned_data.get('data_evento')
        if not evento and data_evento:
            raise forms.ValidationError('Selecione o evento quando a data do evento estiver preenchida.')
        if evento and not data_evento:
            raise forms.ValidationError('Informe a data do evento para o evento selecionado.')
        return cleaned_data


CronogramaEventoFormSet = inlineformset_factory(
    EditalProvisorio,
    CronogramaEvento,
    form=CronogramaEventoForm,
    formset=BaseCronogramaFormSet,
    extra=7,
    can_delete=True,
)


class AvaliacaoIndividualForm(forms.ModelForm):
    nota = forms.DecimalField(
        label='Nota da Prova',
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('10'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 10,
            'step': 0.01,
            'placeholder': '0,00',
        }),
    )
    nota_entrevista = forms.DecimalField(
        label='Nota da Entrevista',
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('10'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 10,
            'step': 0.01,
            'placeholder': '0,00',
        }),
    )
    data_entrevista = forms.DateField(
        label='Data da Entrevista',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )
    status = forms.ChoiceField(
        label='Status Geral',
        choices=AplicacaoEdital.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = AplicacaoEdital
        fields = ['nota', 'nota_entrevista', 'data_entrevista', 'status']
