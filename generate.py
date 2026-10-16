#!/usr/bin/env python3
"""Builds the Osaka Jade PhpStorm theme from the IDE's own Islands Dark theme.

Islands Dark is read straight from the installed IDE so the theme keeps every
Islands setting, then each color is swapped for its Osaka Jade counterpart.

    ./generate.py [path/to/PhpStorm.app]
"""

import copy
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "src", "themes")

# Omarchy's Osaka Jade palette, the same values Ghostty and Zed use.
BG = "111c18"
BG_DARK = "0c1512"
FG = "C1C497"
FG_BRIGHT = "F7E8B2"
# Lighter than Omarchy's #53685B so comments and line numbers stay readable.
COMMENT = "6b8474"
SURFACE_1 = "1a2a22"
SURFACE_2 = "23372B"
SURFACE_3 = "32473B"
MUTED = "81B8A8"
RED = "FF5345"
RED_DIM = "b33a30"
GREEN = "549e6a"
GREEN_BRIGHT = "63b07a"
GREEN_DARK = "459451"
# Ghostty's brighter green, so keywords stand apart from the green background.
KEYWORD = "5ccd86"
JADE = "509475"
PINK = "D2689C"
CYAN = "2DD5B7"
YELLOW = "E5C736"
TEAL_LIGHT = "ACD4CF"
TEAL = "75bbb3"
AQUA = "8CD3CB"
BROWN = "a2734b"
INLAY = "7e9481"

# UI ramps. Islands derives every surface, border and text color from these.
GRAYS = {
    10: "#111c18", 20: "#14211c", 30: "#192821", 40: "#20332a",
    50: "#283d32", 60: "#32473b", 70: "#56705f", 80: "#718a79",
    90: "#7b9480", 100: "#88a08a", 110: "#9bac8f", 120: "#abb792",
    130: "#c1c497", 140: "#d4d3a5", 150: "#e6deae", 160: "#f7e8b2",
}
JADES = {
    10: "#0f1d18", 20: "#12241d", 30: "#152b22", 40: "#1b3a2d",
    50: "#22493a", 60: "#2a5a46", 70: "#336b53", 80: "#3f7f62",
    90: "#509475", 100: "#6aae8f", 110: "#81b8a8", 120: "#9cc8bb",
    130: "#acd4cf", 140: "#c3e0dc", 150: "#d9ebe8", 160: "#eef6f4",
}

UI_TOKENS = {
    "editor-text": f"#{FG}",
    "text-link": f"#{CYAN}",
    "text-error": f"#{RED}",
    "text-warning": f"#{YELLOW}",
    "text-success": f"#{GREEN_BRIGHT}",
    "popup-completion-match-text": f"#{CYAN}",
    "search-match-bg": "#8f7d2e",
    "tab-file-color-mask-bg": f"#{BG}80",
    "transparent": f"#{BG}00",
    "got-it-text-link": f"#{CYAN}",
    "text-disabled": "gray-70",
}

# Hard coded colors inside Islands' "ui" section.
UI_HEX = {
    "#6F737A": "#718a79", "#393B40": f"#{SURFACE_2}", "#2B2D30": f"#{SURFACE_1}",
    "#43454A": f"#{SURFACE_3}", "#868A91": "#88a08a", "#CED0D6": "#abb792",
    "#26282C": "#192821", "#212326": "#14211c", "#DFE1E5": "#d4d3a5",
    "#B4B8BF": "#95a88c", "#9FA2A8": "#88a08a", "#73767C": "#718a79",
    "#3574F0": "#3f7f62", "#5FAD65": f"#{GREEN_BRIGHT}", "#575A5C": f"#{SURFACE_3}",
    "#1E1F22": f"#{BG}", "#191A1C": f"#{BG}",
}

