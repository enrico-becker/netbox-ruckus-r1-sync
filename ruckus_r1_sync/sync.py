from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, SiteGroup
from ipam.models import IPAddress
from wireless.models import WirelessLAN

from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client as RuckusR1ClientModel
from .ruckus_api import RuckusR1Client


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
    # stable + unique for client devices
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
    return RuckusR1Client(
        base_url=_normalize_base_url(cfg.api_base_url),
        ruckus_tenant_id=cfg.ruckus_tenant_id,
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
        verify_tls=True,
        timeout=30,
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


def _get_or_create_site(cfg: RuckusR1TenantConfig, group: Optional[SiteGroup], venue: Dict[str, Any]) -> Site:
    venue_id = _safe_str(venue.get("id") or venue.get("venueId") or "", 128)
    venue_name = (venue.get("name") or venue.get("venueName") or venue_id or "Venue").strip()
    slug = _slugify(f"r1-{venue_id}-{venue_name}")[:100]

    obj = Site.objects.filter(slug=slug).first()
    if not obj:
        obj = Site.objects.create(
            name=venue_name[:100],
            slug=slug,
            group=group,
            tenant=cfg.tenant,
            status="active",
            description=f"RUCKUS One Venue {venue_id}",
        )
    else:
        changed = False
        if obj.name != venue_name[:100]:
            obj.name = venue_name[:100]
            changed = True
        if obj.group_id != (group.id if group else None):
            obj.group = group
            changed = True
        if obj.tenant_id != cfg.tenant_id:
            obj.tenant = cfg.tenant
            changed = True
        if changed:
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
    # requirement for infra devices
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


def _get_or_create_device_infra(
    cfg: RuckusR1TenantConfig,
    site: Site,
    role_name: str,
    model: str,
    name: str,
    serial: str = "",
) -> Device:
    """
    Infra devices: Manufacturer always RUCKUS Networks, uniqueness by serial.
    """
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
        return Device.objects.create(**kwargs)

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
    """
    NetBox v4 uses generic assignment (assigned_object), older may have 'assigned_object' too.
    We'll try both.
    """
    # generic assignment (NetBox v3/v4)
    if hasattr(ip_obj, "assigned_object"):
        try:
            ip_obj.assigned_object = iface
            ip_obj.save()
            return
        except Exception:
            pass

    # legacy-ish field
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


def _upsert_client_as_dcim_device(cfg: RuckusR1TenantConfig, site: Site, cl: Dict[str, Any]) -> Tuple[Optional[Device], Optional[IPAddress]]:
    """
    Create/Update a NetBox dcim.Device for a Wi-Fi client.
    - Unique by MAC (stored as serial = mac without :)
    - Device.name is ALWAYS unique/stable: CL-<serial> (optionally with hostname prefix)
    - Interface wlan0 with MAC
    - IPAddress assigned to wlan0 + set as primary_ip4
    """
    mac = _norm_mac(cl.get("macAddress") or cl.get("mac") or cl.get("clientMac") or "")
    if not _looks_like_mac(mac):
        return (None, None)

    serial = _mac_to_serial(mac)  # e.g. 9249703b9a1b
    role = _get_or_create_role("Wireless Client")

    manu = _get_or_create_manufacturer_named("Client")
    model = (cl.get("deviceType") or cl.get("modelName") or "Client").strip()
    dtype = _get_or_create_devicetype(manu, model)

    raw_hostname = (cl.get("hostname") or "").strip()
    # Use hostname only as *decorator*, never as the whole name
    host_part = ""
    if raw_hostname and not _looks_like_mac(raw_hostname):
        # keep it safe & short
        host_part = _slugify(raw_hostname)[:20]

    # Deterministic unique name within site+tenant
    # (serial is unique per client MAC)
    name = f"CL-{host_part + '-' if host_part else ''}{serial[:12]}"

    # Find by serial first (primary key)
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

        # IMPORTANT: Do NOT rename to raw hostname (avoids collisions like "wlan0", "Mac", "iPhone", etc.)
        # Only set name to our deterministic scheme if empty or if it looks wrong.
        if not obj.name or obj.name.lower() in ("wlan0", "unknown", "client"):
            obj.name = name[:64]
            changed = True

        # Store hostname in description instead (optional)
        if hasattr(obj, "description"):
            desired_desc = f"R1 Client hostname={raw_hostname}" if raw_hostname else "R1 Client"
            if (obj.description or "") != desired_desc[:200]:
                obj.description = desired_desc[:200]
                changed = True

        if _set_device_role_attr(obj, role):
            changed = True

        if changed:
            obj.save()

    # Interface
    iface = _ensure_interface(obj, "wlan0")
    if hasattr(iface, "mac_address"):
        try:
            if (iface.mac_address or "").lower() != mac:
                iface.mac_address = mac
                iface.save()
        except Exception:
            pass

    # IP
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
    cl: Dict[str, Any],
    *,
    iface_name: str = "eth0",
) -> Tuple[Optional[Device], Optional[IPAddress]]:
    """
    Wired client devices (from venues/switches/clients/query).
    - Unique by MAC (serial=mac sans :)
    - Interface eth0
    - IP best-effort
    """
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
    """
    Handles e.g. "10G", "2.5G", "25G", "2.5G/5G/10G MultiGig".
    Returns best-effort *maximum* in kbps.
    """
    if not cap:
        return None
    t = cap.strip().lower()
    # Extract tokens like 2.5g, 5g, 10g, 25g
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
                # treat as Mbps
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


