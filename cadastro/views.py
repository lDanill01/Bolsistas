from decimal import Decimal
import json
from django.views.generic import CreateView, DetailView, UpdateView, ListView, TemplateView, FormView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.db.models import Q
from django import forms

from base.mixins import (
    ManagerRequiredMixin, ViewUserRequiredMixin,
    ManagerOrExecuteRequiredMixin, GROUP_MANAGER,
)
from .models import (
    CadastroBolsista, FormacaoAcademica, ExperienciaProfissional,
    AnexoComprobatorio, SolicitacaoEdicao, validar_maioridade,
)

from .utils import calcular_pontuacao_previa
from .cursos import get_areas, get_todos_cursos, get_cursos_por_area, get_instituicoes
from classificacao.models import CriterioClassificacao
from accounts.models import User, Perfil


ANEXO_TIPOS = [
    'rg_cpf', 'comprovante_endereco',
    'participacao_congressos', 'resumo_anais', 'artigo_completo_anais',
    'artigo_cientifico_nacional', 'artigo_cientifico_internacional',
    'livro_patente', 'participacao_minicurso', 'treinamento',
]


def _is_manager(user):
    return user.is_superuser or user.groups.filter(name=GROUP_MANAGER).exists()


def _is_manager_or_executor(user):
    from base.mixins import GROUP_EXECUTE_USER
    return user.is_superuser or user.groups.filter(
        name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]
    ).exists()


class FormacaoAcademicaForm(forms.ModelForm):
    area = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    curso = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    instituicao = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = FormacaoAcademica
        fields = ['tipo', 'status', 'instituicao', 'area', 'curso', 'ano_conclusao']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'ano_conclusao': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 2024'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        self.fields['instituicao'].required = False
        self.fields['area'].required = False
        self.fields['curso'].required = False
        self.fields['ano_conclusao'].required = False


class ExperienciaProfissionalForm(forms.ModelForm):
    class Meta:
        model = ExperienciaProfissional
        fields = ['area_atuacao', 'anos_experiencia', 'anexo']
        widgets = {
            'area_atuacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Engenharia de Produção'}),
            'anos_experiencia': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '0'}),
            'anexo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area_atuacao'].required = False
        self.fields['anexo'].required = False


