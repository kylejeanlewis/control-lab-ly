# %% -*- coding: utf-8 -*-
"""
This module holds general mathematical operations for analysis.

Functions:
    intersection
    perpendicular_bisector
"""
# Standard library imports
from __future__ import annotations
from typing import Optional

# Local application imports
print(f"Import: OK <{__name__}>")

def intersection(L1:tuple, L2:tuple) -> tuple[Optional[float], Optional[float]]:
    """
    Get the intersection between two lines

    Args:
        L1 (tuple): line 1
        L2 (tuple): line 2

    Returns:
        tuple[Optional[float], Optional[float]]: x,y values of intersection. (None,None) if intersection not found.
    """
    D  = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x_i = Dx / D
        y_i = Dy / D
        return x_i,y_i
    else:
        return None,None
   
def perpendicular_bisector(pt1:tuple, pt2:tuple) -> tuple[float, float, float]:
    """
    Get the formula of perpendicular bisector between two points

    Args:
        pt1 (tuple): x,y of point 1
        pt2 (tuple): x,y of point 2

    Returns:
        tuple[float, float, float]: rise; run; _value_
    """
    mid = ((pt1[0]+pt2[0])/2, (pt1[1]+pt2[1])/2)
    slope = (pt1[1] - pt2[1]) / (pt1[0] - pt2[0])
    b = -1/slope
    a = mid[1] - b*mid[0]
    # print(f'slope, intercept: {b}, {a}')
    p1 = (0, a)
    p2 = mid
    
    A = (p1[1] - p2[1])
    B = (p2[0] - p1[0])
    C = (p1[0]*p2[1] - p2[0]*p1[1])
    return A, B, -C
