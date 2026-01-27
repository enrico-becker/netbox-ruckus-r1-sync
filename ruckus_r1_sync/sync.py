# ruckus_r1_sync/sync.py
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, SiteGroup
from ipam.models import IPAddress, VLAN
from wireless.models import WirelessLAN

from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client as RuckusR1ClientModel
from .ruckus_api import RuckusR1Client
from .mapping import map_venue_to_netbox, VenueMapping


# -----------------
# Generic helpers
# -----------------

def _now() -> datetime.datetime:
    return timezone.now()


def _nb_model(app_label: str, model_name: str):
    return apps.get_model(app_label, model_name)


def _safe_str(x: Any, max_len: int = 4000) -> str:
    s = "" if x is None else str(x)
    return (s[: max_len - 3] + "...") if len(s) > max_len else s


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", ".", "/"):
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:100] or "ruckus"


def _normalize_base_url(url: str) -> str:
    url = (url or "").strip()
    return url.rstrip("/") if url else url


def _cfg_flag(cfg: RuckusR1TenantConfig, field: str, default: bool = True) -> bool:
    """
    Backwards-compatible feature flag access.
    If the DB/model doesn't have the field yet, we fall back to `default`.
    This prevents the sync from crashing while you're still adding migrations/UI.
    """
    try:
        return bool(getattr(cfg, field))
    except Exception:
        return bool(default)


def _plugin_cfg(key: str, default: Any = None) -> Any:
    """
    Read plugin config from configurations/plugins.py:
      settings.PLUGINS_CONFIG["ruckus_r1_sync"][key]
    """
    try:
        pcfg = getattr(settings, "PLUGINS_CONFIG", {}) or {}
        mine = pcfg.get("ruckus_r1_sync", {}) or {}
        return mine.get(key, default)
    except Exception:
        return default


def _looks_like_mac(s: str) -> bool:
    s = (s or "").strip().lower()
    if len(s) == 17 and s.count(":") == 5 and all(c in "0123456789abcdef:" for c in s):
        return True
    if len(s) == 12 and all(c in "0123456789abcdef" for c in s):
        return True
    return False


def _norm_mac(s: str) -> str:
    s = (s or "").strip().lower()
    if len(s) == 12 and all(c in "0123456789abcdef" for c in s):
        return ":".join([s[i:i + 2] for i in range(0, 12, 2)])
    return s


def _mac_to_serial(mac: str) -> str:
    mac = _norm_mac(mac)
    return mac.replace(":", "")[:50]


def _resolve_config(cfg_or_id: Union[RuckusR1TenantConfig, int]) -> RuckusR1TenantConfig:
    if isinstance(cfg_or_id, RuckusR1TenantConfig):
        return cfg_or_id
    if not isinstance(cfg_or_id, int):
        raise TypeError(f"cfg_or_id must be RuckusR1TenantConfig or int, got {type(cfg_or_id)}")

    cfg = RuckusR1TenantConfig.objects.filter(pk=cfg_or_id).first()
    if cfg:
        return cfg
    cfg = RuckusR1TenantConfig.objects.filter(tenant_id=cfg_or_id).first()
    if cfg:
        return cfg
    raise RuckusR1TenantConfig.DoesNotExist(
        f"No RuckusR1TenantConfig found for config_id={cfg_or_id} or tenant_id={cfg_or_id}"
    )


def _make_client(cfg: RuckusR1TenantConfig) -> RuckusR1Client:
    verify_tls = bool(_plugin_cfg("verify_tls", True))
    timeout = int(_plugin_cfg("request_timeout", 30))
    return RuckusR1Client(
        base_url=_normalize_base_url(cfg.api_base_url),
        ruckus_tenant_id=cfg.ruckus_tenant_id,
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
        verify_tls=verify_tls,
        timeout=timeout,
    )


def _device_role_field_name() -> str:
    fields = {f.name for f in Device._meta.get_fields()}
    return "role" if "role" in fields else ("device_role" if "device_role" in fields else "role")


# -----------------
# Sync log
# -----------------

def _sync_log_start(cfg: RuckusR1TenantConfig) -> RuckusR1SyncLog:
    return RuckusR1SyncLog.objects.create(
        tenant=cfg.tenant,
        status="running",
        summary="running",
        message="",
        error="",
        started=_now(),
        finished=None,
        venues=0,
        networks=0,
        devices=0,
        interfaces=0,
        macs=0,
        vlans=0,
        ips=0,
        wlans=0,
        wlan_groups=0,
        tunnels=0,
        cables=0,
        clients=0,
        custom_field_data={},
    )


def _sync_log_finish(log: RuckusR1SyncLog, status: str, summary: str, message: str = "", error: str = "") -> None:
    log.status = (status or "unknown").lower()
    log.summary = _safe_str(summary, 4000)
    log.message = _safe_str(message, 4000)
    log.error = _safe_str(error, 20000)
    log.finished = _now()
    log.save()


# -----------------
# NetBox object upserts
# -----------------

def _get_or_create_site_group(cfg: RuckusR1TenantConfig) -> Optional[SiteGroup]:
    name = (cfg.default_site_group or "").strip()
    if not name:
        return None
    slug = _slugify(name)
    obj, _ = SiteGroup.objects.get_or_create(slug=slug, defaults={"name": name})
    if obj.name != name:
        obj.name = name
        obj.save()
    return obj


def _get_or_create_role(name: str) -> DeviceRole:
    name = (name or "Unknown").strip()
    slug = _slugify(name)
    obj = DeviceRole.objects.filter(slug=slug).first()
    if not obj:
        obj = DeviceRole.objects.create(name=name[:50], slug=slug, color="9e9e9e")
    return obj


def _get_or_create_manufacturer_named(name: str) -> Manufacturer:
    name = (name or "Unknown").strip()
    slug = _slugify(name)
    obj = Manufacturer.objects.filter(slug=slug).first()
    if not obj:
        obj = Manufacturer.objects.create(name=name[:50], slug=slug)
    else:
        if obj.name != name[:50]:
            obj.name = name[:50]
            obj.save()
    return obj


def _get_or_create_ruckus_manufacturer() -> Manufacturer:
    return _get_or_create_manufacturer_named("RUCKUS Networks")


