"""
Generic view permission mixins
------------------------------

Here we put the classes that derive from
:py:class:`braces.views._access.AccessMixin` because ``AccessMixin` needs Django
to be fully booted in order to be importable.  This is because the module that  ``AccessAdmin``
is in imports some things from ``django.contrib.auth`` that want to load app configs, which
aren't available until after django has fully booted.

For the same reason, don't import this file in ``wildewidgets.views.__init.py``,
because anyone importing any widget that is also a JSON view will cause
``AppRegistryNotReady`` exceptions.
"""
from typing import Optional, List, Type

from braces.views._access import AccessMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.http.request import HttpRequest


class PermissionRequiredMixin(AccessMixin):
    """
    This class-based view mixin grants or denies access to a view based on a
    user's group membership or specific permisisons.

    * Django superusers are always authorized
    * Anonymous users are never authorized
    * If ``request.user`` is in one of the groups returned by
      :py:meth:`get_groups_required`, they are authorized.
    * Failing that, if ``request.user`` has one of the permissions returned by
      :py:meth:`get_permissions_required`, they are authorized.
    * Additionally, if :py:attr:`model` and :py:attr:`required_model_permissions`
      are both set, extend what we got from :py:meth:`get_permissions_required`
      with what we get from :py:meth:`get_model_permissions`
    """

    #: Users who are members of the named Django auth groups will be permitted
    #: access to the view, and those who are not will be denied access.
    groups_required: Optional[List[str]] = None

    #: Users who have any of the listed Django model permissions
    #: will be permitted access to the view.
    permissions_required: Optional[List[str]] = None

    #: Used in conjunction with :py:attr:`required_model_permissions`,
    #: this is the model we want to act on.  This should be set by our
    #: our subclass, which is why it is just a type declaration here.
    #: This is used by :py:meth:`get_model_permissions`
    model: Optional[Type[Model]]
    #: A list of simple strings like ``view``, ``add``, ``change``, ``delete`` that
    #: represent actions that can be done on a model.  This is used by
    #: py:meth:`get_model_permissions`
    required_model_permissions: Optional[List[str]] = None

    def user_can_view(self) -> bool:
        required_perms = self.get_model_permissions(self.model, ['view'])
        return self.check_permissions(
            groups_required=[],
            permissions_required=required_perms
        )

    def user_can_create(self) -> bool:
        required_perms = self.get_model_permissions(self.model, ['add'])
        return self.check_permissions(
            groups_required=[],
            permissions_required=required_perms
        )

    def user_can_update(self) -> bool:
        required_perms = self.get_model_permissions(self.model, ['change'])
        return self.check_permissions(
            groups_required=[],
            permissions_required=required_perms
        )

    def user_can_delete(self) -> bool:
        required_perms = self.get_model_permissions(self.model, ['delete'])
        return self.check_permissions(
            groups_required=[],
            permissions_required=required_perms
        )

    def get_groups_required(self) -> List[Group]:
        if self.groups_required is None:
            return []
        return Group.objects.filter(name__in=self.groups_required)

    def get_permissions_required(self) -> List[str]:
        if self.permissions_required is None:
            return []
        return self.permissions_required

    def get_model_permissions(self, model: Model, perms: List[str]) -> List[str]:
        """
        Given a list of simple strings like ``view``, ``add``, ``change``, etc.
        and a Django :py:class:`django.db.models.Model`, return the list of actual
        permissions names that would apply to that model, e.g. for a model ``Foo`` in
        the django app ``core``::

            >>> PermissionMixin.get_model_permissions(Foo, ['add', 'change'])
            ['core.add_foo', 'core.change_foo']

        Args:
            model: the model for which to build permission strings
            perms: the list of short permissions

        Returns:
            The fully formed permission strings
        """
        required_perms = set()
        for perm in perms:
            full_perm = f'{self.model._meta.app_label}.{perm}_{self.model._meta.object_name.lower()}'
            required_perms.add(full_perm)
        return list(required_perms)

    def check_permissions(
        self,
        groups_required: List[Group] = None,
        permissions_required: List[str] = None
    ) -> bool:
        """
        Check if the current user is authorized for our view.

        * Django superusers are always authorized
        * Anonymous users are never authorized
        * If ``request.user`` is in one of the groups returned by
          :py:meth:`get_groups_required`, they are authorized.
        * Failing that, if ``request.user`` has one of the permissions returned by
          :py:meth:`get_permissions_required`, they are authorized.
        * Additionally, if :py:attr:`model` and :py:attr:`required_model_permissions`
          are both set, extend what we got from :py:meth:`get_permissions_required`
          with what we get from :py:meth:`get_model_permissions`

        Args:
            request: the current request

        Keyword Args:
            groups_required: test versus these groups instead of what
                :py:meth:`get_groups_required` returns
            permissions_required: test versus these permissions instead of what
                :py:meth:`get_permissions_required` returns

        Returns:
            Return ``True`` if the user is authorized, ``False`` otherwise.
        """
        if groups_required is None:
            groups_required = self.get_groups_required()
        if permissions_required is None:
            permissions_required = self.get_permissions_required()
        if self.required_model_permissions:
            model_permissions = self.get_model_permissions(
                self.model,
                self.required_model_permissions
            )
            permissions_required.extend(model_permissions)
        if self.request.user.is_superuser:
            # Superusers users are always authorized
            return True
        user_groups = self.request.user.groups.values_list("name", flat=True)
        if set(groups_required).intersection(set(user_groups)):
            return True
        for perm in permissions_required:
            if self.request.user.has_perm(perm):
                return True
        return False

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.request = request
        if not self.check_permissions():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
