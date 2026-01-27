# ruckus_r1_sync/mapping.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from django.utils.text import slugify
from dcim.models import Site, SiteGroup, Location


@dataclass(frozen=True)
class VenueMapping:
    # site, der an Devices gesetzt wird (immer gesetzt)
    device_site: Site
    # optionale Location, die an Devices gesetzt wird
    device_location: Optional[Location]
    # der ggf. neu/zusätzlich erstellte Venue-Site (nur mode sites/both)
    venue_site: Optional[Site]
    # der ggf. erstellte Venue-Location (mode locations/both)
    venue_location: Optional[Location]


def _deterministic_slug(prefix: str, venue_id: str, name_fallback: str, max_len: int = 100) -> str:
    base = (venue_id or "").strip() or (name_fallback or "").strip() or "venue"
    raw = f"{prefix}-{base}".lower()
    s = slugify(raw)[:max_len]
    return s or slugify(f"{prefix}-venue")[:max_len]


def resolve_parent_site(parent_site_ref: str) -> Site:
    """
    Resolve a Site by slug OR exact name (case-insensitive).
    """
    if not parent_site_ref:
        raise Site.DoesNotExist("Empty parent site reference")

    qs = Site.objects.filter(slug=parent_site_ref)
    if qs.exists():
        return qs.first()

    qs = Site.objects.filter(name__iexact=parent_site_ref)
    if qs.exists():
        return qs.first()

    raise Site.DoesNotExist(f"Parent site not found (by slug or name): {parent_site_ref}")


def map_venue_to_netbox(
    *,
    venue_id: str,
    venue_name: str,
    tenant,
    mode: str,
    site_group: Optional[SiteGroup],
    locations_parent_site: Optional[str],
    child_location_name: str,
    slug_prefix: str = "r1",
) -> VenueMapping:
    """
    modes:
      - sites:      Venue -> Site
      - locations:  Venue -> Location under parent Site
      - both:       Venue -> Site + child Location under that Site
    """
    mode = (mode or "sites").strip().lower()
    if mode not in {"sites", "locations", "both"}:
        raise ValueError(f"Invalid venue_mapping_mode: {mode}")

    venue_id = (venue_id or "").strip()
    venue_name = (venue_name or "").strip() or (venue_id or "Venue")

    venue_site: Optional[Site] = None
    venue_location: Optional[Location] = None

    # Mode A/C: create venue site
    if mode in {"sites", "both"}:
        slug = _deterministic_slug(slug_prefix, venue_id, venue_name, max_len=100)
        venue_site, created = Site.objects.get_or_create(
            slug=slug,
            defaults={
                "name": venue_name[:100],
                "group": site_group,
                "tenant": tenant,
                "status": "active",
                "description": f"RUCKUS One Venue {venue_id}",
            },
        )
        # keep name/group/tenant aligned
        changed = False
        if venue_site.name != venue_name[:100]:
            venue_site.name = venue_name[:100]
            changed = True
        if venue_site.group_id != (site_group.id if site_group else None):
            venue_site.group = site_group
            changed = True
        if venue_site.tenant_id != getattr(tenant, "id", tenant):
            venue_site.tenant = tenant
            changed = True
        if changed:
            venue_site.save()

        # devices live on this site
        device_site = venue_site

        if mode == "both":
            child_location_name = (child_location_name or "Venue").strip() or "Venue"
            child_slug = slugify(f"{slug}-{child_location_name}")[:100] or slugify(f"{slug}-venue")[:100]
            venue_location, _ = Location.objects.get_or_create(
                site=venue_site,
                slug=child_slug,
                defaults={"name": child_location_name[:100]},
            )
            if venue_location.name != child_location_name[:100]:
                venue_location.name = child_location_name[:100]
                venue_location.save()

            return VenueMapping(
                device_site=device_site,
                device_location=venue_location,
                venue_site=venue_site,
                venue_location=venue_location,
            )

        return VenueMapping(
            device_site=device_site,
            device_location=None,
            venue_site=venue_site,
            venue_location=None,
        )

    # Mode B: create venue location under parent site
    if not locations_parent_site:
        raise ValueError("venue_locations_parent_site must be set when venue_mapping_mode='locations'")

    parent_site = resolve_parent_site(locations_parent_site)
    loc_slug = _deterministic_slug(slug_prefix, venue_id, venue_name, max_len=100)

    venue_location, created = Location.objects.get_or_create(
        site=parent_site,
        slug=loc_slug,
        defaults={"name": venue_name[:100]},
    )
    if venue_location.name != venue_name[:100]:
        venue_location.name = venue_name[:100]
        venue_location.save()

    return VenueMapping(
        device_site=parent_site,
        device_location=venue_location,
        venue_site=None,
        venue_location=venue_location,
    )