def _get_or_create_devicetype(manu: Manufacturer, model: str) -> DeviceType:
    model = (model or "Generic").strip()
    slug = _slugify(f"{manu.slug}-{model}")[:100]
    obj = DeviceType.objects.filter(slug=slug, manufacturer=manu).first()
    if not obj:
        obj = DeviceType.objects.create(manufacturer=manu, model=model[:100], slug=slug)
    return obj


def _set_device_role_attr(device: Device, role: DeviceRole) -> bool:
    fn = _device_role_field_name()
    current = getattr(device, fn, None)
    if current and getattr(current, "id", None) == role.id:
        return False
    setattr(device, fn, role)
    return True


def _set_device_location_best_effort(device: Device, location) -> bool:
    """
    location is optional; only set if the field exists (it does in NetBox 4.x).
    """
    if not hasattr(device, "location"):
        return False
    current = getattr(device, "location", None)
    if (current and location and current.id == location.id) or (current is None and location is None):
        return False
    device.location = location
    return True


def _get_or_create_device_infra(
    cfg: RuckusR1TenantConfig,
    site: Site,
    location,
    role_name: str,
    model: str,
    name: str,
    serial: str = "",
) -> Device:
    role = _get_or_create_role(role_name or cfg.default_device_role or "Device")
    manu = _get_or_create_ruckus_manufacturer()
    dtype = _get_or_create_devicetype(manu, model or "Generic")

    name = (name or serial or "device").strip()[:64]
    serial = (serial or "").strip()[:50]

    obj = Device.objects.filter(serial=serial).first() if serial else None
    if not obj:
        obj = Device.objects.filter(site=site, name=name).first()

    if not obj:
        kwargs = {
            "name": name,
            "site": site,
            "tenant": cfg.tenant,
            "device_type": dtype,
            "serial": serial,
            "status": "active",
        }
        kwargs[_device_role_field_name()] = role
        obj = Device.objects.create(**kwargs)
        _set_device_location_best_effort(obj, location)
        if hasattr(obj, "location") and obj.location_id != (getattr(location, "id", None) if location else None):
            obj.save()
        return obj

    changed = False
    if obj.tenant_id != cfg.tenant_id:
        obj.tenant = cfg.tenant
        changed = True
    if obj.site_id != site.id:
        obj.site = site
        changed = True
    if obj.device_type_id != dtype.id:
        obj.device_type = dtype
        changed = True
    if serial and obj.serial != serial:
        obj.serial = serial
        changed = True
    if serial and name and obj.name != name:
        obj.name = name
        changed = True
    if _set_device_role_attr(obj, role):
        changed = True
    if _set_device_location_best_effort(obj, location):
        changed = True

    if changed:
        obj.save()
    return obj


def _get_or_create_wlan(cfg: RuckusR1TenantConfig, ssid: str) -> Optional[WirelessLAN]:
    ssid = (ssid or "").strip()
    if not ssid:
        return None
    obj = WirelessLAN.objects.filter(tenant=cfg.tenant, ssid=ssid).first()
    if not obj:
        obj = WirelessLAN.objects.create(tenant=cfg.tenant, ssid=ssid[:64], status="active", auth_type="open")
    return obj


def _upsert_ip(cfg: RuckusR1TenantConfig, ip: str) -> Optional[IPAddress]:
    ip = (ip or "").strip()
    if not ip:
        return None
    if "/" not in ip:
        ip = f"{ip}/128" if ":" in ip else f"{ip}/32"
    obj = IPAddress.objects.filter(address=ip, tenant=cfg.tenant).first()
    if not obj:
        obj = IPAddress.objects.create(address=ip, tenant=cfg.tenant, status="active")
    return obj


def _upsert_vlan(cfg: RuckusR1TenantConfig, site: Site, vid: int, name: str = "") -> Optional[VLAN]:
    """
    Create/update NetBox VLANs.
    - We scope VLANs to the Site (because in many R1 deployments VLAN IDs repeat across venues).
    - If your NetBox uses global VLANs instead, remove `site=site` from the filters.
    """
    try:
        vid = int(vid)
    except Exception:
        return None
    if vid <= 0 or vid > 4094:
        return None

    name = (name or f"VLAN {vid}").strip()[:64]

    qs = VLAN.objects.filter(tenant=cfg.tenant, vid=vid)
    if "site" in {f.name for f in VLAN._meta.get_fields()}:
        qs = qs.filter(site=site)

    obj = qs.first()
    if not obj:
        kwargs = {"tenant": cfg.tenant, "vid": vid, "name": name}
        if "site" in {f.name for f in VLAN._meta.get_fields()}:
            kwargs["site"] = site
        obj = VLAN.objects.create(**kwargs)
        return obj

    changed = False
    if obj.name != name:
        obj.name = name
        changed = True
    if hasattr(obj, "tenant_id") and obj.tenant_id != cfg.tenant_id:
        obj.tenant = cfg.tenant
        changed = True
    if "site" in {f.name for f in VLAN._meta.get_fields()} and obj.site_id != site.id:
        obj.site = site
        changed = True
    if changed:
        obj.save()
    return obj


# -----------------
# Interface / IP assignment helpers
# -----------------

def _ensure_interface(device: Device, name: str):
    Interface = _nb_model("dcim", "Interface")
    iface = Interface.objects.filter(device=device, name=name).first()
    if not iface:
        iface = Interface(device=device, name=name)
        iface.save()
    return iface


def _assign_ip_to_interface_best_effort(ip_obj: IPAddress, iface) -> None:
    if hasattr(ip_obj, "assigned_object"):
        try:
            ip_obj.assigned_object = iface
            ip_obj.save()
            return
        except Exception:
            pass

    if hasattr(ip_obj, "interface"):
        try:
            ip_obj.interface = iface
            ip_obj.save()
            return
        except Exception:
            pass


def _set_primary_ip4_best_effort(device: Device, ip_obj: IPAddress) -> None:
    if hasattr(device, "primary_ip4_id"):
        try:
            if device.primary_ip4_id != ip_obj.id:
                device.primary_ip4 = ip_obj
                device.save()
        except Exception:
            pass


