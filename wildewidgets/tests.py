from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from .widgets.base import Block
from .widgets.modals import OffcanvasWidget


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
