from django.views.generic import CreateView, DetailView, UpdateView, ListView, TemplateView, FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django import forms

from base.mixins import TenantRequiredMixin, ManagerRequiredMixin
from .models import CadastroBolsista, CursoSuperior, PosGraduacao, SolicitacaoEdicao
from accounts.models import User, Perfil
from .utils import calcular_pontuacao_previa
from classificacao.models import CriterioClassificacao


class CursoSuperiorForm(forms.ModelForm):
    class Meta:
        model = CursoSuperior
        fields = ['instituicao', 'curso', 'grau', 'ano_conclusao']


class PosGraduacaoForm(forms.ModelForm):
    class Meta:
        model = PosGraduacao
        fields = ['tipo', 'instituicao', 'area', 'ano_conclusao']


class CadastroForm(forms.ModelForm):
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CadastroBolsista
        fields = [
            'data_nascimento', 'endereco',
            'participacao_projetos_anos',
            'participacao_congressos', 'resumo_anais', 'artigo_completo_anais',
            'artigo_cientifico_nacional', 'artigo_cientifico_internacional',
            'livro_patente', 'participacao_minicurso', 'treinamento',
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'participacao_projetos_anos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'participacao_congressos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resumo_anais': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'artigo_completo_anais': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'artigo_cientifico_nacional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'artigo_cientifico_internacional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'livro_patente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'participacao_minicurso': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'treinamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.fields['telefone'].initial = self.instance.user.perfil.telefone
            except (AttributeError, Perfil.DoesNotExist):
                pass


class CadastroCreateView(TenantRequiredMixin, FormView):
    template_name = 'cadastro/cadastro_form.html'
    form_class = CadastroForm
    success_url = reverse_lazy('cadastro_detail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = None
        if 'curso_formset' not in kwargs:
            context['curso_formset'] = self._make_curso_formset()
        if 'pos_formset' not in kwargs:
            context['pos_formset'] = self._make_pos_formset()
        return context

    def _make_curso_formset(self, data=None):
        return self._formset_factory(CursoSuperiorForm, 'cursos', data)

    def _make_pos_formset(self, data=None):
        return self._formset_factory(PosGraduacaoForm, 'pos', data)

    def _formset_factory(self, form_class, prefix, data=None):
        return forms.modelformset_factory(
            CursoSuperior if 'curso' in prefix else PosGraduacao,
            form=form_class,
            extra=1,
            can_delete=True,
        )(data or None, prefix=prefix, queryset=CursoSuperior.objects.none() if 'curso' in prefix else PosGraduacao.objects.none())

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        curso_formset = self._make_curso_formset(request.POST)
        pos_formset = self._make_pos_formset(request.POST)
        if form.is_valid() and curso_formset.is_valid() and pos_formset.is_valid():
            return self.form_valid(form, curso_formset, pos_formset)
        return self.form_invalid(form, curso_formset, pos_formset)

    def form_valid(self, form, curso_formset, pos_formset):
        cadastro = form.save(commit=False)
        cadastro.user = self.request.user
        cadastro.tenant = self.request.tenant
        cadastro.save()
        telefone = form.cleaned_data.get('telefone')
        if telefone is not None:
            try:
                perfil = self.request.user.perfil
                perfil.telefone = telefone
                perfil.save()
            except Perfil.DoesNotExist:
                pass
        for cf in curso_formset:
            if cf.cleaned_data and not cf.cleaned_data.get('DELETE'):
                curso = cf.save(commit=False)
                curso.bolsista = cadastro
                curso.tenant = self.request.tenant
                curso.save()
        for pf in pos_formset:
            if pf.cleaned_data and not pf.cleaned_data.get('DELETE'):
                pos = pf.save(commit=False)
                pos.bolsista = cadastro
                pos.tenant = self.request.tenant
                pos.save()
        criterios = CriterioClassificacao.objects.filter(tenant=self.request.tenant, ativo=True)
        _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
        cadastro.pontuacao_previa = pontuacao
        cadastro.save(update_fields=['pontuacao_previa'])
        messages.success(self.request, 'Cadastro criado com sucesso!')
        return redirect(self.success_url)

    def form_invalid(self, form, curso_formset, pos_formset):
        return self.render_to_response(self.get_context_data(
            form=form, curso_formset=curso_formset, pos_formset=pos_formset
        ))

    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'cadastro'):
            return redirect('cadastro_detail')
        return super().get(request, *args, **kwargs)


class CadastroDetailView(TenantRequiredMixin, DetailView):
    model = CadastroBolsista
    template_name = 'cadastro/cadastro_detail.html'
    context_object_name = 'cadastro'

    def get(self, request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.tipo in ('ADMIN', 'MANAGER'):
            pk = kwargs.get('pk')
            if pk:
                return super().get(request, *args, **kwargs)
        if not hasattr(request.user, 'cadastro'):
            return redirect('cadastro_create')
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.tipo in ('ADMIN', 'MANAGER'):
            pk = self.kwargs.get('pk')
            if pk:
                return get_object_or_404(CadastroBolsista, pk=pk, tenant=self.request.tenant)
        return get_object_or_404(CadastroBolsista, user=self.request.user, tenant=self.request.tenant)


class CadastroUpdateView(ManagerRequiredMixin, FormView):
    template_name = 'cadastro/cadastro_form.html'

    def get_object(self):
        return get_object_or_404(
            CadastroBolsista, pk=self.kwargs['pk'], tenant=self.request.tenant
        )

    def get_form_class(self):
        return CadastroForm

    def get_form(self, form_class=None):
        return CadastroForm(instance=self.get_object(), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object()
        cadastro = self.get_object()
        if 'curso_formset' not in kwargs:
            context['curso_formset'] = forms.modelformset_factory(
                CursoSuperior, form=CursoSuperiorForm, extra=1, can_delete=True
            )(prefix='cursos', queryset=cadastro.cursos_superiores.all())
        if 'pos_formset' not in kwargs:
            context['pos_formset'] = forms.modelformset_factory(
                PosGraduacao, form=PosGraduacaoForm, extra=1, can_delete=True
            )(prefix='pos', queryset=cadastro.pos_graduacoes.all())
        return context

    def post(self, request, *args, **kwargs):
        cadastro = self.get_object()
        form = CadastroForm(request.POST, request.FILES, instance=cadastro)
        curso_formset = forms.modelformset_factory(
            CursoSuperior, form=CursoSuperiorForm, extra=1, can_delete=True
        )(request.POST, prefix='cursos', queryset=cadastro.cursos_superiores.all())
        pos_formset = forms.modelformset_factory(
            PosGraduacao, form=PosGraduacaoForm, extra=1, can_delete=True
        )(request.POST, prefix='pos', queryset=cadastro.pos_graduacoes.all())
        if form.is_valid() and curso_formset.is_valid() and pos_formset.is_valid():
            cadastro = form.save()
            telefone = form.cleaned_data.get('telefone')
            if telefone is not None:
                try:
                    perfil = cadastro.user.perfil
                    perfil.telefone = telefone
                    perfil.save()
                except Perfil.DoesNotExist:
                    pass
            for cf in curso_formset:
                if cf.cleaned_data and cf not in curso_formset.deleted_forms:
                    curso = cf.save(commit=False)
                    curso.bolsista = cadastro
                    curso.tenant = self.request.tenant
                    curso.save()
            for pf in pos_formset:
                if pf.cleaned_data and pf not in pos_formset.deleted_forms:
                    pos = pf.save(commit=False)
                    pos.bolsista = cadastro
                    pos.tenant = self.request.tenant
                    pos.save()
            criterios = CriterioClassificacao.objects.filter(tenant=self.request.tenant, ativo=True)
            _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
            cadastro.pontuacao_previa = pontuacao
            cadastro.save(update_fields=['pontuacao_previa'])
            messages.success(self.request, 'Cadastro atualizado com sucesso!')
            return redirect('cadastro_detail_pk', pk=cadastro.pk)
        return self.render_to_response(self.get_context_data(
            form=form, curso_formset=curso_formset, pos_formset=pos_formset
        ))

    def get_success_url(self):
        return reverse_lazy('cadastro_detail_pk', kwargs={'pk': self.kwargs['pk']})


class CadastroListView(ManagerRequiredMixin, ListView):
    model = CadastroBolsista
    template_name = 'cadastro/cadastro_list.html'
    context_object_name = 'cadastros'

    def get_queryset(self):
        return CadastroBolsista.objects.filter(tenant=self.request.tenant).select_related('user')


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoEdicao
        fields = ['campo', 'valor_novo']
        widgets = {
            'campo': forms.HiddenInput(),
            'valor_novo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SolicitacaoCreateView(TenantRequiredMixin, CreateView):
    model = SolicitacaoEdicao
    template_name = 'cadastro/solicitacao_form.html'
    form_class = SolicitacaoForm
    success_url = reverse_lazy('cadastro_detail')

    def get_initial(self):
        initial = super().get_initial()
        campo = self.request.GET.get('campo')
        if campo:
            initial['campo'] = campo
        return initial

    def form_valid(self, form):
        cadastro = get_object_or_404(
            CadastroBolsista, user=self.request.user, tenant=self.request.tenant
        )
        campo = form.cleaned_data['campo']
        valor_original = str(getattr(cadastro, campo, ''))
        form.instance.bolsista = cadastro
        form.instance.valor_original = valor_original
        form.instance.tenant = self.request.tenant
        messages.success(self.request, 'Solicitação de edição enviada para aprovação.')
        return super().form_valid(form)


class SolicitacaoListView(ManagerRequiredMixin, ListView):
    model = SolicitacaoEdicao
    template_name = 'cadastro/solicitacao_list.html'
    context_object_name = 'solicitacoes'

    def get_queryset(self):
        return SolicitacaoEdicao.objects.filter(
            tenant=self.request.tenant, status='pendente'
        ).select_related('bolsista', 'bolsista__user')


class SolicitacaoMultiplaView(TenantRequiredMixin, FormView):
    template_name = 'cadastro/solicitacao_multipla.html'
    form_class = CadastroForm
    success_url = reverse_lazy('cadastro_detail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        cadastro = self.get_cadastro()
        if cadastro:
            kwargs['instance'] = cadastro
        return kwargs

    def get(self, request, *args, **kwargs):
        if not self.get_cadastro():
            return redirect('cadastro_create')
        return super().get(request, *args, **kwargs)

    def get_cadastro(self):
        try:
            return CadastroBolsista.objects.get(user=self.request.user, tenant=self.request.tenant)
        except CadastroBolsista.DoesNotExist:
            return None

    def _make_curso_formset(self, data=None, cadastro=None):
        qs = cadastro.cursos_superiores.all() if cadastro else CursoSuperior.objects.none()
        return forms.modelformset_factory(
            CursoSuperior, form=CursoSuperiorForm, extra=1, can_delete=True
        )(data or None, prefix='cursos', queryset=qs)

    def _make_pos_formset(self, data=None, cadastro=None):
        qs = cadastro.pos_graduacoes.all() if cadastro else PosGraduacao.objects.none()
        return forms.modelformset_factory(
            PosGraduacao, form=PosGraduacaoForm, extra=1, can_delete=True
        )(data or None, prefix='pos', queryset=qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cadastro = self.get_cadastro()
        context['object'] = cadastro
        if 'curso_formset' not in kwargs:
            context['curso_formset'] = self._make_curso_formset(cadastro=cadastro)
        if 'pos_formset' not in kwargs:
            context['pos_formset'] = self._make_pos_formset(cadastro=cadastro)
        return context

    def post(self, request, *args, **kwargs):
        cadastro = self.get_cadastro()
        if not cadastro:
            return redirect('cadastro_create')
        form = self.get_form()
        curso_formset = self._make_curso_formset(request.POST, cadastro=cadastro)
        pos_formset = self._make_pos_formset(request.POST, cadastro=cadastro)
        if form.is_valid() and curso_formset.is_valid() and pos_formset.is_valid():
            return self.form_valid(form, curso_formset, pos_formset)
        return self.form_invalid(form, curso_formset, pos_formset)

    def form_invalid(self, form, curso_formset, pos_formset):
        return self.render_to_response(self.get_context_data(
            form=form, curso_formset=curso_formset, pos_formset=pos_formset
        ))

    def form_valid(self, form, curso_formset, pos_formset):
        cadastro = self.get_cadastro()
        alteracoes = 0

        for cf in curso_formset:
            if cf.cleaned_data and cf not in curso_formset.deleted_forms:
                curso = cf.save(commit=False)
                curso.bolsista = cadastro
                curso.tenant = self.request.tenant
                curso.save()
                alteracoes += 1

        for pf in pos_formset:
            if pf.cleaned_data and pf not in pos_formset.deleted_forms:
                pos = pf.save(commit=False)
                pos.bolsista = cadastro
                pos.tenant = self.request.tenant
                pos.save()
                alteracoes += 1

        campos_texto = ['data_nascimento', 'endereco']
        for campo in campos_texto:
            valor_antigo = str(getattr(cadastro, campo, '') or '')
            valor_novo = str(form.cleaned_data.get(campo, '') or '')
            if valor_antigo != valor_novo:
                SolicitacaoEdicao.objects.create(
                    bolsista=cadastro,
                    campo=campo,
                    valor_original=valor_antigo,
                    valor_novo=valor_novo,
                    status='pendente',
                    tenant=self.request.tenant,
                )
                alteracoes += 1

        telefone = form.cleaned_data.get('telefone')
        if telefone is not None:
            perfil = getattr(cadastro.user, 'perfil', None)
            valor_antigo = str(perfil.telefone if perfil else '')
            if valor_antigo != telefone:
                SolicitacaoEdicao.objects.create(
                    bolsista=cadastro,
                    campo='telefone',
                    valor_original=valor_antigo,
                    valor_novo=telefone,
                    status='pendente',
                    tenant=self.request.tenant,
                )
                alteracoes += 1

        campos_auto = [
            'participacao_projetos_anos', 'participacao_congressos', 'resumo_anais',
            'artigo_completo_anais', 'artigo_cientifico_nacional', 'artigo_cientifico_internacional',
            'livro_patente', 'participacao_minicurso', 'treinamento',
        ]
        for campo in campos_auto:
            valor_novo = form.cleaned_data.get(campo)
            if valor_novo is not None:
                setattr(cadastro, campo, valor_novo)
        cadastro.save(update_fields=campos_auto)

        criterios = CriterioClassificacao.objects.filter(tenant=self.request.tenant, ativo=True)
        _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
        cadastro.pontuacao_previa = pontuacao
        cadastro.save(update_fields=['pontuacao_previa'])

        if alteracoes:
            messages.success(
                self.request,
                f'Solicitação enviada para aprovação. {alteracoes} campo(s) aguardando revisão dos gestores.',
            )
        else:
            messages.info(self.request, 'Nenhuma alteração detectada.')

        return redirect(self.success_url)


class SolicitacaoRevisarView(ManagerRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        solicitacao = get_object_or_404(
            SolicitacaoEdicao, pk=kwargs['pk'], tenant=request.tenant, status='pendente'
        )
        acao = request.POST.get('acao')

        if acao == 'aprovar':
            solicitacao.status = 'aprovado'
            solicitacao.save()
            cadastro = solicitacao.bolsista
            campo = solicitacao.campo
            if hasattr(cadastro, campo):
                setattr(cadastro, campo, solicitacao.valor_novo)
                cadastro.save()
            messages.success(request, f'Solicitação de {solicitacao.campo} aprovada.')
        else:
            solicitacao.status = 'rejeitado'
            solicitacao.save()
            messages.warning(request, f'Solicitação de {solicitacao.campo} rejeitada.')

        solicitacao.revisado_por = request.user
        solicitacao.data_revisao = timezone.now()
        solicitacao.save()

        if request.headers.get('HX-Request'):
            html = render_to_string(
                'cadastro/partials/solicitacao_row.html',
                {'s': solicitacao},
                request=request,
            )
            return HttpResponse(html)
        return redirect('solicitacao_list')


class AdminDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = 'cadastro/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        from editais.models import Edital, AplicacaoEdital
        from classificacao.models import Classificacao, CriterioClassificacao

        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant

        context['total_usuarios'] = User.objects.filter(perfil__tenant=tenant).count()
        context['total_usuarios_ativos'] = User.objects.filter(perfil__tenant=tenant, is_active=True).count()
        context['usuarios_pendentes'] = User.objects.filter(
            perfil__tenant=tenant, is_active=False
        ).select_related('perfil')

        context['cadastros'] = CadastroBolsista.objects.filter(tenant=tenant).select_related('user')
        context['total_cadastros'] = context['cadastros'].count()

        context['total_editais'] = Edital.objects.filter(tenant=tenant).count()
        context['total_aplicacoes'] = AplicacaoEdital.objects.filter(tenant=tenant).count()
        context['total_classificacoes'] = Classificacao.objects.filter(tenant=tenant).count()
        context['total_criterios'] = CriterioClassificacao.objects.filter(tenant=tenant).count()

        context['solicitacoes_pendentes'] = SolicitacaoEdicao.objects.filter(
            tenant=tenant, status='pendente'
        ).select_related('bolsista__user')[:10]

        context['ultimos_cadastros'] = context['cadastros'].order_by('-created_at')[:5]

        return context


class CsvImportView(ManagerRequiredMixin, TemplateView):
    template_name = 'classificacao/csv_import.html'
