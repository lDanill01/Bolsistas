from django.contrib.auth.mixins import UserPassesTestMixin


GROUP_MANAGER = 'Manager'
GROUP_VIEW_USER = 'ViewUser'
GROUP_EXECUTE_USER = 'ExecuteUser'


def user_has_group(user, groups):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=groups).exists()


class GroupRequiredMixin(UserPassesTestMixin):
    groups = []

    def test_func(self):
        return user_has_group(self.request.user, self.groups)


class ManagerRequiredMixin(GroupRequiredMixin):
    groups = [GROUP_MANAGER]


class ViewUserRequiredMixin(GroupRequiredMixin):
    groups = [GROUP_VIEW_USER]


class ExecuteUserRequiredMixin(GroupRequiredMixin):
    groups = [GROUP_EXECUTE_USER]


class ManagerOrExecuteRequiredMixin(GroupRequiredMixin):
    groups = [GROUP_MANAGER, GROUP_EXECUTE_USER]
