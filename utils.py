# Copyright © 2025 Brandon Namgoong.
# Licensed under the GNU General Public License v3.0.
# Made for ICS3U1.

"Module containing utility objects such as colors, path resolving, high scores, and versioning, among others."

from pathlib import Path
from json import load, dump
import sys

#-----------------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------------

versionString: str   = "VERSION 1.1" # string to display on corner for version

# colors
uiColors: dict       = {
    "text": (40, 51, 56),
    "primary": (54, 117, 227),
    "accent": (245, 65, 0),
    "button_normal": (20, 184, 166),
    "button_selected": (251, 191, 36)
}

blockColors: dict    = [ # 400
    (248, 113, 113), # red
    (251, 146, 60), # orange
    (251, 191, 36), # amber
    (250, 204, 21), # yellow
    (163, 230, 53), # lime
    (74, 222, 128), # green
    (52, 211, 153), # emerald
    (45, 212, 191), # teal
    (34, 211, 238), # cyan
    (56, 189, 248), # sky
    (96, 165, 250), # blue
    (129, 140, 248), # indigo
    (167, 139, 250), # violet
    (192, 132, 252), # purple
    (232, 121, 249), # fuschia
    (244, 114, 182), # pink
    (251, 113, 133) # rose
]

# level unlock thresholds
thresholds: dict     = {
    "square": 0,
    "triangle": 0,
    "rectangle": ["square", 5],

    "hexagon": ["rectangle", 10],
    "caret": ["hexagon", 10],
    "slant": ["hexagon", 10],

    "pentagon": ["slant", 15],
    "en": ["pentagon", 15],
    "kay": ["pentagon", 15],

    "mta_arrow": ["en", 10],
    "pi": ["kay", 10],
    "double_u": ["mta_arrow", 15]
}

# friendly level names
friendlyNames: dict  = {
    "square": "Square",
    "triangle": "Triangle",
    "rectangle": "Rectangle",

    "hexagon": "Long Hexagon",
    "caret": "Caret",
    "slant": "Slanted Quad",

    "pentagon": "Pentagon Hat",
    "en": "Uppercase N",
    "kay": "Lowercase K",

    "mta_arrow": "MTA Arrow",
    "pi": "Pi",
    "double_u": "Uppercase W"
}

#-----------------------------------------------------------------------------
# public functions
#-----------------------------------------------------------------------------

def unifiedPath(relativePath: str) -> Path:
    """
    Returns the absolute path of the specified relative path.
    Resolves to the parent `sys._MEIPASS` if filepath is frozen from pyinstaller.
    """
    try:
        return Path(sys._MEIPASS) / Path(relativePath)
    except AttributeError: # if not a pyinstaller path
        return Path(__file__).resolve().parent / Path(relativePath)

def checkHighScoreJson():
    "Checks if highscore file exists. Creates a new blank one if not."
    try:
        with open(unifiedPath("highscores.json"), "r"): pass # try to open
    except (FileNotFoundError, ValueError):
        with open(unifiedPath("highscores.json"), "w") as f:
            dump(
                { # template json
                    "square": 0, "triangle": 0, "rectangle": 0,
                    "hexagon": 0, "caret": 0, "slant": 0,
                    "pentagon": 0, "en": 0, "kay": 0,
                    "mta_arrow": 0, "pi": 0, "double_u": 0
                },
                f, indent = 4
            )

def getHighScore(shapeName: str) -> int:
    "Returns the high score for a given shape level."
    with open(unifiedPath("highscores.json"), "r") as f:
        return load(f)[shapeName]

def setHighScore(shapeName: str, highScore: int):
    "Sets a new high score for a given shape level."
    with open(unifiedPath("highscores.json"), "r") as f:
        scores: dict = load(f)
    scores[shapeName] = highScore
    with open(unifiedPath("highscores.json"), "w") as f:
        dump(scores, f, indent = 4)