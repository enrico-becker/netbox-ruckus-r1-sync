from django.templatetags.static import static
from django.utils.safestring import mark_safe

# NetBox 4.x Template Extension base class
try:
    # NetBox 4.x
    from netbox.plugins import PluginTemplateExtension
except ImportError:
    # Fallback (older NetBox)
    from extras.plugins import PluginTemplateExtension


class RuckusGlobalStyles(PluginTemplateExtension):
    """
    Inject a global stylesheet link into the <head> of all pages.
    """

    def head(self):
        href = static("ruckus_r1_sync/css/icons.css")
        return mark_safe(f'<link rel="stylesheet" href="{href}">')


template_extensions = [RuckusGlobalStyles]
