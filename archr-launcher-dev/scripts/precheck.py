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
    # Free screens (update 20261125.15): variables for every key.
    "vars",
# 3.1: bold face, style, and one table per screen.
"font_bold", "shadow_color", "shadow_blur", "shadow_offset", "glass", "focus",
"focus_scale", "focus_ring", "motion", "gradient", "title_tracking",
# 3.1 later: spaced small capitals, glyph hinting, an app's screens.
"caps_tracking", "font_hinting", "app",
# Free screens phase 5 (update 20261125.19): theme options and other files.
"options", "include",
"toast", "hints", "status", "header", "dialog", "start", "menu", "details", "achievements",
"saves", "shots", "switcher", "resume", "search", "keyboard", "osd", "settings",
}
# The rows Settings › Appearance already has, in every language the launcher
# ships (locales/*.toml, APPEARANCE in settings/pages.rs): an option with one
# of these names would sit next to a row of the same name doing another thing.
APPEARANCE_ROWS = {n.casefold() for n in (
    "Accent color", "Akku in Prozent", "Akzentfarbe", "Ancho de la carátula", "Animaciones",
    "Animações", "Animationen", "Animations", "Ansicht", "Avisos", "Background",
    "Battery percentage", "Benachrichtigungen", "Box art", "Box art corners", "Box art width",
    "Cantos da capa", "Capas", "Carátulas", "Color de énfasis", "Color del texto",
    "Color del texto secundario", "Color del texto seleccionado", "Cor de destaque",
    "Cor do texto", "Cor do texto secundário", "Cor do texto selecionado", "Cover",
    "Coverbreite", "Coverecken", "Dicas de botão só em texto", "Esquinas de la carátula",
    "Fondo", "Fondo del selector", "Fondo del sistema", "Font", "Fonte", "Font weight",
    "Fuente", "Fundo", "Fundo do seletor", "Fundo do sistema", "Grosor de la fuente",
    "Hintergrund", "Hintergrund des Spielwechslers", "Indicaciones de botón solo en texto",
    "Largura da capa", "Loja de temas", "Notifications", "Opciones del tema", "Opções do tema",
    "Peso da fonte", "Porcentagem da bateria", "Porcentaje de batería", "Restaurar padrão",
    "Restaurar valores", "Restore defaults", "Schriftart", "Schriftstärke",
    "Secondary text color", "Sekundäre Textfarbe", "Selected text color",
    "Standard wiederherstellen", "Switcher background", "System background",
    "Systemhintergrund", "Tamanho do texto", "Tamaño del texto", "Tastenhinweise nur als Text",
    "Tema", "Text color", "Textfarbe", "Textfarbe der Auswahl", "Textgröße",
    "Text-only button hints", "Text size", "Theme", "Theme-Optionen", "Theme options",
    "Theme store", "Theme-Store", "Tienda de temas", "View", "Vista", "Visualização",
    "Анимации", "Вид", "Магазин тем", "Насыщенность шрифта", "Обложки", "Параметры темы",
    "Подсказки кнопок только текстом", "Процент заряда", "Размер текста", "Сбросить настройки",
    "Тема", "Уведомления", "Углы обложки", "Фон", "Фон переключателя", "Фон системы",
    "Цвет акцента", "Цвет вторичного текста", "Цвет выделенного текста", "Цвет текста",
    "Ширина обложки", "Шрифт", "主题", "主题商店", "主题选项", "动画", "字体", "字体粗细",
    "封面", "封面圆角", "封面宽度", "平台背景", "强调色", "恢复默认", "文字大小", "文字颜色",
    "次要文字颜色", "游戏切换器背景", "电量百分比", "纯文字按键提示", "背景", "视图",
    "选中文字颜色", "通知")}
PLAIN_ID = re.compile(r"^[A-Za-z0-9_-]+$")
MAX_OPTIONS, MAX_CHOICES, MAX_DEPTH = 12, 24, 4
RECTS = {k for k in THEME_TOP if k.startswith(("details_", "achievements_", "saves_", "switcher_", "resume_"))} | {"shots_grid", "start_widgets", "start_area", "cover"}
# [aspect.<shape>] tables: square below 6:5, classic 6:5 to 29:20, wide above.
ASPECTS = {"square", "classic", "wide"}
# Kept from the theme as loaded, whatever the screen shape.
PER_THEME = {"font", "font_semibold", "font_bold", "font_mono", "font_mono_medium", "name", "sounds",
             "description", "author", "version", "license", "min_launcher"}
SCREEN_KEYS = {"header", "title", "status", "divider", "summary", "list", "panel", "art",
               "backdrop", "info", "meta", "dots", "decor", "strip"}
# Free screens (launcher crates/archr-ui/src/layout/scene.rs): the fields of
# an [[view.<id>.systems.el]] / [[view.<id>.games.el]] element.
EL_COMMON = {"id", "kind", "base", "rect", "anchor", "z", "opacity", "rotate", "pivot", "when",
             "enter", "select"}
# Phase 6 (20261125.20): enter / select = { from, distance, fade, scale,
# duration, delay, ease }; nothing runs past ANIM_MAX seconds.
ANIM_KEYS = {"from", "distance", "fade", "scale", "duration", "delay", "ease"}
ANIM_MAX = 0.6
EL_TEXT = {"text", "font", "size", "color", "align", "valign", "upper", "shadow", "wrap", "line",
           "fit_text"}
EL_KINDS = {
    "image": {"src", "fit", "align", "tint", "radius", "fallback", "fallback_text"},
    "text": EL_TEXT,
    "rect": {"fill", "border", "radius", "gradient"},
    "frame": {"image", "slice", "scale", "tile"},
    "panel": {"radius", "style", "gradient"},
    "list": {"row", "selected", "gap", "size", "selected_size", "radius", "axis", "mark", "scroll",
             "cursor", "columns", "color", "font", "align", "loop"},
    "hints": {"align", "style", "color", "badge", "letter_color"},
    "status": {"color"},
    # Phase 2 (20261125.16): stars and a label/value card.
    "rating": {"star", "star_half", "star_empty", "color", "empty", "empty_opacity", "spacing",
               "align", "value", "size"},
    "fields": {"star", "star_half", "star_empty", "color", "empty", "empty_opacity", "spacing",
               "align", "rows", "hide_empty", "upper_labels", "row", "font", "size", "label_font",
               "label_size", "label_color", "divider", "star_size"},
    # Phase 3 (20261125.17): the screen's items as a carousel (row, column,
    # wheel) or a grid, drawn from an `item` template.
    "carousel": {"of", "item", "selected", "spacing", "loop", "favorite", "axis", "visible",
                 "align", "wheel", "reflection"},
    "grid": {"of", "item", "selected", "spacing", "loop", "favorite", "columns", "rows"},
    # Phase 4 (20261125.18): one muted clip per screen.
    "video": {"src", "fit", "radius", "delay", "mute", "loop", "fallback"},
}
# The kinds that take the d-pad: one per screen.
EL_COLLECTIONS = {"list", "carousel", "grid"}
EL_ITEM = {"image", "logo", "text", "font", "size", "color", "w", "h", "fit", "radius", "fill"}
EL_WORDS = {"fit": {"contain", "cover", "stretch"}, "valign": {"top", "middle", "bottom"},
            "fit_text": {"ellipsis", "shrink"}}