class CadastroForm(forms.ModelForm):
    class Meta:
        model = CadastroBolsista
        fields = [
            'telefone', 'data_nascimento',
            'rua', 'numero', 'bairro', 'cidade', 'estado',
            'curriculo',
            'participacao_congressos', 'resumo_anais', 'artigo_completo_anais',
            'artigo_cientifico_nacional', 'artigo_cientifico_internacional',
            'livro_patente', 'participacao_minicurso', 'treinamento',
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(67) 99999-9999'}),
            'rua': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'curriculo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
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
        self.fields['telefone'].required = False
        self.fields['rua'].required = False
        self.fields['numero'].required = False
        self.fields['bairro'].required = False
        self.fields['cidade'].required = False
        self.fields['estado'].required = False


class CadastroCreateView(ViewUserRequiredMixin, FormView):
    template_name = 'cadastro/cadastro_form.html'
    form_class = CadastroForm
    success_url = reverse_lazy('cadastro_detail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = None
        context['cursos_por_area'] = json.dumps(get_cursos_por_area(), ensure_ascii=False)
        context['areas'] = json.dumps([a[0] for a in get_areas()], ensure_ascii=False)
        context['instituicoes'] = json.dumps(get_instituicoes(), ensure_ascii=False)
        if 'formacao_formset' not in kwargs:
            context['formacao_formset'] = forms.modelformset_factory(
                FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
            )(queryset=FormacaoAcademica.objects.none(), prefix='formacoes')
        if 'experiencia_formset' not in kwargs:
            context['experiencia_formset'] = _experiencia_formset_factory(extra=1)(
                queryset=ExperienciaProfissional.objects.none(), prefix='experiencias'
            )
        context['anexo_tipos'] = ANEXO_TIPOS
        context['user'] = self.request.user
        return context

    def form_valid(self, form):
        cadastro = form.save(commit=False)
        cadastro.user = self.request.user
        if not cadastro.data_nascimento:
            try:
                cadastro.data_nascimento = self.request.user.perfil.data_nascimento
            except (AttributeError, CadastroBolsista.DoesNotExist):
                pass
        cadastro.save()

        FormSet = forms.modelformset_factory(
            FormacaoAcademica, form=FormacaoAcademicaForm, extra=0, can_delete=True
        )
        formset = FormSet(self.request.POST, prefix='formacoes')
        if formset.is_valid():
            for fm in formset:
                if fm.cleaned_data and not fm.cleaned_data.get('DELETE', False):
                    fa = fm.save(commit=False)
                    fa.bolsista = cadastro
                    fa.save()

        exp_formset = _experiencia_formset_factory(extra=0)(
            self.request.POST, self.request.FILES, prefix='experiencias'
        )
        if exp_formset.is_valid():
            _salvar_experiencias(exp_formset, cadastro)

        _salvar_anexos(cadastro, self.request.FILES)

        from classificacao.models import AvaliacaoBolsista
        if not AvaliacaoBolsista.objects.filter(bolsista=cadastro).exists():
            criterios = CriterioClassificacao.objects.filter(ativo=True)
            _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
            cadastro.pontuacao_previa = pontuacao
            cadastro.save(update_fields=['pontuacao_previa'])
        messages.success(self.request, 'Cadastro criado com sucesso!')
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        FormSet = forms.modelformset_factory(
            FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
        )
        formset = FormSet(request.POST, prefix='formacoes')
        exp_formset = _experiencia_formset_factory(extra=1)(
            request.POST, request.FILES, prefix='experiencias'
        )
        if form.is_valid() and formset.is_valid() and exp_formset.is_valid():
            return self.form_valid(form)
        return self.render_to_response(self.get_context_data(
            form=form, formacao_formset=formset, experiencia_formset=exp_formset
        ))

    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'cadastro'):
            return redirect('cadastro_detail')
        return super().get(request, *args, **kwargs)


def _experiencia_formset_factory(extra=1):
    return forms.modelformset_factory(
        ExperienciaProfissional, form=ExperienciaProfissionalForm,
        extra=extra, can_delete=True,
    )


def _salvar_experiencias(formset, cadastro):
    for fm in formset:
        if fm.cleaned_data and not fm.cleaned_data.get('DELETE', False):
            if not (fm.cleaned_data.get('area_atuacao') or
                    fm.cleaned_data.get('anos_experiencia') or
                    fm.cleaned_data.get('anexo')):
                continue
            exp = fm.save(commit=False)
            exp.bolsista = cadastro
            exp.save()
    cadastro.sincronizar_anos_experiencia()


def _salvar_anexos(cadastro, files):
    for tipo in ANEXO_TIPOS:
        for f in files.getlist('anexo_' + tipo):
            if f and f.name:
                AnexoComprobatorio.objects.create(
                    bolsista=cadastro, tipo=tipo, anexo=f
                )


class CadastroDetailView(LoginRequiredMixin, DetailView):
    model = CadastroBolsista
    template_name = 'cadastro/cadastro_detail.html'
    context_object_name = 'cadastro'

    def get(self, request, *args, **kwargs):
        if _is_manager(request.user):
            pk = kwargs.get('pk')
            if pk:
                return super().get(request, *args, **kwargs)
        if not request.user.groups.filter(name='ViewUser').exists() and not request.user.is_superuser:
            return redirect('home')
        if not hasattr(request.user, 'cadastro'):
            return redirect('cadastro_create')
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if _is_manager(self.request.user):
            pk = self.kwargs.get('pk')
            if pk:
                return get_object_or_404(CadastroBolsista, pk=pk)
        return get_object_or_404(CadastroBolsista, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cadastro = context['cadastro']
        context['can_edit'] = cadastro.user == self.request.user or _is_manager(self.request.user)
        context['formacoes'] = cadastro.formacoes.all()
        return context


class CadastroUpdateView(ManagerRequiredMixin, FormView):
    template_name = 'cadastro/cadastro_form.html'

    def get_object(self):
        return get_object_or_404(
            CadastroBolsista, pk=self.kwargs['pk']
        )

    def get_form_class(self):
        return CadastroForm

    def get_form(self, form_class=None):
        return CadastroForm(instance=self.get_object(), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cadastro = self.get_object()
        context['object'] = cadastro
        context['user'] = self.request.user
        context['cursos_por_area'] = json.dumps(get_cursos_por_area(), ensure_ascii=False)
        context['areas'] = json.dumps([a[0] for a in get_areas()], ensure_ascii=False)
        context['instituicoes'] = json.dumps(get_instituicoes(), ensure_ascii=False)
        if 'formacao_formset' not in kwargs:
            context['formacao_formset'] = forms.modelformset_factory(
                FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
            )(queryset=cadastro.formacoes.all(), prefix='formacoes')
        if 'experiencia_formset' not in kwargs:
            context['experiencia_formset'] = _experiencia_formset_factory(extra=1)(
                queryset=cadastro.experiencias.all(), prefix='experiencias'
            )
        context['anexo_tipos'] = ANEXO_TIPOS
        return context

    def post(self, request, *args, **kwargs):
        cadastro = self.get_object()
        form = CadastroForm(request.POST, request.FILES, instance=cadastro)
        FormSet = forms.modelformset_factory(
            FormacaoAcademica, form=FormacaoAcademicaForm, extra=0, can_delete=True
        )
        formset = FormSet(request.POST, prefix='formacoes')
        exp_formset = _experiencia_formset_factory(extra=0)(
            request.POST, request.FILES, prefix='experiencias'
        )
        if form.is_valid() and formset.is_valid() and exp_formset.is_valid():
            cadastro = form.save()
            for fm in formset:
                if fm.cleaned_data and not fm.cleaned_data.get('DELETE', False):
                    fa = fm.save(commit=False)
                    fa.bolsista = cadastro
                    fa.save()
            _salvar_experiencias(exp_formset, cadastro)
            _salvar_anexos(cadastro, request.FILES)
            from classificacao.models import AvaliacaoBolsista
            if not AvaliacaoBolsista.objects.filter(bolsista=cadastro).exists():
                criterios = CriterioClassificacao.objects.filter(ativo=True)
                _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
                cadastro.pontuacao_previa = pontuacao
                cadastro.save(update_fields=['pontuacao_previa'])
            messages.success(self.request, 'Cadastro atualizado com sucesso!')
            return redirect('cadastro_detail_pk', pk=cadastro.pk)
        return self.render_to_response(self.get_context_data(
            form=form, formacao_formset=formset, experiencia_formset=exp_formset
        ))

    def get_success_url(self):
        return reverse_lazy('cadastro_detail_pk', kwargs={'pk': self.kwargs['pk']})


class CadastroListView(ManagerRequiredMixin, ListView):
    model = CadastroBolsista
    template_name = 'cadastro/cadastro_list.html'
    context_object_name = 'cadastros'

    def get_queryset(self):
        qs = CadastroBolsista.objects.all().select_related('user')
        busca = self.request.GET.get('busca', '')
        if busca:
            qs = qs.filter(
                Q(user__nome_completo__icontains=busca) |
                Q(numero_serie__icontains=busca)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busca'] = self.request.GET.get('busca', '')
        return context


class BolsistaCreateForm(forms.ModelForm):
    data_nascimento = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        validators=[validar_maioridade],
    )
    telefone = forms.CharField(
        label='Telefone', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(67) 99999-9999'}),
    )
    unidade = forms.CharField(
        label='Unidade', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['nome_completo', 'email']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do bolsista'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este e-mail.')
        return email


class BolsistaCreateView(ManagerOrExecuteRequiredMixin, FormView):
    template_name = 'cadastro/bolsista_form.html'
    form_class = CadastroForm
    success_url = reverse_lazy('cadastro_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = None
        if 'user_form' not in kwargs:
            context['user_form'] = BolsistaCreateForm()
        if 'formacao_formset' not in kwargs:
            context['formacao_formset'] = forms.modelformset_factory(
                FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
            )(queryset=FormacaoAcademica.objects.none(), prefix='formacoes')
        if 'experiencia_formset' not in kwargs:
            context['experiencia_formset'] = _experiencia_formset_factory(extra=1)(
                queryset=ExperienciaProfissional.objects.none(), prefix='experiencias'
            )
        context['anexo_tipos'] = ANEXO_TIPOS
        return context

    def post(self, request, *args, **kwargs):
        user_form = BolsistaCreateForm(request.POST)
        form = self.get_form()
        FormSet = forms.modelformset_factory(
            FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
        )
        formset = FormSet(request.POST, prefix='formacoes')
        exp_formset = _experiencia_formset_factory(extra=1)(
            request.POST, request.FILES, prefix='experiencias'
        )

        if user_form.is_valid() and form.is_valid() and formset.is_valid() and exp_formset.is_valid():
            return self.form_valid(user_form, form, formset, exp_formset)
        return self.render_to_response(self.get_context_data(
            user_form=user_form, form=form, formacao_formset=formset,
            experiencia_formset=exp_formset
        ))

    def form_valid(self, user_form, form, formset, exp_formset):
        import secrets

        user = User.objects.create_user(
            email=user_form.cleaned_data['email'],
            nome_completo=user_form.cleaned_data['nome_completo'],
            password=secrets.token_urlsafe(16),
        )
        user.is_active = True
        user.save()

        perfil, _ = Perfil.objects.get_or_create(user=user)
        perfil.telefone = user_form.cleaned_data.get('telefone', '')
        perfil.unidade = user_form.cleaned_data.get('unidade', '')
        perfil.data_nascimento = user_form.cleaned_data.get('data_nascimento')
        perfil.save()

        cadastro = form.save(commit=False)
        cadastro.user = user
        cadastro.data_nascimento = user_form.cleaned_data.get('data_nascimento')
        cadastro.save()

        for fm in formset:
            if fm.cleaned_data and not fm.cleaned_data.get('DELETE', False):
                fa = fm.save(commit=False)
                fa.bolsista = cadastro
                fa.save()

        if exp_formset.is_valid():
            _salvar_experiencias(exp_formset, cadastro)

        _salvar_anexos(cadastro, self.request.FILES)

        criterios = CriterioClassificacao.objects.filter(ativo=True)
        _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
        cadastro.pontuacao_previa = pontuacao
        cadastro.save(update_fields=['pontuacao_previa'])

        messages.success(
            self.request,
            f'Bolsista {user.nome_completo} cadastrado com sucesso! '
            f'O bolsista deverá usar a opção "Esqueci minha senha" no primeiro acesso para definir sua senha.'
        )
        return redirect('cadastro_detail_pk', pk=cadastro.pk)


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoEdicao
        fields = ['campo', 'valor_novo']
        widgets = {
            'campo': forms.HiddenInput(),
            'valor_novo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SolicitacaoCreateView(ViewUserRequiredMixin, CreateView):
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
            CadastroBolsista, user=self.request.user
        )
        campo = form.cleaned_data['campo']
        valor_original = str(getattr(cadastro, campo, ''))
        form.instance.bolsista = cadastro
        form.instance.valor_original = valor_original
        messages.success(self.request, 'Solicitação de edição enviada para aprovação.')
        return super().form_valid(form)


class SolicitacaoListView(ManagerRequiredMixin, ListView):
    model = SolicitacaoEdicao
    template_name = 'cadastro/solicitacao_list.html'
    context_object_name = 'solicitacoes'

    def get_queryset(self):
        return SolicitacaoEdicao.objects.filter(
            status='pendente'
        ).select_related('bolsista', 'bolsista__user')


class SolicitacaoMultiplaView(ViewUserRequiredMixin, FormView):
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
            return CadastroBolsista.objects.get(user=self.request.user)
        except CadastroBolsista.DoesNotExist:
            return None

    def _make_formset(self, data=None, cadastro=None):
        qs = cadastro.formacoes.all() if cadastro else FormacaoAcademica.objects.none()
        return forms.modelformset_factory(
            FormacaoAcademica, form=FormacaoAcademicaForm, extra=1, can_delete=True
        )(data or None, prefix='formacoes', queryset=qs)

    def _make_experiencia_formset(self, data=None, files=None, cadastro=None):
        qs = cadastro.experiencias.all() if cadastro else ExperienciaProfissional.objects.none()
        return _experiencia_formset_factory(extra=1)(
            data or None, files or None, prefix='experiencias', queryset=qs
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cadastro = self.get_cadastro()
        context['object'] = cadastro
        if 'formacao_formset' not in kwargs:
            context['formacao_formset'] = self._make_formset(cadastro=cadastro)
        if 'experiencia_formset' not in kwargs:
            context['experiencia_formset'] = self._make_experiencia_formset(cadastro=cadastro)
        context['anexo_tipos'] = ANEXO_TIPOS
        return context

    def post(self, request, *args, **kwargs):
        cadastro = self.get_cadastro()
        if not cadastro:
            return redirect('cadastro_create')
        form = self.get_form()
        formset = self._make_formset(request.POST, cadastro=cadastro)
        exp_formset = self._make_experiencia_formset(
            request.POST, request.FILES, cadastro=cadastro
        )
        if form.is_valid() and formset.is_valid() and exp_formset.is_valid():
            return self.form_valid(form, formset, exp_formset)
        return self.form_invalid(form, formset, exp_formset)

    def form_invalid(self, form, formset, exp_formset=None):
        return self.render_to_response(self.get_context_data(
            form=form, formacao_formset=formset, experiencia_formset=exp_formset
        ))

    def form_valid(self, form, formset, exp_formset=None):
        cadastro = self.get_cadastro()
        alteracoes = 0

        for fm in formset:
            if fm.cleaned_data and fm not in formset.deleted_forms:
                fa = fm.save(commit=False)
                fa.bolsista = cadastro
                fa.save()
                alteracoes += 1

        if exp_formset is not None and exp_formset.is_valid():
            _salvar_experiencias(exp_formset, cadastro)

        _salvar_anexos(cadastro, self.request.FILES)

        campos_auto = [
            'participacao_projetos_anos', 'participacao_congressos', 'resumo_anais',
            'artigo_completo_anais', 'artigo_cientifico_nacional', 'artigo_cientifico_internacional',
            'livro_patente', 'participacao_minicurso', 'treinamento',
        ]
        for campo in campos_auto:
            valor_novo = form.cleaned_data.get(campo)
            if valor_novo is not None:
                setattr(cadastro, campo, valor_novo)
        cadastro.sincronizar_anos_experiencia()
        cadastro.save(update_fields=campos_auto)

        from classificacao.models import AvaliacaoBolsista
        if not AvaliacaoBolsista.objects.filter(bolsista=cadastro).exists():
            criterios = CriterioClassificacao.objects.filter(ativo=True)
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
            SolicitacaoEdicao, pk=kwargs['pk'], status='pendente'
        )
        acao = request.POST.get('acao')

        solicitacao.revisado_por = request.user
        solicitacao.data_revisao = timezone.now()

        if acao == 'aprovar':
            solicitacao.status = 'aprovado'
            cadastro = solicitacao.bolsista
            campo = solicitacao.campo
            if hasattr(cadastro, campo):
                setattr(cadastro, campo, solicitacao.valor_novo)
                cadastro.save()
            messages.success(request, f'Solicitação de {solicitacao.campo} aprovada.')
        else:
            solicitacao.status = 'rejeitado'
            messages.warning(request, f'Solicitação de {solicitacao.campo} rejeitada.')

        solicitacao.save()

        if request.headers.get('HX-Request'):
            html = render_to_string(
                'cadastro/partials/solicitacao_row.html',
                {'s': solicitacao},
                request=request,
            )
            return HttpResponse(html)
        return redirect('solicitacao_list')


class MinhasCandidaturasView(ViewUserRequiredMixin, TemplateView):
    """Pagina 'Minhas Candidaturas' — trilha completa do candidato:
    aplicacoes, status, avaliacoes e pontuacao."""
    template_name = 'cadastro/minhas_candidaturas.html'

    def get(self, request, *args, **kwargs):
        try:
            self.bolsista = CadastroBolsista.objects.get(user=request.user)
        except CadastroBolsista.DoesNotExist:
            return redirect('cadastro_create')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bolsista = self.bolsista

        # Aplicacoes com edital relacionado (ordenadas por data mais recente)
        aplicacoes = (
            bolsista.aplicacoes
            .select_related('edital')
            .order_by('-created_at')
        )

        # Avaliacoes com criterio e avaliador (ordenadas por criterio)
        avaliacoes = (
            bolsista.avaliacoes
            .select_related('criterio', 'avaliado_por')
            .order_by('criterio__nome')
        )

        # Totais
        total_avaliacoes = avaliacoes.count()
        pontuacao_avaliacoes = sum(a.pontos for a in avaliacoes)

        context.update({
            'bolsista': bolsista,
            'aplicacoes': aplicacoes,
            'avaliacoes': avaliacoes,
            'total_aplicacoes': aplicacoes.count(),
            'total_avaliacoes': total_avaliacoes,
            'pontuacao_avaliacoes': pontuacao_avaliacoes,
            'pontuacao_previa': bolsista.pontuacao_previa,
            'status_labels': {
                'pendente': ('warning', 'Pendente'),
                'em_analise': ('info', 'Em Análise'),
                'aprovado': ('success', 'Aprovado'),
                'rejeitado': ('danger', 'Rejeitado'),
                'cancelado': ('secondary', 'Cancelado'),
            },
        })
        return context


def _recalcular_pontuacao(cadastro):
    from classificacao.models import AvaliacaoBolsista
    tem_avaliacao_manual = AvaliacaoBolsista.objects.filter(bolsista=cadastro).exists()
    if tem_avaliacao_manual:
        return
    criterios = CriterioClassificacao.objects.filter(ativo=True)
    _, pontuacao = calcular_pontuacao_previa(cadastro, criterios)
    cadastro.pontuacao_previa = pontuacao
    cadastro.save(update_fields=['pontuacao_previa'])


@login_required
def formacao_add(request, pk):
    cadastro, error = _check_cadastro_permission(request, pk)
    if error:
        return error

    ctx_base = {
        'formacoes': cadastro.formacoes.all(),
        'cadastro': cadastro,
        'can_edit': True,
        'areas': json.dumps([a[0] for a in get_areas()], ensure_ascii=False),
        'cursos_por_area': json.dumps(get_cursos_por_area(), ensure_ascii=False),
        'instituicoes': json.dumps(get_instituicoes(), ensure_ascii=False),
    }

    if request.method == 'POST':
        form = FormacaoAcademicaForm(request.POST)
        if form.is_valid():
            fa = form.save(commit=False)
            fa.bolsista = cadastro
            fa.save()
            _recalcular_pontuacao(cadastro)
            messages.success(request, 'Formação adicionada com sucesso!')
            return render(request, 'cadastro/partials/formacao_section.html', ctx_base)
    else:
        if request.GET.get('cancel'):
            return render(request, 'cadastro/partials/formacao_section.html', ctx_base)
        form = FormacaoAcademicaForm()

    ctx_base['formacao_form'] = form
    return render(request, 'cadastro/partials/formacao_section.html', ctx_base)


@login_required
def formacao_remove(request, pk, formacao_pk):
    cadastro, error = _check_cadastro_permission(request, pk)
    if error:
        return error

    fa = get_object_or_404(FormacaoAcademica, pk=formacao_pk, bolsista=cadastro)
    fa.delete()
    _recalcular_pontuacao(cadastro)
    messages.success(request, 'Formação removida com sucesso!')

    return render(request, 'cadastro/partials/formacao_section.html', {
        'formacoes': cadastro.formacoes.all(),
        'cadastro': cadastro,
        'can_edit': True,
    })


def _check_cadastro_permission(request, pk):
    cadastro = get_object_or_404(CadastroBolsista, pk=pk)
    if not (request.user.is_superuser or _is_manager(request.user) or cadastro.user == request.user):
        return None, HttpResponseForbidden()
    return cadastro, None