def _create_wireless_link_best_effort(a_device: Device, b_device: Device, a_mac: str, b_mac: str) -> bool:
    try:
        WirelessLink = _nb_model("wireless", "WirelessLink")
    except Exception:
        return False

    a_iface = _ensure_interface(a_device, "mesh")
    b_iface = _ensure_interface(b_device, "mesh")
    _upsert_macaddress_best_effort(a_iface, a_mac)
    _upsert_macaddress_best_effort(b_iface, b_mac)

    qs = WirelessLink.objects.all()
    for fa, fb in (("interface_a", "interface_b"), ("a_interface", "b_interface")):
        if hasattr(WirelessLink, fa) and hasattr(WirelessLink, fb):
            try:
                if qs.filter(**{fa: a_iface, fb: b_iface}).exists() or qs.filter(**{fa: b_iface, fb: a_iface}).exists():
                    return False
            except Exception:
                pass

    obj = WirelessLink()
    created = False

    for fa, fb in (("interface_a", "interface_b"), ("a_interface", "b_interface")):
        if hasattr(obj, fa) and hasattr(obj, fb):
            try:
                setattr(obj, fa, a_iface)
                setattr(obj, fb, b_iface)
                created = True
                break
            except Exception:
                continue

    if not created:
        for fa, fb in (("device_a", "device_b"), ("a_device", "b_device")):
            if hasattr(obj, fa) and hasattr(obj, fb):
                try:
                    setattr(obj, fa, a_device)
                    setattr(obj, fb, b_device)
                    created = True
                    break
                except Exception:
                    continue

    if not created:
        return False

    try:
        obj.save()
        return True
    except Exception:
        return False


def _sync_switch_ports_for_venue(cfg: RuckusR1TenantConfig, api: RuckusR1Client, site: Site, venue_id: str) -> Tuple[int, int]:
    """
    /venues/switches/switchPorts/query
    Creates/updates dcim.Interface on the corresponding switch device.
    Matching: switchUnitId -> Device.serial
    Returns: (touched_ifaces, touched_macs)
    """
    touched_ifaces = 0
    touched_macs = 0

    rows = _query_all(api, "/venues/switches/switchPorts/query", {"venueId": venue_id, "limit": 5000})
    if not rows:
        return (0, 0)

    for p in rows:
        if not isinstance(p, dict):
            continue

        switch_unit_id = (p.get("switchUnitId") or "").strip()
        if not switch_unit_id:
            continue

        sw = Device.objects.filter(tenant=cfg.tenant, site=site, serial=switch_unit_id).first()
        if not sw and cfg.allow_stub_devices:
            # fallback: build a stub switch (rare, but helps)
            sw_name = (p.get("switchName") or p.get("switchModel") or switch_unit_id).strip()
            sw_model = (p.get("switchModel") or "Switch").strip()
            sw = _get_or_create_device_infra(cfg, site, "Switch", sw_model, sw_name or switch_unit_id, serial=switch_unit_id)

        if not sw:
            continue

        ifname = (p.get("portIdentifier") or p.get("name") or "").strip()
        if not ifname:
            continue

        iface = _ensure_interface(sw, ifname)
        touched_ifaces += 1

        # MAC
        pmac = (p.get("portMac") or "").strip()
        if pmac and _upsert_macaddress_best_effort(iface, pmac):
            touched_macs += 1

        # enabled/admin + speed + poe + description
        admin_up = (p.get("adminStatus") == "Up")
        speed_kbps = _capacity_to_kbps(p.get("portSpeedCapacity") or "") or _parse_link_speed_to_kbps(p.get("portSpeed") or "")
        poe_enabled = p.get("poeEnabled")
        if poe_enabled is None:
            poe_enabled = p.get("poeEnabled")  # keep

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

    return (touched_ifaces, touched_macs)


