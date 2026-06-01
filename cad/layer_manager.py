"""Layer manager — defines layers and generates SCR setup commands.

Uses newline-separated format (one param per line, blank line = exit).
This is the most reliable format for multi-option commands like -LAYER.
"""

from typing import Dict, List, Tuple
from config.cad_templates import ACAD_COLORS


class LayerManager:
    """Manages AutoCAD layer definitions."""

    LAYERS: List[Tuple[str, int, str]] = [
        ("Walls",      ACAD_COLORS["white"],    "Walls"),
        ("Doors",      ACAD_COLORS["red"],      "Doors"),
        ("Windows",    ACAD_COLORS["blue"],     "Windows"),
        ("Lines",      ACAD_COLORS["white"],    "Lines"),
        ("Circles",    ACAD_COLORS["green"],    "Circles"),
        ("Arcs",       ACAD_COLORS["cyan"],     "Arcs"),
        ("PolyLines",  ACAD_COLORS["white"],    "PolyLines"),
        ("Trees",      ACAD_COLORS["green"],    "Trees"),
        ("Paths",      ACAD_COLORS["yellow"],   "Paths"),
        ("Water",      ACAD_COLORS["cyan"],     "Water"),
    ]

    def __init__(self):
        self._layer_dict: Dict[str, int] = {name: color for name, color, _ in self.LAYERS}

    def get_layer_setup_commands(self) -> str:
        """Generate layer creation commands in newline SCR format.

        Format per layer:
            -LAYER
            N
            <name>
                    <- blank line exits New sub-prompt
            C
            <color>
            <name>
                    <- blank line exits -LAYER
        """
        lines = []
        for name, color, desc in self.LAYERS:
            lines.append(f"-LAYER\nN\n{name}\n\nC\n{color}\n{name}\n")
        # Switch to Walls as default
        lines.append(f"-LAYER\nS\nWalls\n\n")
        return "\n".join(lines)

    def get_layer_switch_command(self, name: str) -> str:
        """Layer switch: -LAYER S <name> Enter Enter"""
        return f"-LAYER\nS\n{name}\n\n"

    def get_all_layer_names(self) -> List[str]:
        return [name for name, _, _ in self.LAYERS]

    def get_layer_color(self, name: str) -> int:
        return self._layer_dict.get(name, ACAD_COLORS["white"])
