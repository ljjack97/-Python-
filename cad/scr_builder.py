"""SCR script builder — minimal, reliable format.

No -LAYER commands (they disrupt SCR execution in some AutoCAD versions).
All geometry drawn on layer 0.
"""

from typing import List
from cad.code_generator import CodeGenerator


class ScrBuilder:
    """Assembles a minimal, working AutoCAD .scr script."""

    def __init__(self, layer_manager, code_generator: CodeGenerator):
        self.cg = code_generator

    def build(self, geometry_list: List, scale_factor: float) -> str:
        sections: List[str] = []

        # Drawing commands only — no layers, no setup
        sections.append(self.cg.generate(geometry_list, scale_factor))

        # ZOOM Extents at the end
        sections.append("ZOOM\nE\n")

        return "\n".join(sections)
