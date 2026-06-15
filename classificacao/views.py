from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django import forms

from base.mixins import ManagerRequiredMixin, TenantRequiredMixin
from .models import CriterioClassificacao, Classificacao, ClassificacaoCriterio
from editais.models import AplicacaoEdital


class CriterioForm(forms.ModelForm):
    class Meta:
        model = CriterioClassificacao
        fields = ['nome', 'tipo_criterio', 'descricao', 'peso', 'peso_maximo', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_criterio': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peso': forms.NumberInput(attrs={'class': 'form-control'}),
            'peso_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CriterioListView(ManagerRequiredMixin, ListView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_list.html'
    context_object_name = 'criterios'

    def get_queryset(self):
        return CriterioClassificacao.objects.filter(tenant=self.request.tenant)


class CriterioCreateView(ManagerRequiredMixin, CreateView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_form.html'
    form_class = CriterioForm
    success_url = reverse_lazy('criterio_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        messages.success(self.request, 'Critério criado com sucesso!')
        return super().form_valid(form)


class CriterioUpdateView(ManagerRequiredMixin, UpdateView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_form.html'
    form_class = CriterioForm
    success_url = reverse_lazy('criterio_list')

    def get_queryset(self):
        return CriterioClassificacao.objects.filter(tenant=self.request.tenant)

    def form_valid(self, form):
        messages.success(self.request, 'Critério atualizado com sucesso!')
        return super().form_valid(form)


class ClassificacaoForm(forms.ModelForm):
    class Meta:
        model = Classificacao
        fields = ['aplicacao', 'observacoes']
        widgets = {
            'aplicacao': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['aplicacao'].queryset = AplicacaoEdital.objects.filter(
                tenant=tenant, status='em_analise'
            ).select_related('bolsista__user', 'edital')

    def clean(self):
        cleaned = super().clean()
        aplicacao = cleaned.get('aplicacao')
        if aplicacao and Classificacao.objects.filter(aplicacao=aplicacao).exists():
            raise forms.ValidationError('Esta aplicação já possui uma classificação.')
        return cleaned


class ClassificacaoCriterioForm(forms.ModelForm):
    class Meta:
        model = ClassificacaoCriterio
        fields = ['criterio', 'nota']
        widgets = {
            'criterio': forms.Select(attrs={'class': 'form-select'}),
            'nota': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ClassificacaoCreateView(ManagerRequiredMixin, FormView):
    template_name = 'classificacao/classificacao_form.html'
    form_class = ClassificacaoForm
    success_url = reverse_lazy('classificacao_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'criterio_formset' not in kwargs:
            context['criterio_formset'] = self._make_formset()
        return context

    def _make_formset(self, data=None):
        criterios = CriterioClassificacao.objects.filter(
            tenant=self.request.tenant, ativo=True
        )
        initial = [{'criterio': c.pk} for c in criterios]
        return forms.modelformset_factory(
            ClassificacaoCriterio,
            form=ClassificacaoCriterioForm,
            extra=len(criterios),
            max_num=len(criterios),
            can_delete=False,
        )(data or None, prefix='criterio', initial=initial)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        criterio_formset = self._make_formset(request.POST)
        if form.is_valid() and criterio_formset.is_valid():
            return self.form_valid(form, criterio_formset)
        return self.form_invalid(form, criterio_formset)

    def form_valid(self, form, criterio_formset):
        classificacao = Classificacao(
            aplicacao=form.cleaned_data['aplicacao'],
            classificador=self.request.user,
            observacoes=form.cleaned_data.get('observacoes', ''),
            pontuacao_total=0,
            tenant=self.request.tenant,
        )
        pontuacao_total = 0
        classificacao.save()

        for cf in criterio_formset:
            if cf.cleaned_data:
                nota = cf.cleaned_data.get('nota', 0)
                criterio = cf.cleaned_data['criterio']
                pontuacao_total += float(nota) * float(criterio.peso)
                ClassificacaoCriterio.objects.create(
                    classificacao=classificacao,
                    criterio=criterio,
                    nota=nota,
                )

        classificacao.pontuacao_total = pontuacao_total
        classificacao.save()

        messages.success(self.request, 'Classificação registrada com sucesso!')
        return redirect(self.success_url)

    def form_invalid(self, form, criterio_formset):
        return self.render_to_response(self.get_context_data(
            form=form, criterio_formset=criterio_formset
        ))


class ClassificacaoListView(TenantRequiredMixin, ListView):
    model = Classificacao
    template_name = 'classificacao/classificacao_list.html'
    context_object_name = 'classificacoes'
    paginate_by = 10

    def get_queryset(self):
        qs = Classificacao.objects.filter(tenant=self.request.tenant)
        perfil = getattr(self.request.user, 'perfil', None)
        if not perfil or perfil.tipo not in ('ADMIN', 'MANAGER'):
            if hasattr(self.request.user, 'cadastro'):
                qs = qs.filter(aplicacao__bolsista=self.request.user.cadastro)
            else:
                return Classificacao.objects.none()
        return qs.select_related(
            'aplicacao__bolsista__user', 'aplicacao__edital', 'classificador'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = getattr(self.request.user, 'perfil', None)
        context['eh_gestor'] = perfil and perfil.tipo in ('ADMIN', 'MANAGER')
        return context


class ClassificacaoDetailView(TenantRequiredMixin, DetailView):
    model = Classificacao
    template_name = 'classificacao/classificacao_detail.html'
    context_object_name = 'classificacao'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notas'] = self.object.notas.select_related('criterio')
        return context

    def get_queryset(self):
        return Classificacao.objects.filter(tenant=self.request.tenant).select_related(
            'aplicacao__bolsista__user', 'aplicacao__edital', 'classificador'
        )


class CsvImportForm(forms.Form):
    TIPO_CHOICES = [
        ('usuarios', 'Usuários'),
        ('editais', 'Editais'),
    ]
    tipo = forms.ChoiceField(choices=TIPO_CHOICES, label='Tipo', widget=forms.Select(attrs={'class': 'form-select'}))
    arquivo = forms.FileField(label='Arquivo CSV', widget=forms.FileInput(attrs={'class': 'form-control'}))


class CsvImportView(ManagerRequiredMixin, FormView):
    template_name = 'classificacao/csv_import.html'
    form_class = CsvImportForm
    success_url = reverse_lazy('csv_import')

    def form_valid(self, form):
        messages.success(self.request, 'Importação realizada com sucesso!')
        return super().form_valid(form)
