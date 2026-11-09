#!/usr/bin/env python3
"""Static pre-check of an archr-launcher theme or module folder.

Usage: python3 precheck.py <folder> [--offline]

Catches the usual packaging mistakes before the launcher's own checks
(`archr-launcher --check-module` for modules, the capture test for themes).
It does not replace them. Needs Python 3.11+ (tomllib). Exit 1 on errors.
"""
import hashlib
import re
import struct
import sys
import tomllib
import urllib.request
from pathlib import Path

LANGS = ["en", "pt_BR", "es", "ru"]
errors: list[str] = []
warnings: list[str] = []


def png_size(path: Path):
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_preview(folder: Path, required: bool):
    for rel in ["preview.png", "screenshots/1.png", "screenshots/2.png", "screenshots/3.png"]:
        p = folder / rel
        if not p.exists():
            if rel == "preview.png" and required:
                warnings.append("preview.png missing (the store needs it)")
            continue
        size = png_size(p)
        if size != (640, 480):
            errors.append(f"{rel}: must be a 640x480 PNG, found {size}")
        if p.stat().st_size > 2 << 20:
            errors.append(f"{rel}: larger than 2 MB")


# ---------------------------------------------------------------- themes
THEME_TOP = {
    "background", "text", "highlight_bg", "accent", "highlight_text", "accent_text",
    "dim_text", "dim", "surface", "surface_elevated", "border", "badge",
    "text_secondary", "muted", "accent_text_secondary", "scrim", "success", "warning",
    "danger", "radius_item", "radius_card", "header_height", "footer_height",
    "row_height", "game_row_height", "selected_height", "game_selected_height",
    "font_size", "margin", "list_width", "cover", "system_screen", "font",
    "font_semibold", "font_mono", "font_mono_medium", "name", "view", "sounds",
    "details_shot", "details_info", "details_title", "details_subtitle",
    "details_text", "details_actions", "start_widgets", "start_area", "achievements_progress",
    "achievements_list", "saves_list", "saves_card", "shots_grid", "switcher_card",
    "switcher_side", "switcher_info", "resume_shot", "resume_info", "corners",
    "border_width", "shadow", "art_scaling", "image_scaling", "easing", "font_scale",
    "font_grid", "font_min", "font_smoothing", "text_outline", "background_image",
    "frames", "aspect", "description", "author", "version", "license", "min_launcher",
}
RECTS = {k for k in THEME_TOP if k.startswith(("details_", "achievements_", "saves_", "switcher_", "resume_"))} | {"shots_grid", "start_widgets", "start_area", "cover"}
# [aspect.<shape>] tables: square below 6:5, classic 6:5 to 29:20, wide above.
ASPECTS = {"square", "classic", "wide"}
# Kept from the theme as loaded, whatever the screen shape.
PER_THEME = {"font", "font_semibold", "font_mono", "font_mono_medium", "name", "sounds",
             "description", "author", "version", "license", "min_launcher"}
SCREEN_KEYS = {"header", "title", "status", "divider", "summary", "list", "panel", "art",
               "backdrop", "info", "meta", "dots", "decor"}
FRAMES = {"header", "footer", "list", "row", "selected", "panel", "art", "button",
          "button_selected", "badge", "tile", "tile_selected"}
SOUND_EVENTS = {"boot", "move", "page", "select", "back", "launch", "menu_open",
                "menu_close", "toggle", "error", "notice", "favorite"}
