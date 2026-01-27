from __future__ import annotations

from netbox.plugins import PluginMenu, PluginMenuItem, PluginMenuButton


menu_items = (
    PluginMenuItem(
        link="plugins:ruckus_r1_sync:ruckusr1tenantconfig_list",
        link_text="RUCKUS One Configs",
        buttons=(
            PluginMenuButton(
                link="plugins:ruckus_r1_sync:ruckusr1tenantconfig_add",
                title="Add",
                icon_class="icon-ruckus-dog",
            ),
        ),
    ),
)

menu = PluginMenu(
    label="RUCKUS One Sync",
    groups=(("RUCKUS One", menu_items),),
    icon_class="icon-ruckus-dog",
)
 