def _sync_switch_clients_for_venue(
    cfg: RuckusR1TenantConfig,
    api: RuckusR1Client,
    site: Site,
    venue_id: str
) -> Tuple[int, int, int]:
    """
    /venues/switches/clients/query
    - Upserts plugin model RuckusR1Client (as "wired" client)
    - Upserts dcim.Device for wired client + eth0
    - Best-effort create Cable between switch port and client eth0 (if switchUnitId + portIdentifier present)
    Returns: (processed_clients, touched_ifaces, touched_cables)
    """
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
        # venue id effective
        vinfo = cl.get("venueInformation") or {}
        venue_id_effective = (vinfo.get("id") or venue_id or "").strip()

        if not _looks_like_mac(mac):
            # salvage
            for _, v in cl.items():
                if isinstance(v, str) and _looks_like_mac(v):
                    mac = _norm_mac(v)
                    break

        if not _looks_like_mac(mac):
            mac = "unknown"

        # Plugin model upsert (wired client)
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

        # dcim device + eth0
        client_dev = None
        client_iface = None
        if mac != "unknown":
            client_dev, _ = _upsert_wired_client_as_dcim_device(cfg, site, cl, iface_name="eth0")
            if client_dev:
                client_iface = _ensure_interface(client_dev, "eth0")
                touched_ifaces += 1

        # Best-effort cable: switch port -> client eth0
        if client_dev and client_iface and switch_unit_id and port_name:
            sw = Device.objects.filter(tenant=cfg.tenant, site=site, serial=switch_unit_id).first()
            if sw:
                sw_iface = _ensure_interface(sw, port_name)
                touched_ifaces += 1
                if _create_cable(sw_iface, client_iface, status="connected"):
                    touched_cables += 1

        processed_clients += 1

    return (processed_clients, touched_ifaces, touched_cables)


def _sync_topologies_for_venue(cfg: RuckusR1TenantConfig, api: RuckusR1Client, site: Site, venue_id: str) -> Tuple[int, int, int, int]:
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

        dev = _get_or_create_device_infra(cfg, site, role, model, name or serial or mac or "device", serial=serial)

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

        if not a_dev and cfg.allow_stub_devices:
            a_dev = _get_or_create_device_infra(cfg, site, "Device", "Device", from_name or from_serial or "device", serial=from_serial)
        if not b_dev and cfg.allow_stub_devices:
            b_dev = _get_or_create_device_infra(cfg, site, "Device", "Device", to_name or to_serial or "device", serial=to_serial)

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

        elif ctype == "mesh":
            if _create_wireless_link_best_effort(a_dev, b_dev, from_mac, to_mac):
                touched_wlinks += 1

    return (touched_ifaces, touched_macs, touched_cables, touched_wlinks)


# -----------------
# Main sync
# -----------------

