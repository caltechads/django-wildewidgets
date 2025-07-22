__version__ = "1.1.7"

from .forms import *  # noqa: F403
from .menus import *  # noqa: F403
from .views import *  # noqa: F403
from .widgets import *  # noqa: F403
# WARNING: do not import .viewsets here, because it required Django to be
# fully initialized.  That makes it impossible to build the docs.
