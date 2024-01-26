#!/usr/bin/env python
# coding=utf-8

# This file is part of fretboard_extension.

# fretboard_extension is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# fretboard_extension is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with fretboard_extension. If not, see <https://www.gnu.org/licenses/>.
"""
Simple extension for inkscape to draw guitar scale, fretboard boundaries and fret lines
"""

import math
from typing import Union
import inkex
from inkex import Group, PathElement, Polygon, Style

class FretboardExtension(inkex.GenerateExtension):
    """FretboardExtension designer class"""

    def __init__(self):
        super().__init__()
        self.midline_y = 0
        self.fretboard_angle_tan = 0.0

    def add_arguments(self, pars):
        pars.add_argument("--scale", type=float, help="Scale (in)")
        pars.add_argument("--strings", type=int, help="Number of strings")
        pars.add_argument("--strings-color", type=int, help="Strings color")
        pars.add_argument("--nut-width", type=float, help="Nut total width")
        pars.add_argument("--nut-string-space", type=float, help="Distance between outer strings")
        pars.add_argument("--bridge-width", type=float, help="Bridge width (mm)")
        pars.add_argument("--ignore-bridge-width", type=inkex.Boolean, help="Ignore bridge width, compute it")
        pars.add_argument("--bridge-string-space", type=float, help="Distance between 2 strings on bridge (mm)")
        pars.add_argument("--frets", type=int, help="Number of frets")
        pars.add_argument("--frets-color", type=int, help="frets color")
        pars.add_argument("--strings-gauges", type=str, help="List of string gauges")
        pars.add_argument("--frets-tang-width", type=float, help="Frets tang width (mm)")
        pars.add_argument("--frets-crown-width", type=float, help="Frets crown width (mm)")
        pars.add_argument("--ignore-custom-width", type=inkex.Boolean, help="Ignore string gauges, don't draw frets crowns")
        pars.add_argument("--debug", type=inkex.Boolean, help="Show debug messages")

    def generate(self):
        self.debug_msg("Debug messages\n===========\n")
        self.debug_msg(f"strings_color: {self.options.strings_color}")

        self.strings_color = f"#{hex(self.options.strings_color)[2:-2]}"
        self.strings_opacity = (self.options.strings_color & 255) / 255
        self.debug_msg(f"strings_color: {self.options.strings_color}, {self.strings_color}, opacity: {self.strings_opacity}")
        self.frets_color = f"#{hex(self.options.frets_color)[2:-2]}"
        self.midline_y = self.set_midline()
        self.debug_msg(f"midline_y: {self.midline_y}")

        if not self.options.ignore_bridge_width:
            bridge_width = self.options.bridge_width
        else:
            bridge_width = self.options.bridge_string_space * (self.options.strings - 1) + self.options.nut_width - self.options.nut_string_space
            self.debug_msg(f"bridge_width: {bridge_width}")

        self.fretboard_angle_tan = (bridge_width / 2 - self.options.nut_width / 2) / self._to_mm(self.options.scale)
        self.fretboard_angle = math.atan(self.fretboard_angle_tan)
        self.debug_msg(f"fretboard_angle: {self.fretboard_angle} rad, {self.fretboard_angle * 180 / math.pi}°")

        fretboard = Group.new(label="fretboard")

        fretboard_scale_outline_points = [
            f"0,{self.midline_y - bridge_width / 2}",
            f"{self._to_mm(self.options.scale)},{self.midline_y - self.options.nut_width / 2}",
            f"{self._to_mm(self.options.scale)},{self.midline_y + self.options.nut_width / 2}",
            f"0,{self.midline_y + bridge_width / 2}"
        ]
        fretboard_scale_outline = Group.new(label="fretboard_scale_outline")
        fretboard_scale_outline.append(
            Polygon(
                points=" ".join(fretboard_scale_outline_points),
                attrib=Style(
                    style={
                        "fill": None,
                        "stroke-width": 0.1,
                        "stroke": "#000000"
                    }
                )
            )
        )
        last_fret_x = self._to_mm(self.options.scale - self.distance_to_nut(self.options.scale, self.options.frets + 1))
        last_fret_y1 = self.midline_y - bridge_width / 2 + last_fret_x * self.fretboard_angle_tan
        last_fret_y2 = self.midline_y + bridge_width / 2 - last_fret_x * self.fretboard_angle_tan
        fretboard_outline_points = [
            f"{last_fret_x},{last_fret_y1}",
            f"{self._to_mm(self.options.scale)},{self.midline_y - self.options.nut_width / 2}",
            f"{self._to_mm(self.options.scale)},{self.midline_y + self.options.nut_width / 2}",
            f"{last_fret_x},{last_fret_y2}"
        ]
        fretboard_outline = Group.new(label="fretboard_outline")
        fretboard_outline.append(
            Polygon(
                points=" ".join(fretboard_outline_points),
                attrib=Style(
                    style={
                        "fill": None,
                        "stroke-width": 0.1,
                        "stroke": "#ff0000"
                    }
                )
            )
        )

        strings_gauges = self.options.strings_gauges.split(",")
        self.debug_msg(f"strings_gauges: {strings_gauges}, len(strings_gauges): {len(strings_gauges)}")
        
        if  self.options.ignore_custom_width:
            strings_gauges = [10] * self.options.strings
        elif len(strings_gauges) == self.options.strings:
            for sg in range(len(strings_gauges)):
                try:
                    strings_gauges[sg] = int(strings_gauges[sg])
                except Exception as e:
                    self.debug_msg(f"strings_gauges[sg], {e}")
            strings_gauges.reverse()
        else:
            strings_gauges = [10] * self.options.strings
            self.debug_msg(f"gauges list items don't match strings number\n{strings_gauges}")

        strings_lines = Group.new(label="strings")
        for string_i in range(0, self.options.strings):
            string_x1 = 0
            string_y1 = self.midline_y - self.options.bridge_string_space * (self.options.strings - 1) / 2 + self.options.bridge_string_space * string_i
            string_x2 = self._to_mm(self.options.scale)
            string_y2 = self.midline_y - self.options.nut_string_space / 2 + self.options.nut_string_space / (self.options.strings - 1) * string_i
            string = PathElement()
            string.set_path(f"M {string_x1} {string_y1} L {string_x2} {string_y2}")
            string.style.update({
                            "fill": None,
                            "stroke-opacity": self.strings_opacity,
                            "stroke-width": strings_gauges[string_i] / 100 * 2.54,
                            "stroke": self.strings_color or "#00ff00"
                        })
            strings_lines.append(
                string
            )
        
        frets_tang_lines = Group.new(label="fret_tangs")
        frets_crown_lines = Group.new(label="fret_crowns")
        last_case = False
        for fret_i in range(self.options.frets + 2):
            if fret_i == self.options.frets + 1:
                last_case = True
            fret_x = self._to_mm(self.options.scale - self.distance_to_nut(self.options.scale, fret_i))
            fret_y1 = self.midline_y - bridge_width / 2 + fret_x * self.fretboard_angle_tan
            fret_y2 = self.midline_y + bridge_width / 2 - fret_x * self.fretboard_angle_tan
            if not (self.options.ignore_custom_width or last_case):
                fret_crown = PathElement()
                fret_crown.set_path(f"M {fret_x} {fret_y1} L {fret_x} {fret_y2}")
                fret_crown.set_id(f"fret_{fret_i}")
                fret_crown.style.update({
                                "fill": None,
                                "stroke-width": self.options.frets_crown_width,
                                "stroke": self.frets_color or "#e0e0e0"
                            })
                frets_crown_lines.append(fret_crown)
            fret_tang = PathElement()
            fret_tang.set_path(f"M {fret_x} {fret_y1} L {fret_x} {fret_y2}")
            fret_tang.set_id(f"fret_{fret_i}")
            fret_tang.style.update({
                            "fill": None,
                            "stroke-width": self.options.frets_tang_width if not last_case else 0.1,
                            "stroke": "#999999" if not last_case else "#ff0000"
                        })
            frets_tang_lines.append(fret_tang)

        fretboard.append(fretboard_scale_outline)
        fretboard.append(fretboard_outline)
        fretboard.append(frets_tang_lines)
        fretboard.append(frets_crown_lines)
        fretboard.append(strings_lines)
        return fretboard
    
    def set_midline(self) -> int:
        return 10 * int(self.options.bridge_width / 10)
    
    def add_midline(self, y) -> int:
        return y + self.midline_y

    @classmethod
    def _to_mm(self, inches: Union[int, float]) -> float:
        return inches * 25.4
    
    @staticmethod
    def distance_to_nut(scale, n):
        # d = s – (s / (2 ^ (n / 12)))
        # d = distance from nut
        # s = scale length
        # n = fret number
        return scale - (scale / (pow(2, (n / 12))))
    
    def debug_msg(self, msg):
        if self.options.debug:
            self.msg(msg=msg)


if __name__ == '__main__':
    FretboardExtension().run()
