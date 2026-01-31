from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.utils.text import slugify

from dcim.models import Location, Site, SiteGroup
from tenancy.models import Tenant


def _safe_slug(value: str, fallback: str) -> str:
    s = slugify((value or "").strip())
    if not s:
        s = slugify(fallback.strip()) or fallback.strip().lower()
    return s[:100]


@dataclass(frozen=True)
class VenueMapping:
    # Where devices/interfaces/VLANs of this venue should land
    device_site: Site
    device_location: Optional[Location]


def _coerce_site_group(site_group: Optional[SiteGroup]) -> Optional[SiteGroup]:
    return site_group if isinstance(site_group, SiteGroup) else None


def _resolve_parent_site(locations_parent_site, tenant: Optional[Tenant]) -> Site:
    """Resolve the configured parent site for 'locations' mode.

    Accepts:
      - Site instance
      - Site ID (int/str)
      - Site name (str)
    """
    if isinstance(locations_parent_site, Site):
        return locations_parent_site

    if locations_parent_site is None:
        raise ValueError("venue_locations_parent_site is required when venue_mapping_mode='locations'")

    # Try ID
    try:
        sid = int(str(locations_parent_site).strip())
        site = Site.objects.filter(pk=sid).first()
        if site:
            return site
    except Exception:
        pass

    # Fallback name
    name = str(locations_parent_site).strip()
    site = Site.objects.filter(name=name).first()
    if site:
        return site

    raise ValueError(f"Parent site not found: {locations_parent_site!r}")


@transaction.atomic
def map_venue_to_netbox(
    *,
    venue_id: str,
    venue_name: str,
    tenant: Optional[Tenant],
    mode: str,
    site_group: Optional[SiteGroup] = None,
    locations_parent_site=None,
    child_location_name: str = "Venue",
    slug_prefix: str = "r1",
) -> VenueMapping:
    """Map a RUCKUS One venue to NetBox objects.

    Modes:
      - sites:        create/reuse Site per venue, no Location
      - locations:    reuse existing parent Site, create/reuse Location per venue name under it
      - both:         create/reuse Site per venue AND create/reuse child Location under that Site
    """
    mode = (mode or "sites").strip().lower()
    sg = _coerce_site_group(site_group)

    venue_name = (venue_name or venue_id or "Venue").strip()
    venue_id = (venue_id or "").strip()

    if mode == "locations":
        parent_site = _resolve_parent_site(locations_parent_site, tenant)

        # Location name must be unique per site -> upsert by (site, name)
        loc_name = venue_name
        loc, created = Location.objects.get_or_create(
            site=parent_site,
            name=loc_name,
            defaults={
                "slug": _safe_slug(loc_name, f"{slug_prefix}-{venue_id or 'venue'}"),
                "tenant": tenant,
            },
        )
        # Always update core fields if changed (rename-safe / tenant moves etc.)
        updates = {}
        desired_slug = _safe_slug(loc_name, f"{slug_prefix}-{venue_id or 'venue'}")
        if not (loc.slug or "").strip():
            updates["slug"] = desired_slug
        if loc.slug != desired_slug and desired_slug and loc.slug and loc.slug.startswith(f"{slug_prefix}-"):
            # only auto-adjust if it looks like ours, avoid clobbering user-managed slugs
            updates["slug"] = desired_slug
        if getattr(loc, "tenant_id", None) != (tenant.id if tenant else None):
            updates["tenant"] = tenant
        if updates:
            for k, v in updates.items():
                setattr(loc, k, v)
            loc.save()

        return VenueMapping(device_site=parent_site, device_location=loc)

    # sites or both -> create/reuse Site per venue
    site_name = venue_name
    site = Site.objects.filter(name=site_name).first()
    if site is None:
        site = Site.objects.create(
            name=site_name,
            slug=_safe_slug(site_name, f"{slug_prefix}-{venue_id or 'site'}"),
            group=sg,
            tenant=tenant,
        )
    else:
        # update group/tenant/slug if needed (do not overwrite custom slug unless empty)
        changed = False
        if sg and getattr(site, "group_id", None) != sg.id:
            site.group = sg
            changed = True
        if getattr(site, "tenant_id", None) != (tenant.id if tenant else None):
            site.tenant = tenant
            changed = True
        if not (site.slug or "").strip():
            site.slug = _safe_slug(site_name, f"{slug_prefix}-{venue_id or 'site'}")
            changed = True
        if changed:
            site.save()

    if mode == "both":
        cname = (child_location_name or "Venue").strip()
        if not cname:
            cname = "Venue"
        loc, _ = Location.objects.get_or_create(
            site=site,
            name=cname,
            defaults={
                "slug": _safe_slug(cname, f"{slug_prefix}-{venue_id or 'venue'}"),
                "tenant": tenant,
            },
        )
        # keep tenant aligned
        if getattr(loc, "tenant_id", None) != (tenant.id if tenant else None):
            loc.tenant = tenant
            loc.save()
        return VenueMapping(device_site=site, device_location=loc)

    # sites
    return VenueMapping(device_site=site, device_location=None)
