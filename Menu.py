"""
This is the menu file, responsible for keeping track of menu state basically
- Keeps track of sound and music
- Map generation parameters and sliders
- Presets maybe eventually
"""

import random as r


class Menu:
    def __init__(self):
        self.sound = True  # for sound eventually
        self.music = True
        self.starting_year = 0
        self.water_slider = 0  # all sliders go from 0 - 1
        self.temperature_slider = 0
        self.mountain_slider = 0
        self.island_slider = 0
        self.mapsize_slider = 0

    def random_initial_vatiables(self):
        self.water_slider = r.randint(30, 80) / 100  # sets the water/land ratio. Good range(0.4-0.8)
        self.temperature_slider = r.randint(20, 80) / 100  # snow, desert and jungle. Good range(0.2-0.8)
        self.mountain_slider = r.randint(5, 25) / 100  # Good range(0.05-0.25)
        self.island_slider = r.randint(10, 80) / 100  # Good range(0.1 - 0.8)
        self.mapsize_slider = r.randint(1, 2) * 10
        self.starting_year = r.randint(-2000, -1000)  # start on a random year

