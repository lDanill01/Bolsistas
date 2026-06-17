from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from base.mixins import TenantRequiredMixin, ManagerRequiredMixin
from .models import EditalProvisorio
from .forms import EditalProvisorioForm, CronogramaEventoFormSet


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = EditalProvisorio.STATUS_CHOICES
        return context


class EditalProvisorioListView(TenantRequiredMixin, ContextMixin, ListView):
    model = EditalProvisorio
    template_name = 'edital_provisorio/edital_list.html'
    context_object_name = 'editais'
    paginate_by = 10

    def get_queryset(self):
        qs = EditalProvisorio.objects.filter(tenant=self.request.tenant).select_related('criado_por')
        busca = self.request.GET.get('busca', '')
        status = self.request.GET.get('status', '')
        if busca:
            qs = qs.filter(nome_instituto__icontains=busca)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busca'] = self.request.GET.get('busca', '')
        context['status_atual'] = self.request.GET.get('status', '')
        return context


class EditalProvisorioCreateView(ManagerRequiredMixin, ContextMixin, CreateView):
    model = EditalProvisorio
    template_name = 'edital_provisorio/edital_form.html'
    form_class = EditalProvisorioForm
    success_url = reverse_lazy('edital_provisorio:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                self.request.POST, prefix='cronograma'
            )
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(prefix='cronograma')
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        if cronograma_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.criado_por = self.request.user
            self.object.tenant = self.request.tenant
            self.object.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            messages.success(self.request, 'Edital provisório criado com sucesso!')
            return redirect(self.get_success_url())
        return self.render_to_response(context)


class EditalProvisorioUpdateView(ManagerRequiredMixin, ContextMixin, UpdateView):
    model = EditalProvisorio
    template_name = 'edital_provisorio/edital_form.html'
    form_class = EditalProvisorioForm

    def get_queryset(self):
        return EditalProvisorio.objects.filter(tenant=self.request.tenant)

    def get_success_url(self):
        return reverse_lazy('edital_provisorio:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                self.request.POST, instance=self.object, prefix='cronograma'
            )
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                instance=self.object, prefix='cronograma'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        if cronograma_formset.is_valid():
            self.object = form.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            messages.success(self.request, 'Edital provisório atualizado com sucesso!')
            return redirect(self.get_success_url())
        return self.render_to_response(context)


class EditalProvisorioDetailView(TenantRequiredMixin, ContextMixin, DetailView):
    model = EditalProvisorio
    template_name = 'edital_provisorio/edital_detail.html'
    context_object_name = 'edital'

    def get_queryset(self):
        return EditalProvisorio.objects.filter(tenant=self.request.tenant).select_related('criado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cronograma'] = self.object.cronograma.all()
        return context


class EditalProvisorioDeleteView(ManagerRequiredMixin, ContextMixin, DeleteView):
    model = EditalProvisorio
    template_name = 'edital_provisorio/edital_confirm_delete.html'
    success_url = reverse_lazy('edital_provisorio:list')

    def get_queryset(self):
        return EditalProvisorio.objects.filter(tenant=self.request.tenant)

    def form_valid(self, form):
        messages.success(self.request, 'Edital provisório removido com sucesso!')
        return super().form_valid(form)