def _upsert_client_as_dcim_device(
    cfg: RuckusR1TenantConfig,
    site: Site,
    location,
    cl: Dict[str, Any]
) -> Tuple[Optional[Device], Optional[IPAddress]]:
    mac = _norm_mac(cl.get("macAddress") or cl.get("mac") or cl.get("clientMac") or "")
    if not _looks_like_mac(mac):
        return (None, None)

    serial = _mac_to_serial(mac)
    role = _get_or_create_role("Wireless Client")

    manu = _get_or_create_manufacturer_named("Client")
    model = (cl.get("deviceType") or cl.get("modelName") or "Client").strip()
    dtype = _get_or_create_devicetype(manu, model)

    raw_hostname = (cl.get("hostname") or "").strip()
    host_part = ""
    if raw_hostname and not _looks_like_mac(raw_hostname):
        host_part = _slugify(raw_hostname)[:20]

    name = f"CL-{host_part + '-' if host_part else ''}{serial[:12]}"

    obj = Device.objects.filter(serial=serial).first()

    if not obj:
        kwargs = {
            "name": name[:64],
            "site": site,
            "tenant": cfg.tenant,
            "device_type": dtype,
            "serial": serial,
            "status": "active",
        }
        kwargs[_device_role_field_name()] = role
        obj = Device.objects.create(**kwargs)
        _set_device_location_best_effort(obj, location)
        if hasattr(obj, "location"):
            obj.save()
    else:
        changed = False
        if obj.tenant_id != cfg.tenant_id:
            obj.tenant = cfg.tenant
            changed = True
        if obj.site_id != site.id:
            obj.site = site
            changed = True
        if obj.device_type_id != dtype.id:
            obj.device_type = dtype
            changed = True
        if obj.serial != serial:
            obj.serial = serial
            changed = True

        if not obj.name or obj.name.lower() in ("wlan0", "unknown", "client"):
            obj.name = name[:64]
            changed = True

        if hasattr(obj, "description"):
            desired_desc = f"R1 Client hostname={raw_hostname}" if raw_hostname else "R1 Client"
            if (obj.description or "") != desired_desc[:200]:
                obj.description = desired_desc[:200]
                changed = True

        if _set_device_role_attr(obj, role):
            changed = True

        if _set_device_location_best_effort(obj, location):
            changed = True

        if changed:
            obj.save()

    iface = _ensure_interface(obj, "wlan0")
    if hasattr(iface, "mac_address"):
        try:
            if (iface.mac_address or "").lower() != mac:
                iface.mac_address = mac
                iface.save()
        except Exception:
            pass

    ip = (cl.get("ipAddress") or cl.get("ip") or "").strip()
    ip_obj = None
    if ip and ":" not in ip:
        ip_obj = _upsert_ip(cfg, ip)
        if ip_obj:
            _assign_ip_to_interface_best_effort(ip_obj, iface)
            _set_primary_ip4_best_effort(obj, ip_obj)

    return (obj, ip_obj)


def _upsert_wired_client_as_dcim_device(
    cfg: RuckusR1TenantConfig,
    site: Site,
    location,
    cl: Dict[str, Any],
    *,
    iface_name: str = "eth0",
) -> Tuple[Optional[Device], Optional[IPAddress]]:
    mac = _norm_mac(cl.get("macAddress") or cl.get("mac") or cl.get("clientMac") or cl.get("deviceMac") or "")
    if not _looks_like_mac(mac):
        return (None, None)

    serial = _mac_to_serial(mac)
    role = _get_or_create_role("Wired Client")

    manu = _get_or_create_manufacturer_named("Client")
    model = (cl.get("deviceType") or cl.get("modelName") or cl.get("manufacturer") or "Client").strip()
    dtype = _get_or_create_devicetype(manu, model)

    raw_name = (cl.get("hostname") or cl.get("name") or "").strip()
    host_part = ""
    if raw_name and not _looks_like_mac(raw_name):
        host_part = _slugify(raw_name)[:20]

    name = f"CL-W-{host_part + '-' if host_part else ''}{serial[:12]}"

    obj = Device.objects.filter(serial=serial).first()
    if not obj:
        kwargs = {
            "name": name[:64],
            "site": site,
            "tenant": cfg.tenant,
            "device_type": dtype,
            "serial": serial,
            "status": "active",
        }
        kwargs[_device_role_field_name()] = role
        obj = Device.objects.create(**kwargs)
        _set_device_location_best_effort(obj, location)
        if hasattr(obj, "location"):
            obj.save()
    else:
        changed = False
        if obj.tenant_id != cfg.tenant_id:
            obj.tenant = cfg.tenant
            changed = True
        if obj.site_id != site.id:
            obj.site = site
            changed = True
        if obj.device_type_id != dtype.id:
            obj.device_type = dtype
            changed = True
        if _set_device_role_attr(obj, role):
            changed = True
        if not obj.name or obj.name.lower() in ("unknown", "client"):
            obj.name = name[:64]
            changed = True
        if hasattr(obj, "description"):
            vlan = cl.get("vlan") or cl.get("vlanId") or cl.get("vlanIds")
            desired_desc = f"R1 Wired Client vlan={vlan}" if vlan else "R1 Wired Client"
            if (obj.description or "") != desired_desc[:200]:
                obj.description = desired_desc[:200]
                changed = True
        if _set_device_location_best_effort(obj, location):
            changed = True
        if changed:
            obj.save()

    iface = _ensure_interface(obj, iface_name)
    if hasattr(iface, "mac_address"):
        try:
            if (iface.mac_address or "").lower() != mac:
                iface.mac_address = mac
                iface.save()
        except Exception:
            pass

    ip = (cl.get("ipAddress") or cl.get("ip") or "").strip()
    ip_obj = None
    if ip and ":" not in ip:
        ip_obj = _upsert_ip(cfg, ip)
        if ip_obj:
            _assign_ip_to_interface_best_effort(ip_obj, iface)
            _set_primary_ip4_best_effort(obj, ip_obj)

    return (obj, ip_obj)


# -----------------
# API query adapter
# -----------------

