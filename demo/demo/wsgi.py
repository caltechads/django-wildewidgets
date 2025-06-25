"""
WSGI config for demo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# This allows easy placement of apps within the interior demo directory.
app_path = os.path.abspath(  # noqa: PTH100
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)  # noqa: PTH100, PTH118, PTH120
)
sys.path.append(os.path.join(app_path, "demo"))  # noqa: PTH118

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")

# This application object is used by any WSGI server configured to use this file.
application = get_wsgi_application()

# Apply WSGI middleware here.
