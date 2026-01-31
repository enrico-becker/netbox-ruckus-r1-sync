## ruckus_r1_sync/api/serializers.py  
Defines REST serializers for NetBox API integration.  

- **RuckusR1TenantConfigSerializer**  
  - Serializes tenant-specific sync settings.  
  - Exposes sync toggles and behavior flags.  

```python
class RuckusR1TenantConfigSerializer(NetBoxModelSerializer):
    class Meta:
        model = RuckusR1TenantConfig
        fields = [
            "id","url","display","created","last_updated",
            "tenant","name","api_base_url","ruckus_tenant_id",
            "client_id","client_secret","enabled",
            "sync_wlans","sync_vlans","sync_aps","sync_switches",
            # …more toggles and flags…
            "last_sync","last_sync_status","last_sync_message",
        ]
```  

- **RuckusR1SyncLogSerializer**  
  - Captures metrics and status for each sync run.  
  - Fields include counts of devices, interfaces, vlans, etc.  

- **RuckusR1ClientSerializer**  
  - Exposes per-client data imported from RUCKUS One.  
  - Fields: MAC, IP, hostname, VLAN, venue/network IDs.  


## ruckus_r1_sync/api/urls.py  
Registers API endpoints with NetBox’s router.  

```python
router.register("tenant-configs", RuckusR1TenantConfigViewSet)
router.register("sync-logs",   RuckusR1SyncLogViewSet)
router.register("clients",     RuckusR1ClientViewSet)

urlpatterns = router.urls
```  

Each route maps to its corresponding ViewSet for CRUD operations.


## ruckus_r1_sync/api/views.py  
Implements DRF viewsets extending NetBoxModelViewSet.  

- **RuckusR1TenantConfigViewSet**  
- **RuckusR1SyncLogViewSet**  
- **RuckusR1ClientViewSet**  

Each viewset sets `queryset` and `serializer_class` to link models, serializers and API routes.


## ruckus_r1_sync/management/commands/ruckus_sync.py  
Provides Django management command to trigger sync.  

- Options:  
  - `--tenant-id <id>`: sync a single tenant.  
  - `--all`: sync all enabled configs.  

- Workflow:  
  1. Validate arguments.  
  2. Fetch matching RuckusR1TenantConfig records.  
  3. Call `run_sync_for_tenantconfig` for each.  
  4. Report success or raise errors.  


## Database Migrations  
Defines schema evolution from initial plugin install to advanced features.  

### 0001_initial.py  
Creates three models:  
| Model                 | Key Fields                             |
|-----------------------|----------------------------------------|
| RuckusR1TenantConfig  | tenant (OneToOne), API creds, toggles  |
| RuckusR1SyncLog       | fields for counts, status, timestamps  |
| RuckusR1Client        | tenant FK, mac, ip, hostname, raw data |

  
### 0002_add_custom_field_data.py  
Adds `custom_field_data` JSONField to all three models.  

### 0003_add_message_to_synclog.py  
Adds `started` and `finished` timestamp columns to SyncLog via raw SQL.  

### 0004_rename_client_fields.py  
Renames `ip` → `ip_address` and `ap_serial` → `ruckus_id` on RuckusR1Client.  

### 0005_client_venue_network_defaults.py  
Ensures `venue_id` and `network_id` default to empty strings.  

### 0006_sync_toggles.py  
Adds boolean fields for each sync step (wlans, aps, switches, etc.) to TenantConfig.  

### 0007_add_venue_mapping_fields.py  
Introduces Venue mapping mode:  
- `sites`  
- `locations`  
- `both`  

Also adds child-location name and parent-site FK.  

### 0008_add_venue_roadmap_fields.py  
Caches venue metadata in JSON fields:  
- `venues_cache`  
- `venues_selected`  


## ruckus_r1_sync/static/ruckus_r1_sync/dual_list_selector.js  
Implements the Dual-List selector widget behavior.  

```js
// Moves items between ‘available’ and ‘selected’ lists.
// Hooks into form’s SelectMultiple fields.
// Enables filtering and ordering.
```

Enhances venue selection UI in TenantConfig form.


## Templates  

### inc/config_actions.html  
Renders table row action buttons: View, Edit, Delete.  

```html
<div class="btn-group btn-group-sm">
  <a class="btn btn-primary" href="{% url ... view %}">View</a>
  <a class="btn btn-warning" href="{% url ... edit %}">Edit</a>
  <a class="btn btn-danger" href="{% url ... delete %}">Delete</a>
</div>
```

### inc/run_button.html  
Displays a “Run Sync” button on object view pages.  

```html
<form method="post" action="{% url ... run %}">
  {% csrf_token %}
  <button class="btn btn-success">Run Sync</button>
</form>
```

### widgets/dual_list_selector.html  
Custom widget template for two-list multi-select.  

