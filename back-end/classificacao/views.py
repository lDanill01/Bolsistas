from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from base.mixins import ManagerRequiredMixin, ManagerOrExecuteRequiredMixin
from .models import CriterioClassificacao, AvaliacaoBolsista


class CriterioListView(ManagerOrExecuteRequiredMixin, ListView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_list.html'
    context_object_name = 'criterios'

    def get_queryset(self):
        return CriterioClassificacao.objects.all().order_by('nome')


class CriterioCreateView(ManagerRequiredMixin, CreateView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_form.html'
    fields = ['nome', 'tipo_criterio', 'descricao', 'peso', 'peso_maximo', 'ativo']
    success_url = reverse_lazy('criterio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Critério de classificação criado com sucesso!')
        return super().form_valid(form)


class CriterioUpdateView(ManagerRequiredMixin, UpdateView):
    model = CriterioClassificacao
    template_name = 'classificacao/criterio_form.html'
    fields = ['nome', 'tipo_criterio', 'descricao', 'peso', 'peso_maximo', 'ativo']
    success_url = reverse_lazy('criterio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Critério de classificação atualizado com sucesso!')
        return super().form_valid(form)


class AvaliacaoListView(ManagerOrExecuteRequiredMixin, ListView):
    model = AvaliacaoBolsista
    template_name = 'classificacao/avaliacao_list.html'
    context_object_name = 'avaliacoes'

    def get_queryset(self):
        return AvaliacaoBolsista.objects.select_related(
            'bolsista', 'bolsista__user', 'criterio', 'avaliado_por'
        ).order_by('-created_at')


class AvaliacaoDetailView(ManagerOrExecuteRequiredMixin, DetailView):
    model = AvaliacaoBolsista
    template_name = 'classificacao/avaliacao_detail.html'
    context_object_name = 'avaliacao'

    def get_queryset(self):
        return AvaliacaoBolsista.objects.select_related(
            'bolsista', 'bolsista__user', 'criterio', 'avaliado_por'
        )