KEPT = {"toml", "png", "jpg", "jpeg", "webp", "svg", "ttf", "otf", "ogg", "wav", "txt", "md"}
COLOR = re.compile(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
COLOR_KEYS = {"background", "text", "accent", "accent_text", "dim", "surface",
              "surface_elevated", "border", "badge", "text_secondary", "muted",
              "accent_text_secondary", "scrim", "success", "warning", "danger"}


def file_ref(folder: Path, rel: str, what: str):
    if not isinstance(rel, str) or rel == "":
        return
    if rel.startswith("/") or ".." in Path(rel).parts:
        errors.append(f"{what}: {rel!r} must be a relative path inside the theme")
    elif not (folder / rel).is_file():
        errors.append(f"{what}: {rel} does not exist (paths are case-sensitive)")


def names(value, what: str):
    if isinstance(value, str):
        return
    if not isinstance(value, dict) or "en" not in value:
        errors.append(f"{what}: give a string or a table with at least en")
        return
    missing = [l for l in LANGS if l not in value]
    if missing:
        warnings.append(f"{what}: no text for {', '.join(missing)}")


def check_layout(folder: Path, t: dict, at: str):
    """Colors, rectangles, theme images and views: the keys an [aspect.<shape>]
    table may change as well as the top level (`at` prefixes messages)."""
    for key in COLOR_KEYS & t.keys():
        if not (isinstance(t[key], str) and COLOR.match(t[key])):
            errors.append(f"{at}{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
    for key in RECTS & t.keys():
        r = t[key]
        ok = isinstance(r, dict) and all(isinstance(r.get(c), (int, float)) and 0 <= r[c] <= 1 for c in "xywh")
        if not ok or r["x"] + r["w"] > 1 or r["y"] + r["h"] > 1:
            errors.append(f"{at}{key}: needs x, y, w, h fractions with x+w <= 1 and y+h <= 1 (else the default is used)")
    file_ref(folder, t.get("background_image"), f"{at}background_image")
    misplaced = "a top-level key written after a [table] header; move it above the first header"
    for name, frame in (t.get("frames") or {}).items():
        if name not in FRAMES:
            warnings.append(f"{at}frames.{name}: unknown frame name, ignored")
        for key in frame:
            if key in THEME_TOP:
                errors.append(f"{at}frames.{name}.{key}: {misplaced}")
            elif key not in ("image", "slice", "scale", "pad", "tile"):
                warnings.append(f"{at}frames.{name}.{key}: unknown key")
        file_ref(folder, frame.get("image"), f"{at}frames.{name}.image")
    for vid, view in (t.get("view") or {}).items():
        if not isinstance(view, dict):
            continue
        if vid != "lista" and "name" in view:
            names(view["name"], f"{at}view.{vid}.name")
        for key in view:
            if key in THEME_TOP and key not in ("name",):
                errors.append(f"{at}view.{vid}.{key}: a top-level key written after a [table] header; move it above the first header")
            elif key not in ("name", "systems", "games"):
                warnings.append(f"{at}view.{vid}.{key}: unknown key")
        for screen in ("systems", "games"):
            for key, value in (view.get(screen) or {}).items():
                if key in THEME_TOP:
                    errors.append(f"{at}view.{vid}.{screen}.{key}: a top-level key written after a [table] header; move it above the first header")
                elif key not in SCREEN_KEYS:
                    warnings.append(f"{at}view.{vid}.{screen}.{key}: unknown key")
                elif key == "decor":
                    for d in value:
                        file_ref(folder, d.get("image"), f"{at}view.{vid}.{screen}.decor")
                elif isinstance(value, dict):
                    for c in "xywh":
                        v = value.get(c)
                        if isinstance(v, (int, float)) and v > 1:
                            errors.append(f"{at}view.{vid}.{screen}.{key}.{c} = {v}: use a screen fraction, not pixels")


def check_theme(folder: Path):
    src = folder / "theme.toml"
    if src.stat().st_size > 64 << 10:
        errors.append("theme.toml: larger than 64 KiB")
    try:
        t = tomllib.loads(src.read_text("utf-8"))
    except tomllib.TOMLDecodeError as e:
        errors.append(f"theme.toml: not valid TOML: {e}")
        return
    for key in t:
        if key not in THEME_TOP:
            warnings.append(f"unknown top-level key {key} (ignored by the launcher)")
    if "name" not in t:
        errors.append("name: missing (the store refuses the theme)")
    else:
        names(t["name"], "name")
    if "description" in t:
        names(t["description"], "description")
    misplaced = "a top-level key written after a [table] header; move it above the first header"
    for key in ("font", "font_semibold", "font_mono", "font_mono_medium"):
        file_ref(folder, t.get(key), key)
    for key, rel in (t.get("sounds") or {}).items():
        if key == "systems" and isinstance(rel, dict):
            for sysname, r in rel.items():
                file_ref(folder, r, f"sounds.systems.{sysname}")
        elif key in THEME_TOP:
            errors.append(f"sounds.{key}: {misplaced}")
        elif key not in SOUND_EVENTS:
            warnings.append(f"sounds.{key}: unknown sound event")
        else:
            file_ref(folder, rel, f"sounds.{key}")
    check_layout(folder, t, "")
    aspects = t.get("aspect")
    if aspects is not None and not isinstance(aspects, dict):
        errors.append("aspect: must hold [aspect.square], [aspect.classic] or [aspect.wide] tables")
    for shape, table in (aspects if isinstance(aspects, dict) else {}).items():
        if shape not in ASPECTS:
            warnings.append(f"aspect.{shape}: unknown screen shape (square, classic or wide), ignored")
            continue
        if not isinstance(table, dict):
            errors.append(f"aspect.{shape}: must be a table")
            continue
        for key in table:
            if key not in THEME_TOP or key == "aspect":
                warnings.append(f"aspect.{shape}.{key}: unknown key (ignored by the launcher)")
            elif key in PER_THEME:
                warnings.append(f"aspect.{shape}.{key}: does not change per screen shape; set it at the top level")
        check_layout(folder, table, f"aspect.{shape}.")
    for p in folder.rglob("*"):
        rel = p.relative_to(folder)
        if any(part.startswith(".") for part in rel.parts) or not p.is_file():
            continue
        if p.suffix.lower().lstrip(".") not in KEPT and p.name not in ("LICENSE", "LICENCE", "COPYING"):
            warnings.append(f"{rel}: the store does not install this file type")
        if rel.parts[0] == "backgrounds" and p.suffix.lower() == ".png":
            size = png_size(p)
            if size and max(size) > 2048:
                warnings.append(f"{rel}: {size[0]}x{size[1]}; the launcher refuses pictures over 2048 px a side")
        if rel.parts[0] == "sounds" and p.stat().st_size > 1 << 20:
            errors.append(f"{rel}: sounds must be at most 1 MiB")
    check_preview(folder, required=True)


# --------------------------------------------------------------- modules
READABLE = {"system.language", "system.timezone", "system.cpugovernor", "system.hostname",
            "global.netplay.nickname", "global.retroachievements", "audio.volume",
            "display.brightness"}
ALLOWED = {
    "read": {"roms", "bios", "screenshots"},
    "config_read": READABLE,
    "config_write": {"system.cpugovernor", "global.netplay.nickname"},
    "hooks": {"launch"},
    "system": {"cpu-profile", "brightness", "volume", "wifi", "screenshot"},
}
EVENTS = {"launcher.started", "focus.system", "focus.game", "game.started", "game.ended"}
SEMVER = re.compile(r"^\d{1,6}\.\d{1,6}\.\d{1,6}$")


def flat_locale(path: Path):
    try:
        table = tomllib.loads(path.read_text("utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        errors.append(f"{path.name}: {e}")
        return {}
    for key, value in table.items():
        if isinstance(value, dict):
            errors.append(f"locales/{path.name}: key {key} is a table; quote dotted keys (\"{key}.x\" = ...)")
    return {k: v for k, v in table.items() if isinstance(v, str)}


def at_keys(node, found: set):
    if isinstance(node, str) and node.startswith("@"):
        found.add(node[1:])
    elif isinstance(node, dict):
        for v in node.values():
            at_keys(v, found)
    elif isinstance(node, list):
        for v in node:
            at_keys(v, found)


def check_module(folder: Path, offline: bool):
    try:
        m = tomllib.loads((folder / "module.toml").read_text("utf-8"))
    except tomllib.TOMLDecodeError as e:
        errors.append(f"module.toml: not valid TOML: {e}")
        return
    mid = m.get("id", "")
    if not re.fullmatch(r"[a-z0-9-]{3,40}", str(mid)):
        errors.append("id: required, [a-z0-9-]{3,40}")
    elif folder.name != mid:
        errors.append(f"the folder must be named {mid} (now {folder.name})")
    if not SEMVER.match(str(m.get("version", ""))):
        errors.append("version: required, x.y.z")
    api = m.get("api_version")
    if api not in (1, 2):
        errors.append("api_version: 1 or 2")
    run = m.get("run", {})
    if run.get("runtime") not in ("sh", "bash", "native"):
        errors.append("run.runtime: sh, bash or native")
    if run.get("mode") not in ("daemon", "oneshot"):
        errors.append("run.mode: daemon or oneshot")
    entry = run.get("entry", "")
    if not entry or entry.startswith(("/", ".")) or ".." in entry.split("/") or not (folder / entry).is_file():
        errors.append("run.entry: a file inside the module")
    perms = m.get("permissions", {})
    for key, value in perms.items():
        if key in ("net", "launch"):
            continue
        if key not in ALLOWED:
            errors.append(f"permissions.{key}: unknown or reserved permission (fatal)")
            continue
        for v in value:
            if v not in ALLOWED[key]:
                errors.append(f"permissions.{key}: {v} is not allowed")
    if api == 1 and (perms.get("launch") or any(perms.get(k) for k in ("config_write", "hooks", "system"))):
        errors.append("permissions: config_write, hooks, system and launch need api_version = 2")
    for hook in m.get("hooks", []):
        ev = hook.get("event")
        if ev not in EVENTS:
            warnings.append(f"hooks.event: {ev} is not delivered")
        elif ev.startswith("focus.") and run.get("mode") == "oneshot":
            warnings.append(f"hooks.event: {ev} only reaches daemons")
    pages = m.get("settings", {}).get("pages", [])
    page_ids = {p.get("id") for p in pages}
    rows = sum(len(p.get("rows", [])) for p in pages)
    if len(pages) > 8:
        warnings.append("settings: more than 8 pages, the rest are ignored")
    if rows > 48:
        errors.append(f"settings: {rows} rows, at most 48")
    start = m.get("start", {})
    for kind, cap in (("tiles", 2), ("shortcuts", 1), ("widgets", 1)):
        entries = start.get(kind, [])
        if len(entries) > cap:
            warnings.append(f"start.{kind}: at most {cap} per module")
        for e in entries:
            if "open" in e and e["open"] not in page_ids:
                errors.append(f"start.{kind}.{e.get('id')}: open = {e['open']} but there is no such page")
            if "open" not in e and "action" not in e:
                errors.append(f"start.{kind}.{e.get('id')}: needs open or action")
    if len(m.get("quick", [])) > 1:
        warnings.append("quick: at most 1 per module")
    en = folder / "locales" / "en.toml"
    if not en.is_file():
        errors.append("locales/en.toml: required")
        en_keys = {}
    else:
        en_keys = flat_locale(en)
    used: set = set()
    at_keys({k: v for k, v in m.items()}, used)
    for key in sorted(used - en_keys.keys()):
        errors.append(f"@{key}: not in locales/en.toml")
    for lang in LANGS[1:]:
        p = folder / "locales" / f"{lang}.toml"
        if not p.is_file():
            warnings.append(f"locales/{lang}.toml: missing (recommended)")
            continue
        missing = en_keys.keys() - flat_locale(p).keys()
        if missing:
            warnings.append(f"locales/{lang}.toml: missing {', '.join(sorted(missing))}")
    for field in ("name", "description"):
        if isinstance(m.get(field), dict):
            names(m[field], field)
        elif isinstance(m.get(field), str) and m[field].startswith("@"):
            warnings.append(f"{field}: a language table shows in the store before install; @key does not")
    icons = {m.get("icon")} | {e.get("icon") for k in ("tiles", "shortcuts", "widgets") for e in start.get(k, [])}
    for icon in sorted(i for i in icons if i):
        p = folder / "icons" / f"{icon}.svg"
        if not p.is_file():
            errors.append(f"icons/{icon}.svg: missing")
            continue
        if offline:
            continue
        url = f"https://unpkg.com/lucide-static@0.468.0/icons/{icon}.svg"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                upstream = r.read()
        except OSError as e:
            warnings.append(f"icons/{icon}.svg: could not fetch {url} to compare ({e})")
            continue
        if hashlib.sha256(upstream).digest() != hashlib.sha256(p.read_bytes()).digest():
            errors.append(f"icons/{icon}.svg: differs from Lucide 0.468.0; download it unmodified from {url}")
    check_preview(folder, required=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    folder = Path(args[0]).resolve()
    if (folder / "module.toml").is_file():
        kind = "module"
        check_module(folder, "--offline" in sys.argv)
    elif (folder / "theme.toml").is_file():
        kind = "theme"
        check_theme(folder)
    else:
        sys.exit(f"{folder}: no module.toml or theme.toml")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{folder.name} ({kind}): {'FAILED' if errors else 'ok'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