# Islands Dark editor colors mapped to Osaka Jade, keyed by what they mean there.
SCHEME_HEX = {
    # text and syntax
    "bcbec4": FG, "ced0d6": FG, "c9cbd6": FG, "dfe1e5": FG_BRIGHT,
    "56a8f5": CYAN, "57aaf7": CYAN, "0da19e": CYAN, "83acfc": CYAN, "548af7": CYAN,
    "165e70": CYAN, "3887a1": CYAN,
    "cf8e6d": KEYWORD, "7ec482": GREEN_BRIGHT, "73bd79": GREEN_BRIGHT, "42bd77": GREEN_BRIGHT,
    "f75464": RED, "fa6675": RED, "cf514e": RED, "d64d5b": RED, "de6a66": RED,
    "e88f89": "db9f9c",
    "c77dbb": MUTED, "c77dba": MUTED, "9da0a8": MUTED, "abadb3": MUTED, "849fbf": MUTED,
    "d5b778": GREEN, "67a37c": GREEN,
    "2fbaa3": AQUA, "9c9cff": AQUA, "16baac": AQUA,
    "6aab73": YELLOW, "e0bb65": YELLOW, "8bb33d": YELLOW, "73ad2b": YELLOW, "f2c55c": YELLOW,
    "ba9752": YELLOW, "c29e4a": YELLOW, "70aeff": YELLOW,
    "5c92ff": TEAL, "32b8af": TEAL, "56c1d6": TEAL,
    "b3ae60": BROWN, "b2ae60": BROWN, "42c3d4": BROWN, "857042": BROWN, "d69a6b": BROWN,
    "b189f5": PINK, "2aacb8": PINK, "9e6294": PINK, "ba6387": PINK, "fa7db1": PINK, "cf84cf": PINK,
    "7a7e85": COMMENT, "5f826b": COMMENT, "68a67e": COMMENT, "6f737a": COMMENT, "6f7587": COMMENT,
    "757a85": COMMENT, "6a707a": COMMENT, "6b6c73": COMMENT, "84868c": COMMENT, "8d9199": COMMENT,
    "4b5059": COMMENT,
    "868991": INLAY, "868a91": INLAY, "858a94": INLAY, "727782": INLAY,
    "a1a3ab": FG, "f7e9c6": FG_BRIGHT, "5b786a": JADE, "72d6d6": CYAN, "8c5b65": RED_DIM,
    "467ff2": JADE, "3d7a49": GREEN_DARK, "549159": GREEN_DARK,
    "375fad": "a68f2a", "52433d": "3a3a1f",
    # coverage gutter
    "375239": "3b6f4a", "5e3838": "7a2d27", "5e4d33": "6e5233",
    # backgrounds
    "191a1c": BG, "1f2024": "182620", "1e1f22": BG,
    "2b2d30": SURFACE_1, "27282b": "15221d", "26292c": "15221d", "27292b": "15221d",
    "393b40": SURFACE_2, "343539": SURFACE_2, "373b39": SURFACE_2, "323438": SURFACE_1,
    "43454a": SURFACE_3, "3f4045": SURFACE_3, "4e5157": SURFACE_3, "394d3f": SURFACE_3,
    "1a3b2d": "1b3a2d", "273552": "1b3a2d", "25324d": "1b3a2d", "293c40": "152620",
    "35538f": "2a5a46", "2a5091": "2a5a46", "2d543f": "2e5444", "114957": "2e5444",
    "40252b": "3a1f1c", "402929": "3a1f1c", "402f33": "4a2a3a", "66313f": "5a2a44",
    "2f5194": "2a5a46", "2d416b": "22493a", "283754": "1b3a2d", "242d42": "172b22", "22252e": "13201b",
}

FONT_PLAIN, FONT_BOLD, FONT_ITALIC = 0, 1, 2