def _query_all(
    api: RuckusR1Client,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    *,
    data_key: str = "data",
    page_size: int = 100
) -> List[Dict[str, Any]]:
    body = body or {}
    return api.query_all(path=path, page_size=page_size, extra_body=body, data_key=data_key)


# -----------------
# Topology helpers (interfaces/macs/cables/wlinks)
# -----------------

def _parse_link_speed_to_kbps(s: str) -> Optional[int]:
    if not s:
        return None
    t = s.strip().lower().replace(" ", "")
    t = t.replace("gb/sec", "g").replace("mb/sec", "m").replace("kb/sec", "k")
    try:
        if t.endswith("g"):
            return int(float(t[:-1]) * 1_000_000)
        if t.endswith("m"):
            return int(float(t[:-1]) * 1_000)
        if t.endswith("k"):
            return int(float(t[:-1]))
    except Exception:
        return None
    return None


def _capacity_to_kbps(cap: str) -> Optional[int]:
    if not cap:
        return None
    t = cap.strip().lower()
    toks: List[float] = []
    for part in t.replace("multigig", "").replace("persecond", "").replace(" ", "").split("/"):
        p = part.strip()
        if not p:
            continue
        if p.endswith("g"):
            try:
                toks.append(float(p[:-1]))
            except Exception:
                pass
        elif p.endswith("m"):
            try:
                return int(float(p[:-1]) * 1_000)
            except Exception:
                pass
    if toks:
        return int(max(toks) * 1_000_000)
    return None


def _set_interface_fields_best_effort(
    iface,
    *,
    speed_kbps: Optional[int] = None,
    poe_enabled: Optional[bool] = None,
    description: str = "",
    enabled: Optional[bool] = None,
) -> None:
    changed = False
    if enabled is not None and hasattr(iface, "enabled") and getattr(iface, "enabled", None) != enabled:
        iface.enabled = enabled
        changed = True
    if description and hasattr(iface, "description") and (iface.description or "") != description:
        iface.description = description[:200]
        changed = True
    if speed_kbps is not None and hasattr(iface, "speed") and getattr(iface, "speed", None) != speed_kbps:
        iface.speed = speed_kbps
        changed = True
    if poe_enabled is not None and hasattr(iface, "poe_mode"):
        new_mode = "pse" if poe_enabled else None
        if getattr(iface, "poe_mode", None) != new_mode:
            iface.poe_mode = new_mode
            changed = True
    if changed:
        iface.save()


def _upsert_macaddress_best_effort(iface, mac: str) -> bool:
    mac = _norm_mac(mac)
    if not _looks_like_mac(mac):
        return False

    if hasattr(iface, "mac_address"):
        if (getattr(iface, "mac_address", "") or "").lower() != mac:
            iface.mac_address = mac
            iface.save()

    try:
        MACAddress = _nb_model("dcim", "MACAddress")
    except Exception:
        return False

    obj = MACAddress.objects.filter(mac_address=mac).first()
    if not obj:
        obj = MACAddress(mac_address=mac)

    if hasattr(obj, "assigned_object"):
        try:
            obj.assigned_object = iface
        except Exception:
            pass
    if hasattr(obj, "interface"):
        try:
            obj.interface = iface
        except Exception:
            pass

    obj.save()
    return True


def _find_device_by_any_mac(cfg: RuckusR1TenantConfig, site: Site, mac: str) -> Optional[Device]:
    """
    Best-effort resolve a NetBox Device from a MAC.
    Tries:
      1) dcim.MACAddress.assigned_object -> Interface -> device
      2) dcim.Interface.mac_address match
    """
    mac = _norm_mac(mac)
    if not _looks_like_mac(mac):
        return None

    # 1) MACAddress model (NetBox >= 4)
    try:
        MACAddress = _nb_model("dcim", "MACAddress")
        mac_obj = MACAddress.objects.filter(mac_address=mac).first()
        if mac_obj:
            ao = getattr(mac_obj, "assigned_object", None)
            if ao and hasattr(ao, "device_id"):
                dev = Device.objects.filter(id=ao.device_id, tenant=cfg.tenant, site=site).first()
                if dev:
                    return dev
    except Exception:
        pass

    # 2) Interface.mac_address
    try:
        Interface = _nb_model("dcim", "Interface")
        iface = Interface.objects.filter(
            device__tenant=cfg.tenant,
            device__site=site,
            mac_address__iexact=mac,
        ).select_related("device").first()
        if iface and getattr(iface, "device", None):
            return iface.device
    except Exception:
        pass

    return None


def _cable_supports_legacy_fields(Cable) -> bool:
    fields = {f.name for f in Cable._meta.get_fields()}
    return (
        "termination_a_id" in fields and "termination_b_id" in fields
        and "termination_a_type" in fields and "termination_b_type" in fields
    )


def _cable_exists_between(a_iface, b_iface) -> bool:
    Cable = _nb_model("dcim", "Cable")
    ct_iface = ContentType.objects.get_for_model(a_iface.__class__)

    if _cable_supports_legacy_fields(Cable):
        return Cable.objects.filter(
            termination_a_type=ct_iface, termination_a_id=a_iface.id,
            termination_b_type=ct_iface, termination_b_id=b_iface.id,
        ).exists() or Cable.objects.filter(
            termination_a_type=ct_iface, termination_a_id=b_iface.id,
            termination_b_type=ct_iface, termination_b_id=a_iface.id,
        ).exists()

    CableTermination = _nb_model("dcim", "CableTermination")
    a_ids = set(
        CableTermination.objects.filter(termination_type=ct_iface, termination_id=a_iface.id)
        .values_list("cable_id", flat=True)
    )
    if not a_ids:
        return False
    b_ids = set(
        CableTermination.objects.filter(termination_type=ct_iface, termination_id=b_iface.id)
        .values_list("cable_id", flat=True)
    )
    return bool(a_ids.intersection(b_ids))