```html
<div class="dual-list">
  <select multiple name="{{ widget.name }}" id="{{ widget.id }}_to">
    {% for option in widget.optgroups %}
      <option value="{{ option.0 }}">{{ option.1 }}</option>
    {% endfor %}
  </select>
  <!-- Buttons to move items -->
</div>
```

### ruckusr1tenantconfig.html  
Detail view for a TenantConfig. Shows grouped object fields.  

### sync_dashboard.html  
Landing page listing all TenantConfigs with status and actions.  

### sync_logs.html  
Lists recent sync runs in a table.  

### tenantconfig_view.html  
Alternate object view template combining details and action buttons.  


## ruckus_r1_sync/admin.py  
Integrates models into Django admin.  

- Registers all three models.  
- Configures `list_display` and `search_fields` for easy filtering.  


## ruckus_r1_sync/filters.py  
Defines filter sets for NetBox UI tables.  

- **SyncLogFilterSet**: filter by `status` and `tenant`.  
- **TenantConfigFilterSet**: filter by `tenant` name and `enabled` flag.  


## ruckus_r1_sync/forms.py  
Custom forms for TenantConfig editing.  

- **RuckusR1TenantConfigForm** extends `NetBoxModelForm`.  
  - Dynamically adjusts choices for `api_base_url`.  
  - Populates `venues_selected` from cache.  
  - Validates mapping mode + required fields.  

- **DualListSelectorWidget**  
  - Renders two-list UI for venue selection.  


## ruckus_r1_sync/jobs.py  
Defines a NetBox Job for bulk sync.  

- **RuckusFullSyncJob**  
  - Iterates all TenantConfig records.  
  - Calls `run_sync_for_tenantconfig` per config.  
  - Returns counts of successes/failures.  


## ruckus_r1_sync/mapping.py  
Maps a RUCKUS venue into NetBox Site/Location.  

- Determines slug, parent relationships, and device site/location.  
- Returns a `VenueMapping` object (site + location references).  


## ruckus_r1_sync/models.py  
Core ORM definitions:  

- **RuckusR1TenantConfig**  
  - Stores API credentials, sync toggles, mapping mode, venue cache/selection, default values for DCIM objects.  
- **RuckusR1SyncLog**  
  - Logs metrics and statuses per sync run.  
- **RuckusR1Client**  
  - Persists client device data imported from RUCKUS One.  


## ruckus_r1_sync/navigation.py  
Adds plugin entries to NetBox side navigation.  

- Creates “RUCKUS One Sync” menu with a button to add new configs.  


## ruckus_r1_sync/plugin.py  
Empty stub. NetBox 4.5 discovers PluginConfig in `__init__.py`.  


## ruckus_r1_sync/ruckus_api.py  
OAuth2 client for RUCKUS One REST API.  

- Handles token requests against `${region}.ruckus.cloud/oauth2/token`.  
- Exposes `query_all`, `get`, `post`, etc., with automatic paging.  
- Manages token caching/refresh.  


## ruckus_r1_sync/sync.py  
Contains the main sync orchestrator:  

- **run_sync_for_tenantconfig**  
  1. Build API client (`_make_client`).  
  2. Start a SyncLog entry (`_sync_log_start`).  
  3. Query venues, apply selection filter.  
  4. For each venue:  
     - Map to NetBox site/location.  
     - Sync APs, switches, interfaces, VLANs, clients, cabling, wireless links.  
     - Update counts.  
  5. Commit Transaction, update TenantConfig status.  
  6. Finalize SyncLog (`_sync_log_finish`).  

- Helper functions handle data transformations, DCIM upserts, error handling, capacity parsing, etc.  


## ruckus_r1_sync/tables.py  
Defines table layouts for NetBox views:  

- **RuckusR1TenantConfigTable**  
- **RuckusR1SyncLogTable**  
- **RuckusR1ClientTable**  

Columns map to model fields; linkify/view actions are configured.  


## ruckus_r1_sync/tasks.py  
Provides UI tables for NetBox’s Job scheduling interface.  

- Adds action buttons next to each TenantConfig.  


## ruckus_r1_sync/template_extensions.py  
Injects custom CSS via a plugin template extension.  

- Adds `icons.css` to all NetBox pages.  


## ruckus_r1_sync/urls.py  
Defines web UI routes under `/plugins/ruckus_r1_sync/`:  

- TenantConfig list, add, edit, view, delete, changelog, run, refresh venues  
- SyncLog list  
- Client list  


## ruckus_r1_sync/views.py  
Implements Django class-based views for the plugin:  

- **ObjectListView** for TenantConfig, SyncLog, Client  
- **ObjectView/Edit/DeleteView** for TenantConfig  
- **RunView** triggers sync via POST  
- **RefreshVenuesView** updates venue cache without syncing  

These views tie together forms, tables, models, and sync logic to deliver a seamless UI.