# Attributes set explicitly, so PHP, Blade, JS and CSS read like the Zed theme.
ATTRIBUTES = {
    "TEXT": {"FOREGROUND": FG, "BACKGROUND": BG},
    "DEFAULT_IDENTIFIER": {"FOREGROUND": FG},
    "DEFAULT_KEYWORD": {"FOREGROUND": KEYWORD},
    "DEFAULT_STRING": {"FOREGROUND": YELLOW},
    "DEFAULT_VALID_STRING_ESCAPE": {"FOREGROUND": BROWN},
    "DEFAULT_NUMBER": {"FOREGROUND": PINK},
    "DEFAULT_CONSTANT": {"FOREGROUND": PINK, "FONT_TYPE": FONT_PLAIN},
    "DEFAULT_PREDEFINED_SYMBOL": {"FOREGROUND": PINK},
    "DEFAULT_LINE_COMMENT": {"FOREGROUND": COMMENT, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_BLOCK_COMMENT": {"FOREGROUND": COMMENT, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_DOC_COMMENT": {"FOREGROUND": COMMENT, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_DOC_COMMENT_TAG": {"FOREGROUND": GREEN, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_DOC_COMMENT_TAG_VALUE": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_OPERATION_SIGN": {"FOREGROUND": TEAL},
    "DEFAULT_BRACES": {"FOREGROUND": MUTED},
    "DEFAULT_BRACKETS": {"FOREGROUND": MUTED},
    "DEFAULT_PARENTHS": {"FOREGROUND": MUTED},
    "DEFAULT_COMMA": {"FOREGROUND": MUTED},
    "DEFAULT_SEMICOLON": {"FOREGROUND": MUTED},
    "DEFAULT_DOT": {"FOREGROUND": MUTED},
    "DEFAULT_CLASS_NAME": {"FOREGROUND": AQUA},
    "DEFAULT_CLASS_REFERENCE": {"FOREGROUND": AQUA},
    "DEFAULT_INTERFACE_NAME": {"FOREGROUND": AQUA},
    "DEFAULT_FUNCTION_DECLARATION": {"FOREGROUND": CYAN},
    "DEFAULT_FUNCTION_CALL": {"FOREGROUND": CYAN},
    "DEFAULT_INSTANCE_METHOD": {"FOREGROUND": CYAN},
    "DEFAULT_STATIC_METHOD": {"FOREGROUND": CYAN, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_INSTANCE_FIELD": {"FOREGROUND": MUTED},
    "DEFAULT_STATIC_FIELD": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "DEFAULT_LOCAL_VARIABLE": {"FOREGROUND": FG},
    "DEFAULT_PARAMETER": {"FOREGROUND": FG},
    "DEFAULT_GLOBAL_VARIABLE": {"FOREGROUND": PINK},
    "DEFAULT_METADATA": {"FOREGROUND": BROWN},
    "DEFAULT_LABEL": {"FOREGROUND": BROWN},
    "DEFAULT_TAG": {"FOREGROUND": GREEN},
    "DEFAULT_ATTRIBUTE": {"FOREGROUND": BROWN},
    "DEFAULT_ENTITY": {"FOREGROUND": BROWN},
    "DEFAULT_TEMPLATE_LANGUAGE_COLOR": {"FOREGROUND": FG},
    "TODO_DEFAULT_ATTRIBUTES": {"FOREGROUND": YELLOW, "FONT_TYPE": FONT_BOLD | FONT_ITALIC, "ERROR_STRIPE_COLOR": YELLOW},
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES": {"BACKGROUND": "22493a", "ERROR_STRIPE_COLOR": JADE},
    "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": {"BACKGROUND": "4a2a3a", "ERROR_STRIPE_COLOR": PINK},
    "SEARCH_RESULT_ATTRIBUTES": {"BACKGROUND": "2e5444", "ERROR_STRIPE_COLOR": CYAN},
    "TEXT_SEARCH_RESULT_ATTRIBUTES": {"BACKGROUND": "4d4415", "EFFECT_COLOR": YELLOW, "ERROR_STRIPE_COLOR": YELLOW},
    "MATCHED_BRACE_ATTRIBUTES": {"FOREGROUND": FG_BRIGHT, "BACKGROUND": SURFACE_3, "FONT_TYPE": FONT_BOLD},
    "HYPERLINK_ATTRIBUTES": {"FOREGROUND": CYAN, "EFFECT_COLOR": CYAN, "EFFECT_TYPE": 1},
    "INLINE_PARAMETER_HINT": {"FOREGROUND": INLAY, "BACKGROUND": SURFACE_1},
    "INLAY_DEFAULT": {"FOREGROUND": INLAY, "BACKGROUND": SURFACE_1},

    # PHP
    "PHP_KEYWORD": {"FOREGROUND": KEYWORD},
    "PHP_TAG": {"FOREGROUND": KEYWORD},
    "PHP_CLOSING_TAG": {"FOREGROUND": KEYWORD},
    "PHP_PRIMITIVE_TYPE_HINT": {"FOREGROUND": KEYWORD},
    "PHP_VAR": {"FOREGROUND": FG},
    "PHP_VAR_VAR": {"FOREGROUND": FG},
    "PHP_PARAMETER": {"FOREGROUND": FG},
    "PHP_THIS_VAR": {"FOREGROUND": PINK},
    "PHP_INSTANCE_FIELD": {"FOREGROUND": MUTED},
    "PHP_PRIVATE_INSTANCE_FIELD": {"FOREGROUND": MUTED},
    "PHP_PROTECTED_INSTANCE_FIELD": {"FOREGROUND": MUTED},
    "PHP_STATIC_FIELD": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "PHP_FUNCTION": {"FOREGROUND": CYAN},
    "PHP_FUNCTION_CALL": {"FOREGROUND": CYAN},
    "PHP_INSTANCE_METHOD": {"FOREGROUND": CYAN},
    "PHP_PRIVATE_INSTANCE_METHOD": {"FOREGROUND": CYAN},
    "PHP_PROTECTED_INSTANCE_METHOD": {"FOREGROUND": CYAN},
    "PHP_STATIC_METHOD": {"FOREGROUND": CYAN, "FONT_TYPE": FONT_ITALIC},
    "PHP_CLASS": {"FOREGROUND": AQUA},
    "PHP_INTERFACE": {"FOREGROUND": AQUA, "FONT_TYPE": FONT_ITALIC},
    "PHP_ALIAS_REFERENCE": {"FOREGROUND": AQUA},
    "PHP_CONSTANT": {"FOREGROUND": PINK},
    "PHP_NUMBER": {"FOREGROUND": PINK},
    "PHP_STRING": {"FOREGROUND": YELLOW},
    "PHP_HEREDOC_CONTENT": {"FOREGROUND": YELLOW},
    "PHP_HEREDOC_ID": {"FOREGROUND": KEYWORD},
    "PHP_EXEC_COMMAND_ID": {"FOREGROUND": YELLOW},
    "PHP_ESCAPE_SEQUENCE": {"FOREGROUND": BROWN},
    "PHP_INVALID_ESCAPE_SEQUENCE": {"FOREGROUND": RED, "EFFECT_COLOR": RED, "EFFECT_TYPE": 2},
    "PHP_NAMED_ARGUMENT": {"FOREGROUND": BROWN},
    "PHP_ATTRIBUTE": {"FOREGROUND": BROWN},
    "PHP_OPERATION_SIGN": {"FOREGROUND": TEAL},
    "PHP_CONCATENATION": {"FOREGROUND": TEAL},
    "PHP_BRACES": {"FOREGROUND": MUTED},
    "PHP_BRACKETS": {"FOREGROUND": MUTED},
    "PHP_PARENTHESES": {"FOREGROUND": MUTED},
    "PHP_COMMA": {"FOREGROUND": MUTED},
    "PHP_SEMICOLON": {"FOREGROUND": MUTED},
    "PHP_IDENTIFIER": {"FOREGROUND": FG},
    "PHP_COMMENT": {"FOREGROUND": COMMENT, "FONT_TYPE": FONT_ITALIC},
    "PHP_DOC_TAG": {"FOREGROUND": GREEN, "FONT_TYPE": FONT_ITALIC},
    "PHP_DOC_PARAMETER": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "PHP_DOC_IDENTIFIER": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "PHP_DOC_VAR": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "PHP_DOC_PROPERTY_IDENTIFIER": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "PHP_SCRIPTING_BACKGROUND": {},

    # HTML, Blade and XML
    "HTML_TAG": {"FOREGROUND": MUTED},
    "HTML_TAG_NAME": {"FOREGROUND": GREEN},
    "HTML_CUSTOM_TAG_NAME": {"FOREGROUND": AQUA},
    "HTML_ATTRIBUTE_NAME": {"FOREGROUND": BROWN},
    "HTML_ATTRIBUTE_VALUE": {"FOREGROUND": YELLOW},
    "HTML_ENTITY_REFERENCE": {"FOREGROUND": PINK},
    "HTML_COMMENT": {"FOREGROUND": COMMENT, "FONT_TYPE": FONT_ITALIC},
    "XML_TAG": {"FOREGROUND": MUTED},
    "XML_TAG_NAME": {"FOREGROUND": GREEN},
    "XML_CUSTOM_TAG_NAME": {"FOREGROUND": AQUA},
    "XML_ATTRIBUTE_NAME": {"FOREGROUND": BROWN},
    "XML_ATTRIBUTE_VALUE": {"FOREGROUND": YELLOW},

    # JavaScript and TypeScript
    "JS.GLOBAL_VARIABLE": {"FOREGROUND": PINK},
    "JS.GLOBAL_FUNCTION": {"FOREGROUND": CYAN},
    "JS.INSTANCE_MEMBER_FUNCTION": {"FOREGROUND": CYAN},
    "JS.REGEXP": {"FOREGROUND": BROWN},
    "JS.JSX_CLIENT_COMPONENT": {"FOREGROUND": AQUA},

    # CSS and Tailwind
    "CSS.IDENT": {"FOREGROUND": AQUA},
    "CSS.TAG_NAME": {"FOREGROUND": GREEN},
    "CSS.PROPERTY_NAME": {"FOREGROUND": MUTED},
    "CSS.PROPERTY_VALUE": {"FOREGROUND": FG},
    "CSS.FUNCTION": {"FOREGROUND": CYAN},
    "CSS.KEYWORD": {"FOREGROUND": KEYWORD},
    "CSS.NUMBER": {"FOREGROUND": PINK},
    "CSS.STRING": {"FOREGROUND": YELLOW},
    "CSS.URL": {"FOREGROUND": TEAL},
    "CSS.COLOR": {"FOREGROUND": PINK},
    "CSS.IMPORTANT": {"FOREGROUND": RED, "FONT_TYPE": FONT_BOLD},

    # Markdown
    "MARKDOWN.HEADER_LEVEL_1": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.HEADER_LEVEL_2": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.HEADER_LEVEL_3": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.HEADER_LEVEL_4": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.HEADER_LEVEL_5": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.HEADER_LEVEL_6": {"FOREGROUND": FG_BRIGHT, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.BOLD_TEXT": {"FOREGROUND": CYAN, "FONT_TYPE": FONT_BOLD},
    "MARKDOWN.ITALIC_TEXT": {"FOREGROUND": CYAN, "FONT_TYPE": FONT_ITALIC},
    "MARKDOWN.LINK_TEXT": {"FOREGROUND": CYAN},
    "MARKDOWN.LINK_DESTINATION": {"FOREGROUND": TEAL, "FONT_TYPE": FONT_ITALIC},
    "MARKDOWN.CODE_SPAN": {"FOREGROUND": YELLOW, "BACKGROUND": SURFACE_1},
    "MARKDOWN.BLOCK_QUOTE": {"FOREGROUND": MUTED, "FONT_TYPE": FONT_ITALIC},
    "MARKDOWN.LIST_ITEM": {"FOREGROUND": JADE},

    # YAML, JSON and .env
    "YAML_SCALAR_KEY": {"FOREGROUND": MUTED},
    "YAML_SCALAR_VALUE": {"FOREGROUND": YELLOW},
    "YAML_SCALAR_STRING": {"FOREGROUND": YELLOW},
    "YAML_SCALAR_DSTRING": {"FOREGROUND": YELLOW},
    "JSON.PROPERTY_KEY": {"FOREGROUND": MUTED},
    "JSON.KEYWORD": {"FOREGROUND": PINK},
    "DOTENV_KEY": {"FOREGROUND": MUTED},
    "DOTENV_VALUE": {"FOREGROUND": YELLOW},

    # Console, matching the Ghostty palette
    "CONSOLE_NORMAL_OUTPUT": {"FOREGROUND": FG},
    "CONSOLE_SYSTEM_OUTPUT": {"FOREGROUND": MUTED},
    "CONSOLE_ERROR_OUTPUT": {"FOREGROUND": RED},
    "CONSOLE_USER_INPUT": {"FOREGROUND": GREEN_BRIGHT, "FONT_TYPE": FONT_ITALIC},
    "CONSOLE_BLACK_OUTPUT": {"FOREGROUND": BG},
    "CONSOLE_RED_OUTPUT": {"FOREGROUND": RED},
    "CONSOLE_GREEN_OUTPUT": {"FOREGROUND": "5ccd86"},
    "CONSOLE_YELLOW_OUTPUT": {"FOREGROUND": GREEN_DARK},
    "CONSOLE_BLUE_OUTPUT": {"FOREGROUND": JADE},
    "CONSOLE_MAGENTA_OUTPUT": {"FOREGROUND": PINK},
    "CONSOLE_CYAN_OUTPUT": {"FOREGROUND": CYAN},
    "CONSOLE_GRAY_OUTPUT": {"FOREGROUND": FG},
    "CONSOLE_DARKGRAY_OUTPUT": {"FOREGROUND": COMMENT},
    "CONSOLE_RED_BRIGHT_OUTPUT": {"FOREGROUND": "db9f9c"},
    "CONSOLE_GREEN_BRIGHT_OUTPUT": {"FOREGROUND": GREEN_BRIGHT},
    "CONSOLE_YELLOW_BRIGHT_OUTPUT": {"FOREGROUND": YELLOW},
    "CONSOLE_BLUE_BRIGHT_OUTPUT": {"FOREGROUND": TEAL_LIGHT},
    "CONSOLE_MAGENTA_BRIGHT_OUTPUT": {"FOREGROUND": TEAL},
    "CONSOLE_CYAN_BRIGHT_OUTPUT": {"FOREGROUND": AQUA},
    "CONSOLE_WHITE_OUTPUT": {"FOREGROUND": FG_BRIGHT},
}

COLORS = {
    "CARET_COLOR": FG_BRIGHT,
    "CARET_ROW_COLOR": "182620",
    "SELECTION_BACKGROUND": SURFACE_3,
    "SELECTION_FOREGROUND": "",
    "CONSOLE_BACKGROUND_KEY": BG,
    "LINE_NUMBERS_COLOR": COMMENT,
    "LINE_NUMBER_ON_CARET_ROW_COLOR": FG,
    "INDENT_GUIDE": SURFACE_1,
    "SELECTED_INDENT_GUIDE": SURFACE_3,
    "RIGHT_MARGIN_COLOR": SURFACE_2,
    "WHITESPACES": SURFACE_3,
    "ADDED_LINES_COLOR": GREEN_DARK,
    "MODIFIED_LINES_COLOR": "a68f2a",
    "DELETED_LINES_COLOR": RED_DIM,
    "IGNORED_DELETED_LINES_BORDER_COLOR": RED_DIM,
    "FILESTATUS_DELETED": RED_DIM,
    "FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM": RED_DIM,
    "FILESTATUS_IDEA_FILESTATUS_IGNORED": COMMENT,
}


def find_ide(argv):
    if len(argv) > 1 and argv[1]:
        return argv[1]
    apps = glob.glob(os.path.expanduser("~/Applications/PhpStorm*.app")) + glob.glob("/Applications/PhpStorm*.app")
    if not apps:
        sys.exit("No PhpStorm app found. Pass its path as the first argument.")
    # Prefer the EAP (PhpStorm Light) when both are installed.
    return sorted(apps, key=lambda path: "Light" not in path)[0]


def read_islands(ide):
    jar = os.path.join(ide, "Contents", "lib", "intellij.platform.resources.jar")
    with zipfile.ZipFile(jar) as archive:
        theme = json.loads(archive.read("themes/islands/ManyIslandsDark.theme.json"))
        scheme = archive.read("themes/islands/IslandSchemeDark.xml").decode()
    return theme, scheme


def build_theme(theme):
    colors = theme["colors"]
    for step, value in GRAYS.items():
        colors[f"gray-{step}"] = value
    for step, value in JADES.items():
        colors[f"blue-{step}"] = value
    colors.update(UI_TOKENS)

    ui = json.dumps(theme["ui"])
    for old, new in UI_HEX.items():
        ui = re.sub(re.escape(old), new, ui, flags=re.IGNORECASE)
    theme["ui"] = json.loads(ui)

    theme["name"] = "Osaka Jade"
    theme["author"] = "Josh Donnell"
    theme["editorScheme"] = "/themes/OsakaJade.xml"
    return theme


def remap(value, unmapped):
    if not value:
        return value
    key = value.lower()
    alpha = ""
    if len(key) == 8:
        key, alpha = key[:6], key[6:]
    key = key.zfill(6)
    if key in SCHEME_HEX:
        return SCHEME_HEX[key] + alpha
    unmapped.add(value)
    return value


def set_attribute(attributes, name, values):
    for option in attributes.findall("option"):
        if option.get("name") == name:
            attributes.remove(option)
    option = ET.SubElement(attributes, "option", name=name)
    value = ET.SubElement(option, "value")
    for key, val in values.items():
        ET.SubElement(value, "option", name=key, value=str(val))


def build_scheme(source):
    root = ET.fromstring(source)
    root.set("name", "Osaka Jade")
    unmapped = set()

    for option in root.iter("option"):
        if option.get("name") in ("FONT_TYPE", "EFFECT_TYPE"):
            continue
        value = option.get("value")
        if value and re.fullmatch(r"[0-9A-Fa-f]{5,8}", value):
            option.set("value", remap(value, unmapped))

    colors = root.find("colors")
    for name, value in COLORS.items():
        for option in colors.findall("option"):
            if option.get("name") == name:
                colors.remove(option)
        ET.SubElement(colors, "option", name=name, value=value)

    attributes = root.find("attributes")
    for name, values in ATTRIBUTES.items():
        set_attribute(attributes, name, values)

    for group in (colors, attributes):
        group[:] = sorted(group, key=lambda option: option.get("name"))

    if unmapped:
        print("Colors left as Islands had them:", ", ".join(sorted(unmapped)))

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode") + "\n"


def main():
    ide = find_ide(sys.argv)
    theme, scheme = read_islands(ide)
    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "OsakaJade.theme.json"), "w") as file:
        json.dump(build_theme(copy.deepcopy(theme)), file, indent=2)
        file.write("\n")

    with open(os.path.join(OUT, "OsakaJade.xml"), "w") as file:
        file.write(build_scheme(scheme))

    print(f"Generated the theme from {ide}")


if __name__ == "__main__":
    main()