EL_ANCHORS = {"top-left", "top", "top-right", "left", "center", "right", "bottom-left", "bottom",
              "bottom-right"}
EL_DATA = {"system", "system.name", "system.fullname", "system.maker", "system.year",
           "system.count", "system.games", "system.favorites", "game.name", "game.description",
           "game.genre", "game.developer", "game.publisher", "game.year", "game.players",
           "game.rating", "game.last_played", "list.index", "list.total", "item", "item.name",
           "aspect"}
# Pictures, not text: valid in an image's src and in when.has, not in ${...}.
EL_PICTURES = {"game.cover", "game.screenshot", "game.logo", "game.wheel", "game.marquee",
               "system.logo", "system.image"}
# Clips: valid in a video's src and in when.has, not in ${...} nor in an image.
EL_CLIPS = {"game.video", "system.video"}
EL_FACES = {"regular", "semibold", "bold", "mono"}
DATA_REF = re.compile(r"\$\{([^}]*)\}")
FRAMES = {"header", "footer", "list", "row", "selected", "panel", "art", "button",
          "button_selected", "badge", "tile", "tile_selected"}
SOUND_EVENTS = {"boot", "move", "page", "select", "back", "launch", "menu_open",
                "menu_close", "toggle", "error", "notice", "favorite"}
KEPT = {"toml", "png", "jpg", "jpeg", "webp", "svg", "ttf", "otf", "ogg", "wav", "txt", "md"}
# 3.1 screen tables (launcher crates/archr-ui/src/screens.rs): every key, and
# the words a style key takes. A rectangle is { x, y, w, h } in screen fractions.
SCREEN_TABLES = {
    "toast": {"position": {"top-left", "top", "top-right"}, "width": None,
              "icon": {"circle", "square", "none"}, "style": {"glass", "plain"}},
    "hints": {"style": {"bar", "capsule"}, "position": {"left", "center", "right"}, "lit": None},
    "status": {"style": {"glass", "plain"}, "battery": None, "radios": None,
               "clock": {"mono", "text"}, "rect": "rect"},
    "header": {"style": {"path", "capsule"}},
    "dialog": {"width": None, "radius": None, "icon": None, "buttons": {"row", "hints"},
               "style": {"glass", "plain"}},
    "start": {"style": {"tiles", "control"}, "radius": None, "shortcut": None, "clock": "clock",
              "area": "rect", "widgets": "rect", "tiles": "rect", "shortcuts": "rect"},
    "menu": {"style": {"list", "context"}, "anchor": {"focus", "center"}, "width": None,
             "row": None, "radius": None, "rect": "rect"},
    "details": {"style": {"panels", "hero"}, "shelf": None, "shot": "rect", "info": "rect",
                "title": "rect", "subtitle": "rect", "text": "rect", "actions": "rect"},
    "achievements": {"style": {"plain", "glass"}, "row": None, "gap": None, "badge": None,
                     "badge_radius": None, "progress": "progress", "list": "rect"},
    "saves": {"style": {"list", "preview"}, "row": None, "thumb": None, "list": "rect",
              "preview": "rect"},
    "shots": {"sections": None, "columns": None, "gap": None, "radius": None, "grid": "rect"},
    "switcher": {"cards": {"row", "depth"}, "card": "rect", "side": "rect", "info": "rect"},
    "resume": {"style": {"picture", "title"}, "shot": "rect", "info": "rect",
               "progress": "rect", "backdrop": "backdrop"},
    "search": {"style": {"plain", "field"}, "row": None, "height": None, "field": "rect",
               "results": "rect", "dock": {"bottom", "results"}},
    "keyboard": {"sheet": None, "key": None},
    "osd": {"style": {"pill", "capsule"}, "position": {"right", "left", "top", "bottom"},
            "fill": "color", "track": "color", "radius": None},
    "settings": {"layout": {"list", "sidebar"}, "sidebar": None, "row": None,
                 "icon": {"plain", "tile"}, "groups": {"flat", "inset"},
                 "title": {"beside", "below"}, "icon_colors": None},
}
SETTINGS_PAGES = {"network", "sound", "controls", "games", "region", "appearance",
                  "launcher", "achievements", "system", "storage"}
STYLE_WORDS = {"shadow": {"soft", "hard", "none"}, "focus": {"pill", "lift"},
               "motion": {"tween", "spring"}, "art_scaling": {"smooth", "pixel"},
               "image_scaling": {"smooth", "pixel"}, "easing": {"smooth", "steps"},
               "font_hinting": {"mono", "light", "none"}}