def _create_cable(a_iface, b_iface, status: str = "connected") -> bool:
    Cable = _nb_model("dcim", "Cable")
    ct_iface = ContentType.objects.get_for_model(a_iface.__class__)

    if _cable_exists_between(a_iface, b_iface):
        return False

    if _cable_supports_legacy_fields(Cable):
        kwargs = dict(
            termination_a_type=ct_iface,
            termination_a_id=a_iface.id,
            termination_b_type=ct_iface,
            termination_b_id=b_iface.id,
        )
        if "status" in {f.name for f in Cable._meta.get_fields()}:
            kwargs["status"] = status
        Cable.objects.create(**kwargs)
        return True

    CableTermination = _nb_model("dcim", "CableTermination")
    cable_kwargs = {}
    if "status" in {f.name for f in Cable._meta.get_fields()}:
        cable_kwargs["status"] = status
    cable = Cable.objects.create(**cable_kwargs)

    term_fields = {f.name for f in CableTermination._meta.get_fields()}
    a_kwargs = dict(cable=cable, termination_type=ct_iface, termination_id=a_iface.id)
    b_kwargs = dict(cable=cable, termination_type=ct_iface, termination_id=b_iface.id)
    if "cable_end" in term_fields:
        a_kwargs["cable_end"] = "A"
        b_kwargs["cable_end"] = "B"

    CableTermination.objects.create(**a_kwargs)
    CableTermination.objects.create(**b_kwargs)
    return True


def _create_wireless_link_best_effort(
    cfg: RuckusR1TenantConfig,
    a_device: Device,
    b_device: Device,
    a_mac: str,
    b_mac: str,
    *,
    ssid: str = "",
    status: str = "active",
    description: str = "",
) -> bool:
    try:
        WirelessLink = _nb_model("wireless", "WirelessLink")
    except Exception:
        return False

    a_iface = _ensure_interface(a_device, "mesh")
    b_iface = _ensure_interface(b_device, "mesh")

    if a_mac:
        _upsert_macaddress_best_effort(a_iface, a_mac)
    if b_mac:
        _upsert_macaddress_best_effort(b_iface, b_mac)

    qs = WirelessLink.objects.all()
    if qs.filter(interface_a=a_iface, interface_b=b_iface).exists():
        return False
    if qs.filter(interface_a=b_iface, interface_b=a_iface).exists():
        return False

    obj = WirelessLink(
        interface_a=a_iface,
        interface_b=b_iface,
        tenant=cfg.tenant if hasattr(WirelessLink, "tenant") else None,
    )

    if hasattr(obj, "ssid") and ssid:
        obj.ssid = ssid[:64]
    if hasattr(obj, "status") and status:
        obj.status = status
    if hasattr(obj, "description") and description:
        obj.description = description[:200]

    try:
        obj.save()
        return True
    except Exception:
        return False


# -----------------
# Switch ports + wired clients
# -----------------

def _sync_switch_ports_for_venue(cfg: RuckusR1TenantConfig, api: RuckusR1Client, site: Site, location, venue_id: str) -> Tuple[int, int, int]:
    """
    Returns: (touched_ifaces, touched_macs, touched_vlans)
    VLANs are inferred from switch port VLAN fields (vlanIds/unTaggedVlan/accessVlan/managementTrafficVlan).
    """
    touched_ifaces = 0
    touched_macs = 0
    touched_vlans = 0

    rows = _query_all(api, "/venues/switches/switchPorts/query", {"venueId": venue_id, "limit": 5000})
    if not rows:
        return (0, 0, 0)

    for p in rows:
        if not isinstance(p, dict):
            continue

        switch_unit_id = (p.get("switchUnitId") or "").strip()
        if not switch_unit_id:
            continue

        sw = Device.objects.filter(tenant=cfg.tenant, site=site, serial=switch_unit_id).first()
        if not sw and cfg.allow_stub_devices:
            sw_name = (p.get("switchName") or p.get("switchModel") or switch_unit_id).strip()
            sw_model = (p.get("switchModel") or "Switch").strip()
            sw = _get_or_create_device_infra(cfg, site, location, "Switch", sw_model, sw_name or switch_unit_id, serial=switch_unit_id)

        if not sw:
            continue

        ifname = (p.get("portIdentifier") or p.get("name") or "").strip()
        if not ifname:
            continue

        iface = _ensure_interface(sw, ifname)
        touched_ifaces += 1

        pmac = (p.get("portMac") or "").strip()
        if pmac and _upsert_macaddress_best_effort(iface, pmac):
            touched_macs += 1

        admin_status = (p.get("adminStatus") or "").strip().lower()
        admin_up = admin_status in ("up", "enabled", "true", "1")

        speed_kbps = _capacity_to_kbps(p.get("portSpeedCapacity") or "") or _parse_link_speed_to_kbps(p.get("portSpeed") or "")
        poe_enabled = p.get("poeEnabled")

        # VLAN inference
        vids: List[int] = []
        for key in ("unTaggedVlan", "accessVlan", "nativeVlan", "managementTrafficVlan"):
            v = p.get(key)
            try:
                if v is not None and str(v).strip() != "":
                    vids.append(int(str(v).strip()))
            except Exception:
                pass

        vlan_ids = p.get("vlanIds")
        if isinstance(vlan_ids, list):
            for v in vlan_ids:
                try:
                    vids.append(int(str(v).strip()))
                except Exception:
                    pass
        elif isinstance(vlan_ids, str):
            # e.g. "1,10,20"
            for part in vlan_ids.replace(";", ",").split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    vids.append(int(part))
                except Exception:
                    pass

        # Dedup + create
        for vid in sorted({v for v in vids if isinstance(v, int)}):
            if _upsert_vlan(cfg, site, vid):
                touched_vlans += 1

        desc_parts = []
        if p.get("tags"):
            desc_parts.append(str(p["tags"]))
        if p.get("neighborName"):
            desc_parts.append(f"neighbor={p['neighborName']}")
        if p.get("status"):
            desc_parts.append(f"link={p['status']}")
        if p.get("portConnectorType"):
            desc_parts.append(f"connector={p['portConnectorType']}")
        if p.get("opticsType"):
            desc_parts.append(f"media={p['opticsType']}")
        if p.get("vlanIds"):
            desc_parts.append(f"vlans={p['vlanIds']}")
        if p.get("unTaggedVlan"):
            desc_parts.append(f"untag={p['unTaggedVlan']}")

        _set_interface_fields_best_effort(
            iface,
            enabled=admin_up,
            speed_kbps=speed_kbps,
            poe_enabled=bool(poe_enabled) if poe_enabled is not None else None,
            description=" | ".join(desc_parts).strip(),
        )

    return (touched_ifaces, touched_macs, touched_vlans)


