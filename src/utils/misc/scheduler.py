# %%
"""
Questions:
1) Best idle floor?
2) Best number of lifts, given number of floors?
3) Best arrangement of lifts (e.g. partitions of high/low floors)?
4) Different goals (e.g. shortest average service time / least distance travelled)?
"""
import time
import random as rd
import numpy as np
import pandas as pd
import plotly.express as px

CAPACITY = 12 # number of people
MAX_SPEED = 5 # metres per second
ACCEL = 2 # metres per second per second
DECEL = -2 # metres per second per second
MIN_DWELL = 8 # seconds

class Lift:
    def __init__(self, capacity=CAPACITY, max_speed=MAX_SPEED, accel=ACCEL, decel=DECEL, min_dwell=MIN_DWELL) -> None:
        self.capacity = capacity
        self.max_speed = max_speed
        self.accel = accel
        self.decel = decel
        self.min_dwell = min_dwell
        pass

class Person:
    def __init__(self) -> None:
        pass
    
class Floor:
    def __init__(self) -> None:
        pass
    
class Building:
    def __init__(self) -> None:
        self.shaft_distance = 100
        pass
    