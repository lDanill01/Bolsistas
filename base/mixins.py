from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class RoleRequiredMixin(UserPassesTestMixin):
    roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        perfil = getattr(self.request.user, 'perfil', None)
        if not perfil:
            return False
        return perfil.tipo in self.roles


class AdminRequiredMixin(RoleRequiredMixin):
    roles = ['ADMIN']


class ManagerRequiredMixin(RoleRequiredMixin):
    roles = ['ADMIN', 'MANAGER']


class TenantRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return redirect(reverse_lazy('landing'))
        return super().dispatch(request, *args, **kwargs)