def _sync_switch_clients_for_venue(
    cfg: RuckusR1TenantConfig,
    api: RuckusR1Client,
    site: Site,
    location,
    venue_id: str
) -> Tuple[int, int, int]:
    processed_clients = 0
    touched_ifaces = 0
    touched_cables = 0

    rows = _query_all(api, "/venues/switches/clients/query", {"venueId": venue_id, "limit": 5000})
    if not rows:
        return (0, 0, 0)

    for cl in rows:
        if not isinstance(cl, dict):
            continue

        mac = _norm_mac(cl.get("macAddress") or cl.get("mac") or cl.get("clientMac") or cl.get("deviceMac") or "")
        ip = (cl.get("ipAddress") or cl.get("ip") or "").strip()
        hostname = (cl.get("hostname") or cl.get("name") or "").strip()

        vlan_raw = cl.get("vlan") or cl.get("vlanId") or cl.get("accessVlan") or None
        vlan_int: Optional[int] = None
        try:
            if vlan_raw is not None and str(vlan_raw).strip() != "":
                vlan_int = int(str(vlan_raw).strip())
        except Exception:
            vlan_int = None

        switch_unit_id = (cl.get("switchUnitId") or cl.get("switchSerialNumber") or cl.get("switchSerial") or "").strip()
        port_name = (cl.get("portIdentifier") or cl.get("port") or cl.get("connectedPort") or "").strip()

        vinfo = cl.get("venueInformation") or {}
        venue_id_effective = (vinfo.get("id") or venue_id or "").strip()

        if not _looks_like_mac(mac):
            for _, v in cl.items():
                if isinstance(v, str) and _looks_like_mac(v):
                    mac = _norm_mac(v)
                    break

        if not _looks_like_mac(mac):
            mac = "unknown"

        RuckusR1ClientModel.objects.update_or_create(
            tenant=cfg.tenant,
            mac=mac,
            defaults={
                "venue_id": venue_id_effective,
                "network_id": _safe_str(cl.get("networkId") or "", 128),
                "ruckus_id": (switch_unit_id or "")[:128],
                "ip_address": ip or "",
                "hostname": hostname or "",
                "vlan": vlan_int,
                "ssid": "",  # wired
                "last_seen": None,
                "raw": cl,
                "custom_field_data": {},
            },
        )

        client_dev = None
        client_iface = None
        if mac != "unknown":
            client_dev, _ = _upsert_wired_client_as_dcim_device(cfg, site, location, cl, iface_name="eth0")
            if client_dev:
                client_iface = _ensure_interface(client_dev, "eth0")
                touched_ifaces += 1

        if client_dev and client_iface and switch_unit_id and port_name:
            sw = Device.objects.filter(tenant=cfg.tenant, site=site, serial=switch_unit_id).first()
            if sw:
                sw_iface = _ensure_interface(sw, port_name)
                touched_ifaces += 1
                if _create_cable(sw_iface, client_iface, status="connected"):
                    touched_cables += 1

        processed_clients += 1

    return (processed_clients, touched_ifaces, touched_cables)


# -----------------
# Topology sync (wired + wireless links)
# -----------------

def _sync_topologies_for_venue(cfg: RuckusR1TenantConfig, api: RuckusR1Client, site: Site, location, venue_id: str) -> Tuple[int, int, int, int]:
    touched_ifaces = 0
    touched_macs = 0
    touched_cables = 0
    touched_wlinks = 0

    topo = api._get(f"/venues/{venue_id}/topologies")
    blob = None
    if isinstance(topo, dict):
        data = topo.get("data")
        if isinstance(data, list) and data:
            blob = data[0]
    if not isinstance(blob, dict):
        return (0, 0, 0, 0)

    nodes = blob.get("nodes") if isinstance(blob.get("nodes"), list) else []
    edges = blob.get("edges") if isinstance(blob.get("edges"), list) else []

    for n in nodes:
        if not isinstance(n, dict):
            continue
        n_type = (n.get("type") or n.get("deviceType") or "").strip().lower()
        name = (n.get("name") or "").strip()
        mac = (n.get("mac") or "").strip()
        serial = (n.get("serial") or n.get("serialNumber") or "").strip()
        ip = (n.get("ipAddress") or n.get("ip") or "").strip()
        model = (n.get("model") or "").strip()

        if "switch" in n_type:
            role = "Switch"
            model = model or "Switch"
        elif "ap" in n_type:
            role = "Access Point"
            model = model or "Access Point"
        else:
            role = "Device"
            model = model or "Device"

        dev = _get_or_create_device_infra(cfg, site, location, role, model, name or serial or mac or "device", serial=serial)

        if ip:
            _upsert_ip(cfg, ip)

        if mac:
            mgmt = _ensure_interface(dev, "mgmt")
            touched_ifaces += 1
            if _upsert_macaddress_best_effort(mgmt, mac):
                touched_macs += 1

    for e in edges:
        if not isinstance(e, dict):
            continue

        ctype = (e.get("connectionType") or "").strip().lower()
        status = (e.get("connectionStatus") or "").strip()

        from_serial = (e.get("fromSerial") or "").strip()
        to_serial = (e.get("toSerial") or "").strip()
        from_mac = (e.get("fromMac") or "").strip()
        to_mac = (e.get("toMac") or "").strip()
        from_name = (e.get("fromName") or "").strip()
        to_name = (e.get("toName") or "").strip()

        a_dev = Device.objects.filter(serial=from_serial).first() if from_serial else None
        b_dev = Device.objects.filter(serial=to_serial).first() if to_serial else None

        if not a_dev and from_mac:
            a_dev = _find_device_by_any_mac(cfg, site, from_mac)
        if not b_dev and to_mac:
            b_dev = _find_device_by_any_mac(cfg, site, to_mac)

        if not a_dev and cfg.allow_stub_devices:
            stub_serial = from_serial or (_mac_to_serial(from_mac) if _looks_like_mac(from_mac) else "")
            a_dev = _get_or_create_device_infra(cfg, site, location, "Device", "Device", from_name or stub_serial or "device", serial=stub_serial)
        if not b_dev and cfg.allow_stub_devices:
            stub_serial = to_serial or (_mac_to_serial(to_mac) if _looks_like_mac(to_mac) else "")
            b_dev = _get_or_create_device_infra(cfg, site, location, "Device", "Device", to_name or stub_serial or "device", serial=stub_serial)

        if not a_dev or not b_dev:
            continue

        if ctype == "wired":
            connected_port = (e.get("connectedPort") or "uplink").strip()
            corresponding_port = (e.get("correspondingPort") or "uplink").strip()

            a_iface = _ensure_interface(a_dev, connected_port)
            b_iface = _ensure_interface(b_dev, corresponding_port)
            touched_ifaces += 2

            speed_kbps = _parse_link_speed_to_kbps(e.get("linkSpeed") or "")
            poe_enabled = e.get("poeEnabled")

            _set_interface_fields_best_effort(
                a_iface,
                speed_kbps=speed_kbps,
                poe_enabled=bool(poe_enabled) if poe_enabled is not None else None,
                description=f"R1 topology: {status}".strip(),
            )

            if _create_cable(a_iface, b_iface, status="connected"):
                touched_cables += 1

        else:
            wireless_types = {"mesh", "wireless", "wirelessmesh", "smartmesh", "apmesh", "ap-mesh", "wireless-mesh"}
            if ctype in wireless_types or "mesh" in ctype or "wireless" in ctype:
                if _create_wireless_link_best_effort(
                    cfg,
                    a_dev,
                    b_dev,
                    from_mac,
                    to_mac,
                    ssid="",
                    status="active",
                    description=f"R1 topology: {status}".strip(),
                ):
                    touched_wlinks += 1

    return (touched_ifaces, touched_macs, touched_cables, touched_wlinks)


