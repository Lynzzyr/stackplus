# Copyright © 2025 Brandon Namgoong.
# Licensed under the GNU General Public License v3.0.
# Made for ICS3U1.

"""
Module containing functions for interacting with shape JSONs and Polygons.

Some code has been adapted from kickstart ideas from GPT 4o.
"""

from pathlib import Path
from json import load
import numpy as np
import shapely
import random

from utils import unifiedPath

#-----------------------------------------------------------------------------
# globals
#-----------------------------------------------------------------------------

__jsonPath: Path = unifiedPath("res/shapes.json")

#-----------------------------------------------------------------------------
# private functions
#-----------------------------------------------------------------------------

# forces shapes to be wound counterclockwise
def __forceCCW(polygon: shapely.Polygon) -> shapely.Polygon:
    if not polygon.exterior.is_ccw: polygon = shapely.Polygon(polygon.exterior.reverse())
    return polygon

#-----------------------------------------------------------------------------
# public functions
#-----------------------------------------------------------------------------

def allShapes() -> list[str]:
    "Returns a list of all available shape names."
    with open(__jsonPath, "r") as f:
        return list(load(f).keys())

def randomShape() -> str:
    "Returns the name of a shape selected at random from the entire available set."
    with open(__jsonPath, "r") as f:
        return random.choice(list(load(f).keys()))

def get(shapeName: str) -> shapely.Polygon:
    "Returns a Polygon corresponding to the specified shape name."
    with open(__jsonPath, "r") as f:
        return __forceCCW(
            shapely.Polygon(load(f)[shapeName])
        )

def extrude(polygon: shapely.Polygon, depth: float = 1.0) -> dict:
    """
    Extrudes and returns a dictionary containing information about a 3D prism of the given Polygon.
    Specify an optional `depth` to extrude other than the default value of `1.0`.
    
    The dictionary contains 6 keys: `polygon`, `vertices`, `lines`, `bases`, `quads`, and `isConvex`.
    `polygon` contains the original source Polygon.
    `vertices` contains a list of tuple points in 3D space.
    `lines` contains a list of tuple indices connecting pairs of points as lines.
    `bases` contains a list of tuple indices connecting sets of points as the top and bottom of the extruded prism.
    `quads` contains a list of tuple indices connecting quads of points as sides of the extruded prism.
    `isConvex` is a boolean that specifies whether the Polygon is convex or not.
    """
    # ensure 100% winding is CCW before doing ANYTHING
    polygon = __forceCCW(polygon)

    # define other things
    num: int = shapely.count_coordinates(polygon.exterior) - 1 # remove duplicate
    exterior: list = shapely.get_coordinates(polygon.exterior).tolist()[:num]

    # processing
    return {
        "polygon": polygon,
        "vertices": [ # bottom
                (x, y, 0.0) for x, y in exterior[::-1] # bottom reversed for CCW winding when looking at it
            ] + [ # top
                (x, y, depth) for x, y in exterior
            ],
        "lines": [ # bottom
                (i, (i - 1) % num) for i in range(num)
            ] + [ # top
                (i + num, ((i - 1) % num) + num) for i in range(num)
            ] + [ # sides
                (i, -i + (2 * num - 1)) for i in range(num)
            ],
        "bases": [
                tuple([ # bottom
                    i for i in range(num)
                ])
            ] + [
                tuple([ # top
                    i + num for i in range(num)
                ])
            ],
        "quads": [
                (
                    i,                      # BL
                    (i - 1) % num,          # BR
                    (-i % num) + num,       # TR
                    ((-i - 1) % num) + num  # TL
                ) for i in range(num) 
            ],
        "isConvex": bool(shapely.equals(polygon, polygon.convex_hull)) # check if convex by comparison to its convex hull
    }

def spacialTransform(polygon: shapely.Polygon, transformMat: list) -> shapely.Polygon:
    "Calculates and returns the result of a manual transformation of a Polygon based on the given 3-dimensional transformation matrix."
    points = np.array(shapely.get_coordinates(polygon))

    return __forceCCW( # ensure just in case
        shapely.Polygon(
            (
                np.hstack([ # homogenize Nx2 polygon matrix to Nx4 for dot product
                    points,
                    np.zeros((points.shape[0], 1)), # add column of zeros
                    np.ones((points.shape[0], 1)) # add column of ones
                ])
                @ np.array(transformMat)
            )[:, :2]
        )
    )

def andPolygons(polygon1: shapely.Polygon, polygon2: shapely.Polygon) -> shapely.Polygon:
    """
    Calculates and returns the AND operation of both Polygons.
    That is, get the Polygon that is shared by the areas of both specified Polygons.

    If the resulting AND operation returns a MultiPolygon (when multiple areas are shared),
    the Polygon with the largest area will be used.
    """
    result = shapely.intersection(
        polygon1, polygon2,
        grid_size = 0.05
    )

    # check for not polygon, choose largest
    if not isinstance(result, shapely.Polygon):
        largest: shapely.Polygon = shapely.Polygon() # start empty
        try:
            for p in result.geoms:
                if isinstance(p, shapely.Polygon) and p.area > largest.area: # if geom is a polygon and has larger area
                    largest = p
        except AttributeError: # if is a Geometry that is not a collection of geoms
            return shapely.Polygon() # return empty
        return __forceCCW(largest)
    else: return __forceCCW(result)