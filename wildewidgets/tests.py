from types import SimpleNamespace

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path

from .widgets.base import Block
from .widgets.modals import OffcanvasWidget
from .widgets.tables.actions import RowDjangoUrlButton


def _edit_book_view(_request, pk: int) -> HttpResponse:
    """Minimal view used only for URL reversing in unit tests."""
    return HttpResponse(str(pk))


urlpatterns = [
    path("book/<int:pk>/edit/", _edit_book_view, name="edit_book"),
]


@override_settings(ROOT_URLCONF="wildewidgets.tests")
class RowDjangoUrlButtonTest(SimpleTestCase):
    """
    Tests for :py:class:`~wildewidgets.widgets.tables.actions.RowDjangoUrlButton`.
    """

    def test_get_url_with_url_args(self) -> None:
        """
        Reverse a named URL using positional args taken from the row.
        """
        button = RowDjangoUrlButton(
            text="Edit",
            url_path="edit_book",
            url_args=["pk"],
        )
        row = SimpleNamespace(pk=42)

        self.assertEqual(button.get_url(row), "/book/42/edit/")

    def test_get_url_with_url_kwargs(self) -> None:
        """
        Reverse a named URL using keyword args taken from the row.
        """
        button = RowDjangoUrlButton(
            text="Edit",
            url_path="edit_book",
            url_kwargs={"pk": "id"},
        )
        row = SimpleNamespace(id=7)

        self.assertEqual(button.get_url(row), "/book/7/edit/")


class OffcanvasWidgetTest(TestCase):
    """
    Tests for the Bootstrap offcanvas widget.
    """

    def test_renders_offcanvas_with_widget_body(self) -> None:
        """
        Render the Bootstrap offcanvas structure and supplied body widget.
        """
        widget = OffcanvasWidget(
            offcanvas_id="filters",
            offcanvas_title="Filters",
            widget=Block("Body"),
        )

        html = widget.get_content()

        self.assertIn('class="offcanvas offcanvas-start"', html)
        self.assertIn('data-bs-scroll="false"', html)
        self.assertIn('data-bs-backdrop="true"', html)
        self.assertIn('id="filters"', html)
        self.assertIn('aria-labelledby="filtersLabel"', html)
        self.assertIn('id="filtersLabel">Filters</h5>', html)
        self.assertIn('data-bs-dismiss="offcanvas"', html)
        self.assertIn("Body", html)

    def test_renders_scroll_and_backdrop_options(self) -> None:
        """
        Render configured Bootstrap offcanvas scroll and backdrop options.
        """
        widget = OffcanvasWidget(
            offcanvas_id="filters",
            offcanvas_title="Filters",
            widget=Block("Body"),
            scroll=True,
            backdrop=False,
        )

        html = widget.get_content()

        self.assertIn('data-bs-scroll="true"', html)
        self.assertIn('data-bs-backdrop="false"', html)

    def test_requires_offcanvas_id(self) -> None:
        """
        Raise ImproperlyConfigured when no offcanvas id is supplied.
        """
        with self.assertRaises(ImproperlyConfigured):  # noqa: PT027
            OffcanvasWidget(offcanvas_title="Filters", widget=Block("Body"))

    def test_requires_offcanvas_title(self) -> None:
        """
        Raise ImproperlyConfigured when no offcanvas title is supplied.
        """
        with self.assertRaises(ImproperlyConfigured):  # noqa: PT027
            OffcanvasWidget(offcanvas_id="filters", widget=Block("Body"))

    def test_requires_widget(self) -> None:
        """
        Raise ImproperlyConfigured when no body widget is supplied.
        """
        with self.assertRaises(ImproperlyConfigured):  # noqa: PT027
            OffcanvasWidget(offcanvas_id="filters", offcanvas_title="Filters")