# -----------------
# Main sync
# -----------------

def run_sync_for_tenantconfig(cfg_or_id: Union[RuckusR1TenantConfig, int]) -> str:
    cfg = _resolve_config(cfg_or_id)
    if not cfg.enabled:
        return "Config disabled, skipping."

    do_wlans = _cfg_flag(cfg, "sync_wlans", True)
    do_aps = _cfg_flag(cfg, "sync_aps", True)
    do_switches = _cfg_flag(cfg, "sync_switches", True)
    do_interfaces = _cfg_flag(cfg, "sync_interfaces", True)
    do_wifi_clients = _cfg_flag(cfg, "sync_wifi_clients", True)
    do_wired_clients = _cfg_flag(cfg, "sync_wired_clients", True)
    do_cabling = _cfg_flag(cfg, "sync_cabling", True)
    do_wireless_links = _cfg_flag(cfg, "sync_wireless_links", True)
    do_vlans = _cfg_flag(cfg, "sync_vlans", False)

    # Mapping config (plugins.py)
    mapping_mode = str(_plugin_cfg("venue_mapping_mode", "sites")).strip().lower()
    parent_site_ref = _plugin_cfg("venue_locations_parent_site", None)
    child_location_name = str(_plugin_cfg("venue_child_location_name", "Venue"))
    slug_prefix = str(_plugin_cfg("venue_slug_prefix", "r1"))

    api = _make_client(cfg)
    log = _sync_log_start(cfg)
    started = _now()

    try:
        with transaction.atomic():
            site_group = _get_or_create_site_group(cfg)

            venues = _query_all(api, "/venues/query", {"limit": 500})
            # Venue Roadmap: Filter by selected venues (empty => all)
            selected_ids = getattr(cfg, "venues_selected", None) or []
            selected_ids = {str(x).strip() for x in selected_ids if str(x).strip()}
            if selected_ids:
                venues = [v for v in venues if str((v.get("id") or v.get("venueId") or "")).strip() in selected_ids]

            log.venues = len(venues)

            if do_wlans:
                wifi_networks = _query_all(api, "/wifiNetworks/query", {"limit": 500})
                for wn in wifi_networks:
                    ssid = (wn.get("ssid") or wn.get("name") or "").strip()
                    _get_or_create_wlan(cfg, ssid)
                log.wlans = len(wifi_networks)
            else:
                log.wlans = 0

            processed_devices = 0
            processed_ips = 0
            processed_clients = 0
            processed_ifaces = 0
            processed_macs = 0
            processed_cables = 0
            processed_wlinks = 0
            processed_vlans = 0

            for venue in venues:
                venue_id = _safe_str(venue.get("id") or venue.get("venueId") or "", 128)
                venue_name = (venue.get("name") or venue.get("venueName") or venue_id or "Venue").strip()

                mapping: VenueMapping = map_venue_to_netbox(
                    venue_id=venue_id,
                    venue_name=venue_name,
                    tenant=cfg.tenant,
                    mode=mapping_mode,
                    site_group=site_group,
                    locations_parent_site=parent_site_ref,
                    child_location_name=child_location_name,
                    slug_prefix=slug_prefix,
                )

                # Site/Location for all objects in this venue context
                site = mapping.device_site
                location = mapping.device_location

                # APs
                if do_aps:
                    aps = _query_all(api, "/venues/aps/query", {"venueId": venue_id, "limit": 1000})
                    for ap in aps:
                        name = (ap.get("name") or ap.get("apName") or ap.get("hostname") or ap.get("serial") or ap.get("serialNumber") or "").strip()
                        serial = (ap.get("serialNumber") or ap.get("serial") or ap.get("msn") or ap.get("serialNumber") or ap.get("apSerial") or ap.get("deviceSerial") or "").strip()
                        model = (ap.get("model") or ap.get("apModel") or "Access Point").strip()

                        # R1: mgmt IP typically lives under networkStatus.ipAddress
                        ns = ap.get("networkStatus") or {}
                        mgmt_ip = (ns.get("ipAddress") or ap.get("ip") or ap.get("ipAddress") or ap.get("mgmtIp") or "").strip()

                        _get_or_create_device_infra(cfg, site, location, "Access Point", model, name or serial or "AP", serial=serial)
                        processed_devices += 1

                        if mgmt_ip and _upsert_ip(cfg, mgmt_ip):
                            processed_ips += 1

                        # also create mgmt VLAN if present
                        if do_vlans:
                            try:
                                mv = ns.get("managementTrafficVlan")
                                if mv is not None and str(mv).strip() != "":
                                    if _upsert_vlan(cfg, site, int(str(mv).strip()), name=f"MGMT VLAN {mv}"):
                                        processed_vlans += 1
                            except Exception:
                                pass

                # Switches
                if do_switches:
                    switches = _query_all(api, "/venues/switches/query", {"venueId": venue_id, "limit": 1000})
                    for sw in switches:
                        name = (sw.get("name") or sw.get("switchName") or sw.get("hostname") or sw.get("serial") or sw.get("serialNumber") or "").strip()
                        serial = (sw.get("serialNumber") or sw.get("serial") or sw.get("msn") or sw.get("switchSerial") or sw.get("deviceSerial") or "").strip()
                        model = (sw.get("model") or sw.get("switchModel") or "Switch").strip()

                        ns = sw.get("networkStatus") or {}
                        mgmt_ip = (ns.get("ipAddress") or sw.get("ip") or sw.get("ipAddress") or sw.get("mgmtIp") or "").strip()

                        _get_or_create_device_infra(cfg, site, location, "Switch", model, name or serial or "Switch", serial=serial)
                        processed_devices += 1
                        if mgmt_ip and _upsert_ip(cfg, mgmt_ip):
                            processed_ips += 1

                # Switch Ports -> dcim.Interface (+ MACs) + VLAN inference
                if do_interfaces:
                    it_ports, mt_ports, vt_ports = _sync_switch_ports_for_venue(cfg, api, site, location, venue_id)
                    processed_ifaces += it_ports
                    processed_macs += mt_ports
                    if do_vlans:
                        processed_vlans += vt_ports

                # Wi-Fi Clients
                if do_wifi_clients:
                    clients = _query_all(api, "/venues/aps/clients/query", {"venueId": venue_id, "limit": 5000})
                    for cl in clients:
                        if not isinstance(cl, dict):
                            continue

                        mac = _norm_mac(cl.get("macAddress") or cl.get("mac") or cl.get("clientMac") or "")
                        ip = (cl.get("ipAddress") or cl.get("ip") or "").strip()
                        hostname = (cl.get("hostname") or "").strip()

                        netinfo = cl.get("networkInformation") or {}
                        ssid = (netinfo.get("ssid") or cl.get("ssid") or "").strip()

                        apinfo = cl.get("apInformation") or {}
                        ap_serial = (apinfo.get("serialNumber") or cl.get("apSerial") or cl.get("connectedApSerial") or "").strip()

                        vinfo = cl.get("venueInformation") or {}
                        venue_id_effective = (vinfo.get("id") or venue_id or "").strip()

                        if _looks_like_mac(hostname) and not _looks_like_mac(mac):
                            mac = _norm_mac(hostname)
                            hostname = ""
                        if _looks_like_mac(hostname):
                            hostname = ""

                        if not _looks_like_mac(mac):
                            for _, v in cl.items():
                                if isinstance(v, str) and _looks_like_mac(v):
                                    mac = _norm_mac(v)
                                    break

                        if not _looks_like_mac(mac):
                            mac = "unknown"

                        RuckusR1ClientModel.objects.update_or_create(
                            tenant=cfg.tenant,
                            mac=mac,
                            defaults={
                                "venue_id": venue_id_effective,
                                "network_id": _safe_str(netinfo.get("id") or cl.get("networkId") or "", 128),
                                "ruckus_id": ap_serial,
                                "ip_address": ip or "",
                                "hostname": hostname or "",
                                "ssid": ssid or "",
                                "last_seen": None,
                                "raw": cl,
                                "custom_field_data": {},
                            },
                        )

                        if mac != "unknown":
                            _upsert_client_as_dcim_device(cfg, site, location, cl)

                        processed_clients += 1

                # Switch Clients (wired)
                if do_wired_clients:
                    sc, it_sc, ct_sc = _sync_switch_clients_for_venue(cfg, api, site, location, venue_id)
                    processed_clients += sc
                    processed_ifaces += it_sc
                    if do_cabling:
                        processed_cables += ct_sc

                # Venue topologies (cables + wireless links)
                if do_cabling or do_wireless_links:
                    it, mt, ct, wt = _sync_topologies_for_venue(cfg, api, site, location, venue_id)
                    processed_ifaces += it
                    processed_macs += mt
                    if do_cabling:
                        processed_cables += ct
                    if do_wireless_links:
                        processed_wlinks += wt

            log.devices = processed_devices
            log.ips = processed_ips
            log.clients = processed_clients
            log.interfaces = processed_ifaces
            log.macs = processed_macs
            log.cables = processed_cables
            log.vlans = processed_vlans
            log.save()

            cfg.last_sync = _now()
            cfg.last_sync_status = "ok"
            cfg.last_sync_message = (
                f"Sync OK. venues={log.venues} wlans={log.wlans} processed_devices={log.devices} "
                f"processed_interfaces={log.interfaces} processed_macs={log.macs} processed_cables={log.cables} "
                f"processed_wlinks={processed_wlinks} processed_vlans={log.vlans} processed_ips={log.ips} "
                f"processed_clients={log.clients} duration={(_now() - started).total_seconds():.2f}s "
                f"(toggles: wlans={do_wlans} aps={do_aps} switches={do_switches} interfaces={do_interfaces} "
                f"wifi_clients={do_wifi_clients} wired_clients={do_wired_clients} cabling={do_cabling} "
                f"wireless_links={do_wireless_links} vlans={do_vlans}) "
                f"(mapping: mode={mapping_mode} parent_site={parent_site_ref} child_location={child_location_name})"
            )
            cfg.save()

            _sync_log_finish(log, "success", cfg.last_sync_message, message=cfg.last_sync_message)
            return cfg.last_sync_message

    except Exception as e:
        cfg.last_sync = _now()
        cfg.last_sync_status = "failed"
        cfg.last_sync_message = _safe_str(e, 2000)
        cfg.save()

        _sync_log_finish(log, "failed", "Sync failed", message=_safe_str(e, 4000), error=_safe_str(e, 20000))
        raise