def run_sync_for_tenantconfig(cfg_or_id: Union[RuckusR1TenantConfig, int]) -> str:
    cfg = _resolve_config(cfg_or_id)
    if not cfg.enabled:
        return "Config disabled, skipping."

    api = _make_client(cfg)
    log = _sync_log_start(cfg)
    started = _now()

    try:
        with transaction.atomic():
            site_group = _get_or_create_site_group(cfg)

            venues = _query_all(api, "/venues/query", {"limit": 500})
            log.venues = len(venues)

            wifi_networks = _query_all(api, "/wifiNetworks/query", {"limit": 500})
            for wn in wifi_networks:
                ssid = (wn.get("ssid") or wn.get("name") or "").strip()
                _get_or_create_wlan(cfg, ssid)
            log.wlans = len(wifi_networks)

            processed_devices = 0
            processed_ips = 0
            processed_clients = 0
            processed_ifaces = 0
            processed_macs = 0
            processed_cables = 0
            processed_wlinks = 0

            for venue in venues:
                venue_id = _safe_str(venue.get("id") or venue.get("venueId") or "", 128)
                site = _get_or_create_site(cfg, site_group, venue)

                # APs
                aps = _query_all(api, "/venues/aps/query", {"venueId": venue_id, "limit": 1000})
                for ap in aps:
                    name = (ap.get("name") or ap.get("apName") or ap.get("hostname") or ap.get("serial") or "").strip()
                    serial = (ap.get("serial") or ap.get("msn") or ap.get("serialNumber") or ap.get("apSerial") or ap.get("deviceSerial") or "").strip()
                    model = (ap.get("model") or ap.get("apModel") or "Access Point").strip()
                    mgmt_ip = (ap.get("ip") or ap.get("ipAddress") or ap.get("mgmtIp") or "").strip()

                    _get_or_create_device_infra(cfg, site, "Access Point", model, name or serial or "AP", serial=serial)
                    processed_devices += 1
                    if mgmt_ip and _upsert_ip(cfg, mgmt_ip):
                        processed_ips += 1

                # Switches
                switches = _query_all(api, "/venues/switches/query", {"venueId": venue_id, "limit": 1000})
                for sw in switches:
                    name = (sw.get("name") or sw.get("switchName") or sw.get("hostname") or sw.get("serial") or "").strip()
                    serial = (sw.get("serial") or sw.get("msn") or sw.get("serialNumber") or sw.get("switchSerial") or sw.get("deviceSerial") or "").strip()
                    model = (sw.get("model") or sw.get("switchModel") or "Switch").strip()
                    mgmt_ip = (sw.get("ip") or sw.get("ipAddress") or sw.get("mgmtIp") or "").strip()

                    _get_or_create_device_infra(cfg, site, "Switch", model, name or serial or "Switch", serial=serial)
                    processed_devices += 1
                    if mgmt_ip and _upsert_ip(cfg, mgmt_ip):
                        processed_ips += 1

                # NEW: Switch Ports -> dcim.Interface
                it_ports, mt_ports = _sync_switch_ports_for_venue(cfg, api, site, venue_id)
                processed_ifaces += it_ports
                processed_macs += mt_ports

                # Clients (Wi-Fi) -> Plugin model + dcim.Device
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

                    # HERE: create dcim.Device for client
                    if mac != "unknown":
                        _upsert_client_as_dcim_device(cfg, site, cl)

                    processed_clients += 1

                # NEW: Switch Clients (wired)
                sc, it_sc, ct_sc = _sync_switch_clients_for_venue(cfg, api, site, venue_id)
                processed_clients += sc
                processed_ifaces += it_sc
                processed_cables += ct_sc

                # Existing topology (cables/wlinks from /venues/{id}/topologies)
                it, mt, ct, wt = _sync_topologies_for_venue(cfg, api, site, venue_id)
                processed_ifaces += it
                processed_macs += mt
                processed_cables += ct
                processed_wlinks += wt

            # Keep "processed" counters in log (they represent work done, not distinct totals)
            log.devices = processed_devices
            log.ips = processed_ips
            log.clients = processed_clients
            log.interfaces = processed_ifaces
            log.macs = processed_macs
            log.cables = processed_cables
            log.save()

            cfg.last_sync = _now()
            cfg.last_sync_status = "ok"
            cfg.last_sync_message = (
                f"Sync OK. venues={log.venues} wlans={log.wlans} processed_devices={log.devices} "
                f"processed_interfaces={log.interfaces} processed_macs={log.macs} processed_cables={log.cables} "
                f"processed_ips={log.ips} processed_clients={log.clients} duration={(_now() - started).total_seconds():.2f}s"
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
 