HOME_KEYS = {"tabs", "hero", "shelves", "library", "heading", "decor"}
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
    misplaced = "a top-level key written after a [table] header; move it above the first header"
    for key in COLOR_KEYS & t.keys():
        if not (isinstance(t[key], str) and COLOR.match(t[key])):
            errors.append(f"{at}{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
    for key in RECTS & t.keys():
        r = t[key]
        ok = isinstance(r, dict) and all(isinstance(r.get(c), (int, float)) and 0 <= r[c] <= 1 for c in "xywh")
        if not ok or r["x"] + r["w"] > 1 or r["y"] + r["h"] > 1:
            errors.append(f"{at}{key}: needs x, y, w, h fractions with x+w <= 1 and y+h <= 1 (else the default is used)")
    file_ref(folder, t.get("background_image"), f"{at}background_image")
    for key, words in STYLE_WORDS.items():
        if key in t and t[key] not in words:
            errors.append(f"{at}{key}: one of {', '.join(sorted(words))} (else the default is used)")
    for key in ("shadow_color",):
        if key in t and not (isinstance(t[key], str) and COLOR.match(t[key])):
            errors.append(f"{at}{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
    if "title_tracking" in t:
        v = t["title_tracking"]
        if not isinstance(v, (int, float)) or not -0.1 <= v <= 0.1:
            errors.append(f"{at}title_tracking: a number from -0.1 to 0.1 (em), else 0 is used")
    if "caps_tracking" in t:
        v = t["caps_tracking"]
        if not isinstance(v, (int, float)) or not 0 <= v <= 0.3:
            errors.append(f"{at}caps_tracking: a number from 0 to 0.3 (em), else 0 is used")
    app = t.get("app")
    if app is not None and not isinstance(app, dict):
        errors.append(f"{at}app: must be an [app] table")
    elif isinstance(app, dict):
        for key, value in app.items():
            if key not in SCREEN_KEYS or key == "strip":
                warnings.append(f"{at}app.{key}: unknown key (strip does not apply to an app)")
            elif key == "header" and value not in ("full", "compact", "large"):
                errors.append(f"{at}app.header: one of full, compact, large")
            elif key == "list" and isinstance(value, dict) and (
                value.get("mark") in ("grid", "tile") or value.get("axis") == "horizontal"):
                warnings.append(f"{at}app.list: an app's list is always vertical rows; drawn as one")
            elif key == "decor":
                for d in value:
                    file_ref(folder, d.get("image"), f"{at}app.decor")
    for key, subs in (("glass", {"fill", "border", "highlight", "blur"}),
                      ("focus_ring", {"color", "width"}), ("gradient", {"from", "to", "angle"})):
        if key in t:
            if not isinstance(t[key], dict):
                errors.append(f"{at}{key}: must be an inline table {{ {', '.join(sorted(subs))} }}")
                continue
            for sub in t[key]:
                if sub not in subs:
                    warnings.append(f"{at}{key}.{sub}: unknown key")
    for screen, spec in SCREEN_TABLES.items():
        table = t.get(screen)
        if table is None:
            continue
        if not isinstance(table, dict):
            errors.append(f"{at}{screen}: must be a [{screen}] table")
            continue
        for key, value in table.items():
            if key in THEME_TOP and key not in spec:
                errors.append(f"{at}{screen}.{key}: {misplaced}")
            elif key not in spec:
                warnings.append(f"{at}{screen}.{key}: unknown key (ignored by the launcher)")
            elif isinstance(spec[key], set) and value not in spec[key]:
                errors.append(f"{at}{screen}.{key}: one of {', '.join(sorted(spec[key]))} (else the default is used)")
            elif spec[key] == "color" and not (isinstance(value, str) and COLOR.match(value)):
                errors.append(f"{at}{screen}.{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
            elif spec[key] == "clock" and not isinstance(value, dict):
                if not isinstance(value, (int, float)) or not 0.04 <= value <= 0.16:
                    errors.append(f"{at}{screen}.{key}: a size from 0.04 to 0.16, or a rectangle with size inside")
            elif spec[key] == "backdrop":
                ok = isinstance(value, dict) and all(
                    k in ("blur", "opacity") and isinstance(v, (int, float)) for k, v in value.items())
                if not ok:
                    errors.append(f"{at}{screen}.{key}: {{ blur, opacity }} numbers (blur 0..0.2, opacity 0..1)")
            elif spec[key] in ("rect", "progress", "clock"):
                if spec[key] == "progress" and isinstance(value, str):
                    if value not in ("bar", "ring"):
                        errors.append(f"{at}{screen}.{key}: \"bar\", \"ring\" or a rectangle")
                    continue
                r = value if isinstance(value, dict) else {}
                full = all(isinstance(r.get(c), (int, float)) and 0 <= r[c] <= 1 for c in "xywh")
                if not full or r["x"] + r["w"] > 1 or r["y"] + r["h"] > 1:
                    errors.append(f"{at}{screen}.{key}: needs x, y, w, h fractions with x+w <= 1 and y+h <= 1")
        if screen == "settings":
            if table.get("title") == "below" and table.get("layout") != "sidebar":
                warnings.append(f"{at}settings.title: \"below\" only takes effect with layout = \"sidebar\"")
            for name in (table.get("icon_colors") or {}):
                if name not in SETTINGS_PAGES:
                    warnings.append(f"{at}settings.icon_colors.{name}: unknown page")
    for name, frame in (t.get("frames") or {}).items():
        if name not in FRAMES:
            warnings.append(f"{at}frames.{name}: unknown frame name, ignored")
        for key in frame:
            if key in THEME_TOP:
                errors.append(f"{at}frames.{name}.{key}: {misplaced}")
            elif key not in ("image", "slice", "scale", "pad", "tile"):
                warnings.append(f"{at}frames.{name}.{key}: unknown key")
        file_ref(folder, frame.get("image"), f"{at}frames.{name}.image")
    views = t.get("view") or {}
    for vid, view in views.items():
        if not isinstance(view, dict):
            continue
        view = inherited_view(views, vid, view, f"{at}view.{vid}")
        if vid != "lista" and "name" in view:
            names(view["name"], f"{at}view.{vid}.name")
        for key in view:
            if key in THEME_TOP and key not in ("name",):
                errors.append(f"{at}view.{vid}.{key}: a top-level key written after a [table] header; move it above the first header")
            elif key not in ("name", "systems", "games", "home", "base"):
                warnings.append(f"{at}view.{vid}.{key}: unknown key")
        home = view.get("home")
        if isinstance(home, dict):
            for key in home:
                if key not in HOME_KEYS:
                    warnings.append(f"{at}view.{vid}.home.{key}: unknown key")
            for d in home.get("decor") or []:
                file_ref(folder, d.get("image"), f"{at}view.{vid}.home.decor")
            for shelf, own in (home.get("shelves") or {}).items():
                if isinstance(own, dict) and "progress" in own:
                    warnings.append(f"{at}view.{vid}.home.shelves.{shelf}.progress: not a key (no progress data; removed in 3.1)")
        elif home is not None and not isinstance(home, bool):
            errors.append(f"{at}view.{vid}.home: true or [view.{vid}.home.*] tables")
        for screen in ("systems", "games"):
            for key, value in (view.get(screen) or {}).items():
                if key == "el":
                    check_scene(folder, view, screen, value, f"{at}view.{vid}.{screen}.el")
                    continue
                if key == "remove":
                    continue
                # header and status are a screen's keys as well as tables.
                if key in THEME_TOP and key not in SCREEN_KEYS:
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


def merge(base: dict, over: dict) -> dict:
    """The launcher's merge: tables key by key, anything else (lists too)
    replaced whole."""
    out = dict(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def with_includes(folder: Path, t: dict, open_files: list) -> dict:
    """`include = [...]`: the files under `t`, as if written in it; `t` wins,
    and of two included files the later one. Up to 4 deep, no cycles."""
    listed = t.pop("include", None)
    if listed is None:
        return t
    names = [listed] if isinstance(listed, str) else (
        [n for n in listed if isinstance(n, str)] if isinstance(listed, list) else [])
    if not names:
        warnings.append("include: must name files (\"parts/a.toml\" or a list); ignored")
        return t
    under: dict = {}
    for name in names:
        p = Path(name)
        if p.is_absolute() or ".." in p.parts:
            warnings.append(f"include {name!r}: must be a path inside the theme folder; ignored")
            continue
        path = (folder / p).resolve()
        if not path.is_file():
            warnings.append(f"include {name!r}: no such file in the theme folder; ignored")
            continue
        if path.suffix.lower() != ".toml":
            warnings.append(f"include {name!r}: not a .toml file (the store does not install it)")
        if path in open_files:
            warnings.append(f"include {name!r}: includes itself again; ignored")
            continue
        if len(open_files) > MAX_DEPTH:
            warnings.append(f"include {name!r}: files include others at most {MAX_DEPTH} deep; ignored")
            continue
        try:
            part = tomllib.loads(path.read_text("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
            errors.append(f"{name}: not valid TOML: {e}")
            continue
        under = merge(under, with_includes(folder, part, open_files + [path]))
    return merge(under, t)


def check_options(t: dict):
    """[options.<id>]: rows in Settings › Appearance whose choices swap [vars]."""
    options = t.get("options")
    if options is None:
        return
    if not isinstance(options, dict):
        warnings.append("options: must hold [options.<id>] tables; ignored")
        return
    known = t.get("vars") if isinstance(t.get("vars"), dict) else {}
    good = 0
    for oid, option in sorted(options.items()):
        at = f"options.{oid}"
        if not PLAIN_ID.match(oid):
            warnings.append(f"{at}: an option id has only letters, digits, _ and -; ignored")
            continue
        if not isinstance(option, dict):
            warnings.append(f"{at}: must be a table; ignored")
            continue
        for key in option:
            if key not in ("name", "default", "choices"):
                warnings.append(f"{at}.{key}: unknown key (name, default, choices)")
        choices = option.get("choices")
        if not isinstance(choices, dict):
            warnings.append(f"{at}: needs a choices table; ignored")
            continue
        ids = []
        for cid, choice in sorted(choices.items()):
            cat = f"{at}.choices.{cid}"
            if not PLAIN_ID.match(cid) or not isinstance(choice, dict):
                warnings.append(f"{cat}: must be a table under a plain id; ignored")
                continue
            if len(ids) == MAX_CHOICES:
                warnings.append(f"{cat}: an option has at most {MAX_CHOICES} choices; ignored")
                break
            ids.append(cid)
            for key in choice:
                if key not in ("name", "vars"):
                    warnings.append(f"{cat}.{key}: unknown key (name, vars)")
            if "name" in choice:
                names(choice["name"], f"{cat}.name")
            else:
                warnings.append(f"{cat}: no name; the row shows the id {cid!r}")
            cvars = choice.get("vars", {})
            if not isinstance(cvars, dict):
                warnings.append(f"{cat}.vars: must be a table; ignored")
                continue
            for name, value in cvars.items():
                if not isinstance(value, (str, int, float, bool)):
                    warnings.append(f"{cat}.vars.{name}: must be text, a number or true/false; ignored")
                elif name not in known:
                    warnings.append(f"{cat}.vars.{name}: not in [vars]; give it a value there "
                                    "(the one of the other choices)")
        if len(ids) < 2:
            warnings.append(f"{at}: needs at least two choices; ignored")
            continue
        if "default" in option and option["default"] not in ids:
            warnings.append(f"{at}.default: names no choice; the first one ({ids[0]}) is used")
        if "name" not in option:
            warnings.append(f"{at}: no name; the Appearance row shows the id {oid!r}")
        else:
            names(option["name"], f"{at}.name")
            label = option["name"]
            labels = label.values() if isinstance(label, dict) else [label]
            for text in labels:
                if isinstance(text, str) and text.strip().casefold() in APPEARANCE_ROWS:
                    warnings.append(f"{at}.name: {text!r} is already a row of Settings › Appearance; "
                                    "two rows with one name would do different things. Name what the "
                                    "option changes in this theme")
        good += 1
        if good > MAX_OPTIONS:
            warnings.append(f"{at}: a theme has at most {MAX_OPTIONS} options; ignored")


def inherited_view(views: dict, vid: str, view: dict, at: str, depth: int = 0) -> dict:
    """A view with base = "<other>": the other's screens with this one's
    tables over them (same element id: fields changed; remove = [...])."""
    for screen in ("systems", "games"):
        own = view.get(screen)
        if isinstance(own, dict) and "remove" in own and "base" not in view and depth == 0:
            warnings.append(f"{at}.{screen}.remove: only works in a view with base = \"<other view>\"")
    base = view.get("base")
    if base is None:
        return view
    if not isinstance(base, str) or base == vid or not isinstance(views.get(base), dict):
        warnings.append(f"{at}.base: names no other view of this theme; ignored")
        return {k: v for k, v in view.items() if k != "base"}
    if depth >= MAX_DEPTH:
        warnings.append(f"{at}.base: views inherit at most {MAX_DEPTH} deep; ignored")
        return {k: v for k, v in view.items() if k != "base"}
    out = dict(inherited_view(views, base, views[base], f"view.{base}", depth + 1))
    out.pop("name", None)
    out.pop("base", None)
    for key, value in view.items():
        if key == "base":
            continue
        if key in ("systems", "games") and isinstance(value, dict):
            screen = dict(out.get(key) or {}) if isinstance(out.get(key), dict) else {}
            elements = [dict(e) for e in screen.pop("el", []) if isinstance(e, dict)]
            remove = value.get("remove")
            if remove is not None:
                listed = [r for r in remove if isinstance(r, str)] if isinstance(remove, list) else []
                if not listed:
                    warnings.append(f"{at}.{key}.remove: must list element ids; ignored")
                for rid in listed:
                    before = len(elements)
                    elements = [e for e in elements if e.get("id") != rid]
                    if len(elements) == before:
                        warnings.append(f"{at}.{key}.remove: no inherited element {rid!r}")
            for e in value.get("el") or []:
                same = next((x for x in elements if isinstance(e, dict) and e.get("id")
                             and x.get("id") == e.get("id")), None)
                if same is not None:
                    same.update(e)
                else:
                    elements.append(e)
            for k, v in value.items():
                if k not in ("el", "remove"):
                    screen[k] = merge(screen[k], v) if isinstance(v, dict) and isinstance(screen.get(k), dict) else v
            if elements:
                screen["el"] = elements
            out[key] = screen
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out


def substitute(node, vars: dict):
    """[vars] written in, as the launcher does: a value that is exactly
    "$name" becomes the variable (with its type), ${name} inside a string its
    text. Data names (${system}, ${game.name}...) are left for the screen."""
    if isinstance(node, dict):
        return {k: substitute(v, vars) for k, v in node.items() if k != "vars"} | (
            {"vars": node["vars"]} if "vars" in node else {})
    if isinstance(node, list):
        return [substitute(v, vars) for v in node]
    if isinstance(node, str):
        if node.startswith("$") and not node.startswith("${") and node[1:] in vars:
            return vars[node[1:]]
        def text(m):
            name = m.group(1)
            if name in vars and name not in EL_DATA:
                v = vars[name]
                return str(v).lower() if isinstance(v, bool) else str(v)
            return m.group(0)
        return DATA_REF.sub(text, node)
    return node


def own_vars(t: dict, at: str):
    v = t.get("vars", {})
    if not isinstance(v, dict):
        errors.append(f"{at}vars: must be a [vars] table")
        return {}
    for name, value in v.items():
        if not isinstance(value, (str, int, float, bool)):
            warnings.append(f"{at}vars.{name}: must be text, a number or true/false; ignored")
        if name.split(".")[0] in ("system", "game", "list", "item", "aspect"):
            warnings.append(f"{at}vars.{name}: a data name; ${{{name}}} always means the data")
    return {k: x for k, x in v.items() if isinstance(x, (str, int, float, bool))}


def unresolved(node, at: str):
    """A "$name" left after substitution names no variable."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k != "vars":
                unresolved(v, f"{at}.{k}" if at else k)
    elif isinstance(node, list):
        for n, v in enumerate(node):
            unresolved(v, f"{at}[{n}]")
    elif isinstance(node, str) and re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", node):
        warnings.append(f"{at}: {node} is no variable in [vars]; the text stays as written")


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_text_data(text, at: str):
    if not isinstance(text, str):
        return
    for name in DATA_REF.findall(text):
        if name in EL_PICTURES:
            warnings.append(f"{at}: ${{{name}}} is a picture, not text; use it in an image's src")
        elif name in EL_CLIPS:
            warnings.append(f"{at}: ${{{name}}} is a clip, not text; use it in a video's src")
        elif name not in EL_DATA:
            warnings.append(f"{at}: unknown data ${{{name}}} (written as it is)")


def check_scene(folder: Path, view: dict, screen: str, items, at: str):
    """A free screen: the [[...el]] elements of a view's systems or games."""
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        errors.append(f"{at}: must be [[{at}]] tables")
        return
    lists = videos = 0
    for n, item in enumerate(items):
        here = f"{at}[{n}]"
        kind = item.get("kind")
        base = item.get("base")
        if base is not None and kind is None:
            where, _, eid = base.rpartition(".") if isinstance(base, str) else ("", "", "")
            pool = (view.get(where or screen) or {}).get("el") or []
            found = [e for e in pool if isinstance(e, dict) and e.get("id") == eid]
            if not found:
                warnings.append(f"{here}.base: no element {base!r} in this view; element ignored")
                continue
            kind = found[0].get("kind")
            item = {k: v for k, v in found[0].items() if k != "id"} | item
        if kind not in EL_KINDS:
            errors.append(f"{here}.kind: one of {', '.join(sorted(EL_KINDS))}; element ignored")
            continue
        for key in item:
            if key not in EL_COMMON and key not in EL_KINDS[kind]:
                warnings.append(f"{here}.{key}: unknown key for kind = \"{kind}\" (ignored)")
        if kind in EL_COLLECTIONS:
            lists += 1
            if lists > 1:
                warnings.append(f"{here}: a screen has one list, carousel or grid; this one is ignored")
                continue
        if kind == "video" and videos:
            warnings.append(f"{here}: a screen plays one video; this one is ignored")
            continue
        r = item.get("rect")
        if r is not None:
            if not isinstance(r, dict) or any(k not in "xywh" or not number(v) for k, v in r.items()):
                errors.append(f"{here}.rect: {{ x, y, w, h }} numbers (screen fractions)")
            elif any(abs(r.get(c, 0)) > 2 for c in "xy") or any(r.get(c, 1) > 4 for c in "wh"):
                errors.append(f"{here}.rect: use screen fractions, not pixels")
        a = item.get("anchor")
        if a is not None and a not in EL_ANCHORS and not (
                isinstance(a, list) and len(a) == 2 and all(number(v) for v in a)):
            errors.append(f"{here}.anchor: one of {', '.join(sorted(EL_ANCHORS))} or [x, y]")
        for key, lo, hi in (("z", -1000, 1000), ("opacity", 0, 1), ("rotate", -360, 360),
                            ("size", 0.005 if kind == "rating" else 0.01, 0.3), ("line", 0.8, 3),
                            ("radius", 0, 0.5),
                            ("scale", 0.25, 8), ("empty_opacity", 0, 1),
                            ("spacing", 0, 1 if kind in ("carousel", "grid") else 0.2),
                            ("label_size", 0.01, 0.3), ("star_size", 0.005, 0.3)):
            v = item.get(key)
            if v is not None and (not number(v) or not lo <= v <= hi):
                hint = "; sizes are fractions of the screen height" if key in ("size", "radius") else ""
                errors.append(f"{here}.{key}: a number from {lo} to {hi}{hint}")
        for key, words in EL_WORDS.items():
            if key in item and item[key] not in words:
                errors.append(f"{here}.{key}: one of {', '.join(sorted(words))}")
        for key in ("color", "fill", "border", "tint", "badge", "letter_color", "empty",
                    "label_color", "divider"):
            v = item.get(key)
            if v is not None and not (isinstance(v, str) and COLOR.match(v)):
                errors.append(f"{here}.{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
        for key in ("enter", "select"):
            if key in item:
                check_anim(item[key], f"{here}.{key}", 0.3 if key == "enter" else 0.18)
        when = item.get("when")
        if when is not None:
            if not isinstance(when, dict):
                errors.append(f"{here}.when: a table {{ system, aspect, has }}")
            else:
                for k in when:
                    if k not in ("system", "aspect", "has"):
                        warnings.append(f"{here}.when.{k}: unknown key (system, aspect, has)")
                for v in ([when["aspect"]] if isinstance(when.get("aspect"), str) else when.get("aspect") or []):
                    if v not in ASPECTS:
                        warnings.append(f"{here}.when.aspect: unknown shape {v}")
                for v in ([when["has"]] if isinstance(when.get("has"), str) else when.get("has") or []):
                    if v not in EL_DATA and v not in EL_PICTURES and v not in EL_CLIPS:
                        warnings.append(f"{here}.when.has: unknown data {v}")
        texts = [(item.get("text"), f"{here}.text")]
        if kind == "text":
            if not isinstance(item.get("text"), str):
                errors.append(f"{here}.text: required text; element ignored")
            check_font(folder, item.get("font"), f"{here}.font")
        if kind == "image":
            src = item.get("src")
            src = [src] if isinstance(src, str) else (src if isinstance(src, list) else [])
            fb = item.get("fallback")
            for p in src + ([fb] if isinstance(fb, str) else []):
                if p in EL_CLIPS:
                    warnings.append(f"{here}.src: {p} is a clip; use it in kind = \"video\"")
            fixed = [p for p in src + ([fb] if isinstance(fb, str) else [])
                     if isinstance(p, str) and p and "${" not in p and p not in EL_PICTURES
                     and p not in EL_CLIPS]
            for p in fixed:
                if p.startswith("/") or ".." in Path(p).parts:
                    errors.append(f"{here}: {p!r} must be a relative path inside the theme")
            live = len(fixed) < len(src) + (1 if isinstance(fb, str) else 0)
            ft = item.get("fallback_text")
            if not src and fb is None and ft is None:
                errors.append(f"{here}.src: names no picture; element ignored")
            elif fixed and not live and ft is None and not any((folder / p).is_file() for p in fixed):
                errors.append(f"{here}.src: none of {', '.join(fixed)} exists")
            for p in src:
                check_text_data(p, f"{here}.src")
            if isinstance(ft, dict):
                for key in ft:
                    if key not in EL_TEXT:
                        warnings.append(f"{here}.fallback_text.{key}: unknown key")
                texts.append((ft.get("text"), f"{here}.fallback_text.text"))
                check_font(folder, ft.get("font"), f"{here}.fallback_text.font")
            elif isinstance(ft, str):
                texts.append((ft, f"{here}.fallback_text"))
        if kind in ("rating", "fields"):
            for key in ("star", "star_half", "star_empty"):
                if key in item and "${" not in str(item[key]):
                    file_ref(folder, item[key], f"{here}.{key}")
            if item.get("align") not in (None, "left", "center", "right"):
                errors.append(f"{here}.align: left, center or right")
        if kind == "rating" and item.get("value") not in (None, "game.rating"):
            warnings.append(f"{here}.value: only game.rating has stars; the launcher uses it")
        if kind == "fields":
            check_font(folder, item.get("font"), f"{here}.font")
            check_font(folder, item.get("label_font"), f"{here}.label_font")
            row = item.get("row")
            if row is not None and (not number(row) or not 0.01 <= row <= 1):
                errors.append(f"{here}.row: a number from 0.01 to 1 (fraction of the screen height)")
            rows = item.get("rows")
            if not isinstance(rows, list) or not rows:
                errors.append(f"{here}.rows: a list of {{ label, value }}; element ignored")
                rows = []
            for m, line in enumerate(rows):
                at_row = f"{here}.rows[{m}]"
                if not isinstance(line, dict):
                    errors.append(f"{at_row}: must be {{ label, value }}; ignored")
                    continue
                for key in line:
                    if key not in ("label", "value", "rating"):
                        warnings.append(f"{at_row}.{key}: unknown key (label, value, rating)")
                if "value" not in line and "rating" not in line:
                    errors.append(f"{at_row}: needs a value or a rating; ignored")
                elif "value" not in line and line["rating"] != "game.rating":
                    warnings.append(f"{at_row}.rating: only game.rating has stars; the launcher uses it")
                texts.append((line.get("label"), f"{at_row}.label"))
                texts.append((line.get("value"), f"{at_row}.value"))
        if kind == "list":
            check_font(folder, item.get("font"), f"{here}.font")
            if item.get("align") not in (None, "left", "center", "right"):
                errors.append(f"{here}.align: left, center or right")
            sel = item.get("selected")
            if isinstance(sel, dict):
                for key in sel:
                    if key not in ("height", "fill", "color", "frame"):
                        warnings.append(f"{here}.selected.{key}: unknown key (height, fill, color, frame)")
                for key in ("fill", "color"):
                    if key in sel and not (isinstance(sel[key], str) and COLOR.match(sel[key])):
                        errors.append(f"{here}.selected.{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
                check_slices(folder, sel.get("frame"), f"{here}.selected.frame")
            elif sel is not None and not number(sel):
                errors.append(f"{here}.selected: a row height or {{ height, fill, color, frame }}")
        if kind in ("carousel", "grid"):
            check_collection(folder, item, kind, screen, here, texts)
        if kind == "video" and check_video(folder, item, here):
            videos += 1
        if kind == "frame":
            if not isinstance(item.get("image"), str):
                errors.append(f"{here}.image: a theme picture; element ignored")
            elif "${" not in item["image"]:
                file_ref(folder, item["image"], f"{here}.image")
        if kind == "panel" and item.get("style") not in (None, "plain", "glass"):
            errors.append(f"{here}.style: plain or glass")
        if kind == "hints" and item.get("style") not in (None, "filled", "outline", "text"):
            errors.append(f"{here}.style: filled, outline or text")
        for text, where in texts:
            check_text_data(text, where)
    if items and lists == 0:
        warnings.append(f"{at}: no list, carousel or grid; the d-pad moves through a list nobody sees")


def check_anim(a, at: str, duration: float):
    """enter / select (20261125.20), as the launcher reads them."""
    if not isinstance(a, dict):
        warnings.append(f"{at}: must be a table {{ from, distance, fade, scale, duration, delay, ease }}; ignored")
        return
    for key in a:
        if key not in ANIM_KEYS:
            warnings.append(f"{at}.{key}: unknown key ({', '.join(sorted(ANIM_KEYS))})")
    side = a.get("from", "none")
    if side not in ("none", "left", "right", "top", "bottom"):
        warnings.append(f"{at}.from: left, right, top, bottom or none")
        side = "none"
    if a.get("ease", "out") not in ("out", "in-out", "linear"):
        warnings.append(f"{at}.ease: out, in-out or linear")
    if "fade" in a and not isinstance(a["fade"], bool):
        warnings.append(f"{at}.fade: true or false")
    nums = {}
    for key, default, lo, hi in (("distance", 0.04, 0, 1), ("scale", 1, 0.1, 4),
                                 ("duration", duration, 0.05, ANIM_MAX), ("delay", 0, 0, ANIM_MAX)):
        v = a.get(key, default)
        if not number(v) or not lo <= v <= hi:
            unit = " seconds" if key in ("duration", "delay") else ""
            warnings.append(f"{at}.{key}: a number from {lo} to {hi}{unit}; clamped")
            v = default if not number(v) else min(max(v, lo), hi)
        nums[key] = v
    if nums["delay"] + nums["duration"] > ANIM_MAX + 1e-4:
        warnings.append(f"{at}: delay + duration is {nums['delay'] + nums['duration']:.2f} s, past "
                        f"{ANIM_MAX} s; the launcher cuts the delay")
    moves = side != "none" and nums["distance"] > 0
    if not moves and a.get("fade", True) is False and nums["scale"] == 1:
        warnings.append(f"{at}: neither moves, fades nor grows; ignored")


def check_video(folder: Path, item: dict, here: str) -> bool:
    """kind = "video" (20261125.18). False when the launcher drops it."""
    def sources(key):
        v = item.get(key)
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [s for s in v if isinstance(s, str)]
        warnings.append(f"{here}.{key}: a source or a list of them; ignored")
        return []
    src, still = [], []
    for p in sources("src"):
        if p in EL_CLIPS:
            src.append(p)
        elif p in EL_PICTURES or p in EL_DATA:
            warnings.append(f"{here}.src: {p} is no clip (game.video, system.video or a file); ignored")
        elif not p or p.startswith("/") or ".." in Path(p).parts:
            warnings.append(f"{here}.src: {p!r} must be a path inside the theme; ignored")
        else:
            src.append(p)
            if "${" not in p and not (folder / p).is_file():
                warnings.append(f"{here}.src: {p} does not exist in the theme")
    for p in sources("fallback"):
        if p in EL_CLIPS:
            warnings.append(f"{here}.fallback: {p} is a clip; the fallback is a picture")
        elif p in EL_PICTURES:
            still.append(p)
        elif not p or p.startswith("/") or ".." in Path(p).parts:
            warnings.append(f"{here}.fallback: {p!r} must be a path inside the theme; ignored")
        else:
            still.append(p)
            if "${" not in p and not (folder / p).is_file():
                warnings.append(f"{here}.fallback: {p} does not exist in the theme")
    if not src and not still:
        errors.append(f"{here}.src: names no video; element ignored")
        return False
    if item.get("mute") is False:
        warnings.append(f"{here}.mute = false: videos play without sound for now; muted")
    for key in ("mute", "loop"):
        if key in item and not isinstance(item[key], bool):
            errors.append(f"{here}.{key}: true or false")
    d = item.get("delay")
    if d is not None and (not number(d) or not 0 <= d <= 10):
        errors.append(f"{here}.delay: seconds, a number from 0 to 10")
    return True


def check_slices(folder: Path, frame, at: str):
    """A nine-slice theme picture { image, slice, scale, tile }."""
    if frame is None:
        return
    if not isinstance(frame, dict) or not isinstance(frame.get("image"), str):
        errors.append(f"{at}: {{ image, slice, scale, tile }} with a theme picture")
        return
    for key in frame:
        if key not in ("image", "slice", "scale", "tile"):
            warnings.append(f"{at}.{key}: unknown key (image, slice, scale, tile)")
    if "${" not in frame["image"]:
        file_ref(folder, frame["image"], f"{at}.image")


def check_collection(folder: Path, item: dict, kind: str, screen: str, here: str, texts: list):
    """kind = "carousel" or "grid" (20261125.17)."""
    of = item.get("of")
    if of is not None and of != screen:
        warnings.append(f"{here}.of: this screen's items are its {screen}; the launcher uses them")
    if kind == "carousel":
        if item.get("axis") not in (None, "horizontal", "vertical"):
            errors.append(f"{here}.axis: horizontal or vertical")
        if item.get("align") not in (None, "left", "center", "right"):
            errors.append(f"{here}.align: left, center or right")
        for key, lo, hi in (("visible", 1, 15), ("reflection", 0, 1)):
            v = item.get(key)
            if v is not None and (not number(v) or not lo <= v <= hi):
                errors.append(f"{here}.{key}: a number from {lo} to {hi}")
        wheel = item.get("wheel")
        if wheel is not None:
            if not isinstance(wheel, dict):
                errors.append(f"{here}.wheel: {{ angle, pivot }}; ignored")
            else:
                for key in wheel:
                    if key not in ("angle", "pivot"):
                        warnings.append(f"{here}.wheel.{key}: unknown key (angle, pivot)")
                a = wheel.get("angle")
                if a is not None and (not number(a) or not -90 <= a <= 90):
                    errors.append(f"{here}.wheel.angle: degrees from -90 to 90")
                pv = wheel.get("pivot")
                if pv is not None and not (isinstance(pv, list) and len(pv) == 2
                                           and all(number(v) and -50 <= v <= 50 for v in pv)):
                    errors.append(f"{here}.wheel.pivot: [x, y] in item sizes, -50 to 50")
    else:
        for key in ("columns", "rows"):
            v = item.get(key)
            if v is not None and (not number(v) or not 1 <= v <= 8):
                errors.append(f"{here}.{key}: a number from 1 to 8")
    sel = item.get("selected")
    if sel is not None:
        if not isinstance(sel, dict):
            errors.append(f"{here}.selected: {{ scale, opacity, tint, color, frame }}; ignored")
        else:
            for key in sel:
                if key not in ("scale", "opacity", "tint", "color", "frame"):
                    warnings.append(f"{here}.selected.{key}: unknown key (scale, opacity, tint, color, frame)")
            for key, lo, hi in (("scale", 0.25, 4), ("opacity", 0, 1)):
                v = sel.get(key)
                if v is not None and (not number(v) or not lo <= v <= hi):
                    errors.append(f"{here}.selected.{key}: a number from {lo} to {hi}")
            for key in ("tint", "color"):
                if key in sel and not (isinstance(sel[key], str) and COLOR.match(sel[key])):
                    errors.append(f"{here}.selected.{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
            fr = sel.get("frame")
            if isinstance(fr, dict) and "image" in fr:
                check_slices(folder, fr, f"{here}.selected.frame")
            elif isinstance(fr, dict):
                for key in fr:
                    if key not in ("color", "width", "radius"):
                        warnings.append(f"{here}.selected.frame.{key}: unknown key (color, width, radius)")
                if "color" in fr and not (isinstance(fr["color"], str) and COLOR.match(fr["color"])):
                    errors.append(f"{here}.selected.frame.color: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
                w = fr.get("width")
                if w is not None and (not number(w) or not 0.001 <= w <= 0.05):
                    errors.append(f"{here}.selected.frame.width: 0.001 to 0.05 of the screen height")
            elif fr is not None:
                errors.append(f"{here}.selected.frame: {{ color, width, radius }} or {{ image, slice }}")
    fav = item.get("favorite")
    if isinstance(fav, dict):
        for key in fav:
            if key not in ("image", "corner", "size", "tint"):
                warnings.append(f"{here}.favorite.{key}: unknown key (image, corner, size, tint)")
        if fav.get("corner") not in (None, "top-left", "top-right", "bottom-left", "bottom-right"):
            errors.append(f"{here}.favorite.corner: top-left, top-right, bottom-left or bottom-right")
        v = fav.get("size")
        if v is not None and (not number(v) or not 0.05 <= v <= 1):
            errors.append(f"{here}.favorite.size: 0.05 to 1 of the picture's height")
        if isinstance(fav.get("image"), str) and "${" not in fav["image"]:
            file_ref(folder, fav["image"], f"{here}.favorite.image")
    elif fav is not None and not isinstance(fav, bool):
        errors.append(f"{here}.favorite: true, false or {{ image, corner, size, tint }}")
    tpl = item.get("item")
    if tpl is None:
        return
    if not isinstance(tpl, dict):
        errors.append(f"{here}.item: a table {{ image, logo, text, ... }}; the screen's pictures are used")
        return
    for key in tpl:
        if key not in EL_ITEM:
            warnings.append(f"{here}.item.{key}: unknown key ({', '.join(sorted(EL_ITEM))})")
    for key in ("image", "logo"):
        src = tpl.get(key)
        src = [src] if isinstance(src, str) else (src if isinstance(src, list) else [])
        for p in src:
            if not isinstance(p, str):
                continue
            check_text_data(p, f"{here}.item.{key}")
            if p not in EL_PICTURES and "${" not in p:
                if p.startswith("/") or ".." in Path(p).parts:
                    errors.append(f"{here}.item.{key}: {p!r} must be a relative path inside the theme")
                elif not (folder / p).is_file():
                    warnings.append(f"{here}.item.{key}: {p} does not exist; the item's name shows")
    for key, lo, hi in (("w", 0.01, 1), ("h", 0.01, 1), ("radius", 0, 0.5), ("size", 0.01, 0.3)):
        v = tpl.get(key)
        if v is not None and (not number(v) or not lo <= v <= hi):
            errors.append(f"{here}.item.{key}: a number from {lo} to {hi}")
    if tpl.get("fit") not in (None, "contain", "cover", "stretch"):
        errors.append(f"{here}.item.fit: contain, cover or stretch")
    for key in ("color", "fill"):
        if key in tpl and not (isinstance(tpl[key], str) and COLOR.match(tpl[key])):
            errors.append(f"{here}.item.{key}: must be \"#RRGGBB\" or \"#RRGGBBAA\"")
    check_font(folder, tpl.get("font"), f"{here}.item.font")
    texts.append((tpl.get("text"), f"{here}.item.text"))


def check_font(folder: Path, font, at: str):
    if font is None:
        return
    if not isinstance(font, str):
        errors.append(f"{at}: a face (regular, semibold, bold, mono) or a .ttf file")
    elif font.lower().endswith((".ttf", ".otf")):
        file_ref(folder, font, at)
    elif font not in EL_FACES:
        errors.append(f"{at}: a face (regular, semibold, bold, mono) or a .ttf file")


LAUNCHER_PACKAGE = "0.1.0"  # CARGO_PKG_VERSION of the launcher today; not the system version (v3.1.0)


def check_min_launcher(value):
    """min_launcher above the launcher package refuses the install."""
    if value is None:
        return
    def parts(v):
        return [int(p) if p.strip().isdigit() else 0 for p in str(v).split(".")]
    wanted, ours = parts(value), parts(LAUNCHER_PACKAGE)
    n = max(len(wanted), len(ours))
    wanted += [0] * (n - len(wanted))
    ours += [0] * (n - len(ours))
    if wanted > ours:
        errors.append(f"min_launcher = {value!r}: above the launcher package version "
                      f"({LAUNCHER_PACKAGE}), so the store refuses the install; this is not "
                      "the system version (v3.1.0). Use \"0.1.0\" or leave it out")


def check_theme(folder: Path):
    src = folder / "theme.toml"
    if src.stat().st_size > 64 << 10:
        errors.append("theme.toml: larger than 64 KiB")
    try:
        t = tomllib.loads(src.read_text("utf-8"))
    except tomllib.TOMLDecodeError as e:
        errors.append(f"theme.toml: not valid TOML: {e}")
        return
    t = with_includes(folder, t, [src.resolve()])
    check_options(t)
    for key in t:
        if key not in THEME_TOP:
            warnings.append(f"unknown top-level key {key} (ignored by the launcher)")
    top_vars = own_vars(t, "")
    aspects = t.get("aspect")
    t = substitute(t, top_vars)
    if isinstance(aspects, dict):
        t["aspect"] = {
            shape: substitute(table, top_vars | own_vars(table, f"aspect.{shape}."))
            if isinstance(table, dict) else table
            for shape, table in aspects.items()}
    unresolved(t, "")
    check_min_launcher(t.get("min_launcher"))
    if "name" not in t:
        errors.append("name: missing (the store refuses the theme)")
    else:
        names(t["name"], "name")
    if "description" in t:
        names(t["description"], "description")
    misplaced = "a top-level key written after a [table] header; move it above the first header"
    for key in ("font", "font_semibold", "font_bold", "font_mono", "font_mono_medium"):
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
            if size and max(size) > 1920:
                warnings.append(f"{rel}: {size[0]}x{size[1]}; larger than any screen, slow to load on the device")
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
    "system": {"cpu-profile", "cpu-tune", "perf-limits", "boot-tuning", "brightness", "volume", "wifi", "screenshot"},
}
# API 4: systems the launcher refuses for permissions.install (already at the manifest).
REFUSED_INSTALL = {"tools", "windows", "setup", "shell", "moonlight", "music", "idtech", "scummvm", "j2me"}
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


def check_install(value, api):
    if api != 4:
        errors.append("permissions.install needs api_version = 4")
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append("permissions.install: a list of system folders and/or \"ports\"")
        return
    for v in value:
        if v in REFUSED_INSTALL:
            warnings.append(f"permissions.install: {v} will be refused (runs as root or is not an emulated system)")


def check_app(folder: Path, m: dict, api, run: dict):
    app = m.get("app")
    if app is None:
        return
    if api != 4:
        warnings.append("[app]: ignored below api_version = 4")
        return
    if run.get("mode") != "daemon":
        warnings.append("[app]: needs run.mode = \"daemon\"; the module will have no app")
    if not app.get("home"):
        warnings.append("[app].home: missing, the module will have no app")
    art = app.get("art")
    if art:
        p = folder / art
        if art.startswith("/") or ".." in Path(art).parts or not p.is_file():
            errors.append(f"[app].art: {art} must be a file inside the module")
        elif p.stat().st_size > 1024 * 1024:
            errors.append("[app].art: larger than 1 MiB")
    if not m.get("permissions", {}).get("install") and not app.get("home"):
        warnings.append("[app]: no permissions.install; the app can show screens but not install games")


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
    check_min_launcher(m.get("min_launcher"))
    api = m.get("api_version")
    if api not in (1, 2, 3, 4):
        errors.append("api_version: 1, 2, 3 or 4")
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
        if key == "install":
            check_install(value, api)
            continue
        if key not in ALLOWED:
            errors.append(f"permissions.{key}: unknown or reserved permission (fatal)")
            continue
        for v in value:
            if v not in ALLOWED[key]:
                errors.append(f"permissions.{key}: {v} is not allowed")
    if api == 1 and (perms.get("launch") or any(perms.get(k) for k in ("config_write", "hooks", "system"))):
        errors.append("permissions: config_write, hooks, system and launch need api_version = 2")
    for system in ("cpu-tune", "perf-limits", "boot-tuning"):
        if system in (perms.get("system") or []) and isinstance(api, int) and api < 3:
            errors.append(f"permissions.system: {system} needs api_version = 3")
    check_app(folder, m, api, run)
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
    icons = {m.get("icon"), m.get("app", {}).get("icon")} | {e.get("icon") for k in ("tiles", "shortcuts", "widgets") for e in start.get(k, [])}
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
