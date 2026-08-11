from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string

from .models import Notificacao


class NotificacaoListView(LoginRequiredMixin, ListView):
    model = Notificacao
    template_name = 'notifications/notificacao_list.html'
    context_object_name = 'notificacoes'
    paginate_by = 20

    def get_queryset(self):
        return Notificacao.objects.filter(
            destinatario=self.request.user,
        ).select_related('destinatario')


class MarcarLidaView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk):
        notificacao = get_object_or_404(
            Notificacao, pk=pk, destinatario=request.user
        )
        notificacao.lido = True
        notificacao.save(update_fields=['lido'])
        if request.headers.get('HX-Request'):
            html = render_to_string(
                'notifications/partials/notificacao_item.html',
                {'n': notificacao},
                request=request,
            )
            return HttpResponse(html)
        return redirect('notificacao_list')


class MarcarTodasLidasView(LoginRequiredMixin, View):
    def post(self, request):
        Notificacao.objects.filter(
            destinatario=request.user, lido=False
        ).update(lido=True)
        return redirect('notificacao_list')


@login_required
def notificacao_unread_count(request):
    count = Notificacao.objects.filter(
        destinatario=request.user, lido=False
    ).count()
    html = render_to_string(
        'notifications/partials/bell.html',
        {'unread_count': count},
        request=request,
    )
    return HttpResponse(html, content_type='text/html; charset=utf-8')
