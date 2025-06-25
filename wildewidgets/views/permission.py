"""
Generic view permission mixins
------------------------------

Here we put the classes that derive from
:py:class:`braces.views._access.AccessMixin` because ``AccessMixin` needs Django
to be fully booted in order to be importable.  This is because the module that
``AccessAdmin`` is in imports some things from ``django.contrib.auth`` that want
to load app configs, which aren't available until after django has fully booted.

For the same reason, don't import this file in ``wildewidgets.views.__init.py``,
because anyone importing any widget that is also a JSON view will cause
``AppRegistryNotReady`` exceptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from braces.views._access import AccessMixin
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http.request import HttpRequest


class PermissionRequiredMixin(AccessMixin):
    """
    A class-based view mixin that controls access based on user permissions and
    group membership.

    This mixin provides a flexible permission system that can authorize users based on:

    * Django group membership
    * Django permissions
    * Model-specific permissions

    Authorization Rules:

    * Django superusers are always authorized
    * Anonymous users are never authorized
    * Users in any of the groups specified by `groups_required` are authorized
    * Users with any of the permissions specified by `permissions_required` are
      authorized
    * When `model` and `required_model_permissions` are set, the mixin
      automatically checks the corresponding model permissions (e.g.,
      "app.add_model", "app.change_model")

    The mixin also provides helper methods to check specific permissions for
    common operations like viewing, creating, updating, and deleting.

    Example:
        .. code-block:: python

            from django.contrib.auth.models import User
            from django.views.generic import TemplateView
            from wildewidgets import PermissionRequiredMixin

            class StaffRequiredView(PermissionRequiredMixin, TemplateView):
                template_name = "staff_only.html"
                groups_required = ["Staff"]

            class UserModelView(PermissionRequiredMixin, TemplateView):
                template_name = "user_management.html"
                model = User
                required_model_permissions = ["view", "change"]

    """

    #: Users who are members of the named Django auth groups will be permitted
    #: access to the view, and those who are not will be denied access.
    groups_required: list[str] | None = None

    #: Users who have any of the listed Django model permissions
    #: will be permitted access to the view.
    permissions_required: list[str] | None = None

    #: Used in conjunction with :py:attr:`required_model_permissions`,
    #: this is the model we want to act on.  This should be set by our
    #: our subclass, which is why it is just a type declaration here.
    #: This is used by :py:meth:`get_model_permissions`
    model: type[Model] | None
    #: A list of simple strings like ``view``, ``add``, ``change``, ``delete`` that
    #: represent actions that can be done on a model.  This is used by
    #: py:meth:`get_model_permissions`
    required_model_permissions: list[str] | None = None

    def user_can_view(self) -> bool:
        """
        Check if the current user has permission to view the model.

        This is a convenience method that checks for the "view" model permission.

        Returns:
            bool: True if the user has view permission, False otherwise

        Raises:
            ImproperlyConfigured: If `model` is not set

        """
        required_perms = self.get_model_permissions(self.model, ["view"])
        return self.check_permissions(
            groups_required=[], permissions_required=required_perms
        )

    def user_can_create(self) -> bool:
        """
        Check if the current user has permission to create instances of the model.

        This is a convenience method that checks for the "add" model permission.

        Returns:
            bool: True if the user has create permission, False otherwise

        Raises:
            ImproperlyConfigured: If `model` is not set

        """
        required_perms = self.get_model_permissions(self.model, ["add"])
        return self.check_permissions(
            groups_required=[], permissions_required=required_perms
        )

    def user_can_update(self) -> bool:
        """
        Check if the current user has permission to update instances of the model.

        This is a convenience method that checks for the "change" model permission.

        Returns:
            bool: True if the user has update permission, False otherwise

        Raises:
            ImproperlyConfigured: If `model` is not set

        """
        required_perms = self.get_model_permissions(self.model, ["change"])
        return self.check_permissions(
            groups_required=[], permissions_required=required_perms
        )

    def user_can_delete(self) -> bool:
        """
        Check if the current user has permission to delete instances of the model.

        This is a convenience method that checks for the "delete" model permission.

        Returns:
            bool: True if the user has delete permission, False otherwise

        Raises:
            ImproperlyConfigured: If `model` is not set

        """
        required_perms = self.get_model_permissions(self.model, ["delete"])
        return self.check_permissions(
            groups_required=[], permissions_required=required_perms
        )

    def get_groups_required(self) -> list[Group]:
        """
        Get the list of Django Group objects required for authorization.

        This method converts the group names in :py:attr:`groups_required` to actual
        Group objects.

        Returns:
            list[Group]: List of Django Group objects that grant access

        """
        if self.groups_required is None:
            return []
        return list(Group.objects.filter(name__in=self.groups_required))

    def get_permissions_required(self) -> list[str]:
        """
        Get the list of permission strings required for authorization.

        Returns:
            list[str]: List of permission strings that grant access

        """
        if self.permissions_required is None:
            return []
        return self.permissions_required

    def get_model_permissions(
        self,
        model: Model | type[Model] | None,  # noqa: ARG002
        perms: list[str],
    ) -> list[str]:
        """
        Convert simple permission names to fully-qualified model permission strings.

        This method transforms basic permission types like "view", "add",
        "change", "delete" into fully-qualified permission strings like
        "app_label.view_modelname".

        Args:
            model: The model class (ignored - uses self.model instead)
            perms: List of basic permission types to convert

        Returns:
            list[str]: List of fully-qualified permission strings

        Raises:
            ImproperlyConfigured: If :py:attr:`model` is not set to a valid Django
                model class

        Example:
            >>> # If self.model is User from django.contrib.auth
            >>> self.get_model_permissions(None, ["add", "change"])
            ['auth.add_user', 'auth.change_user']

        """
        if self.model is None:
            msg = (
                "PermissionRequiredMixin.get_model_permissions() requires that "
                "self.model is set to a Django model class."
            )
            raise ImproperlyConfigured(msg)
        required_perms = set()
        for perm in perms:
            full_perm = (
                f"{self.model._meta.app_label}.{perm}_"
                f"{self.model._meta.object_name.lower()}"  # type: ignore[union-attr]
            )
            required_perms.add(full_perm)
        return list(required_perms)

    def check_permissions(
        self,
        groups_required: list[Group] | None = None,
        permissions_required: list[str] | None = None,
    ) -> bool:
        """
        Check if the current user is authorized based on groups and permissions.

        This is the core authorization method that implements the following logic:
        1. Superusers are always authorized
        2. If the user belongs to any required group, they are authorized
        3. If the user has any of the required permissions, they are authorized
        4. Otherwise, authorization is denied

        If model permissions are configured via `model` and
        `required_model_permissions`, they are automatically added to the
        permissions check.

        Keyword Args:
            groups_required: custom list of groups to check instead of
                :py:meth:`get_groups_required`
            permissions_required: custom list of permissions to check
                instead of :py:meth:`get_permissions_required`

        Returns:
            bool: True if the user is authorized, False otherwise

        """
        if groups_required is None:
            groups_required = self.get_groups_required()
        if permissions_required is None:
            permissions_required = self.get_permissions_required()
        if self.required_model_permissions:
            model_permissions = self.get_model_permissions(
                self.model, self.required_model_permissions
            )
            permissions_required.extend(model_permissions)
        if self.request.user.is_superuser:  # type: ignore[union-attr]
            # Superusers users are always authorized
            return True
        user_groups = self.request.user.groups.values_list("name", flat=True)  # type: ignore[union-attr]
        if set(groups_required).intersection(set(user_groups)):
            return True
        return any(self.request.user.has_perm(perm) for perm in permissions_required)  # type: ignore[union-attr]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """
        Process the request and enforce permission checks.

        This method intercepts all requests to the view and checks if the user
        has the required permissions before allowing the request to proceed.

        Args:
            request: The HTTP request
            *args: Positional arguments to pass to the handler

        Keyword Arguments:kk
            **kwargs: Keyword arguments to pass to the handler

        Returns:
            Any: The response from the view

        Raises:
            PermissionDenied: If the user doesn't have the required permissions

        """
        self.request = request
        if not self.check_permissions():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
