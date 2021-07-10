"""
The engine of the game, responsible for
- storing the gamestate
- generating the map
- generating civilizations
- storing civilization data
- game logic
- AI eventually
"""

# TODO: fix/tweak civ expansion to expand more
# TODO: fix inherit and war mechanic to add cities adjacent tiles correctly
# TODO: add split empire in half mechanic
# TODO: river, continent, desert and jungle names

from MapGame import Game
import random as r

# probably needs adjusting
# basetypes: w = water, o = ocean, g = grassland/farmland, h = hills, s = snow, d = desert, j = jungle
# secondary types: f = forested grassland, m = mountains, t = taiga, y = forested snowy hills,
# i = forested hills, a = snowy hills, k = hilly jungle  (add more later?)
tile_to_food = {"a": 1, "y": 2, "t": 4, "m": 1, "i": 5, "h": 3, "f": 8, "g": 10,
                "s": 2, "d": 1, "w": 6, "o": 3, "j": 8, "k": 7}

food_to_tile = {v: k for k, v in tile_to_food.items()}

tile_to_production = {"a": 2, "y": 3, "t": 4, "m": 4, "i": 9, "h": 10, "f": 8, "g": 4,
                      "s": 1, "d": 1, "w": 6, "o": 2, "j": 3, "k": 4}

production_to_tile = {v: k for k, v in tile_to_production.items()}


class gameState:
    def __init__(self, mapsizemultiplier):
        # load screen variables
        self.load_screen_text = ""
        self.load_screen_bar = 0
        self.load_screen = True
        self.mapsize = mapsizemultiplier
        # 16x9 map (144 tiles) each tile has a number representing type of tile:
        # basetypes: w = water, o = ocean, g = grassland/farmland, h = hills, s = snow, d = desert, j = jungle
        # secondary types: f = forested grassland, m = mountains, t = taiga, y = forested snowy hills,
        # i = forested hills, a = snowy hills, k = hilly jungle  (add more later?)
        # -1 = empty tile
        # hill types = h, m, y, i, a, k
        # lowland types = g, s, d, j, f, t
        # forested = f, t, y, i
        # each tile can have up to two types at once
        # Map names for immersion
        self.place_names = []
        self.continent_names_list = []
        self.ocean_names_list = []
        self.river_names_list = []
        self.island_names_list = []
        self.mountain_names_list = []
        self.desert_names_list = []
        self.jungle_names_list = []
        # important gamestate variables:
        self.map = []
        self.civilization_map = []
        self.civ_name_list = []  # list of ALL civ names randomized
        self.civ_name = []  # list of of names with right index
        self.civ_capital_pos = []
        self.civ_color_index = []
        self.civ_area_list = []
        self.civ_cities = []
        self.civ_army_power = []
        self.civ_tech = []
        self.civ_population = []
        self.civ_food = []
        self.civ_production = []
        self.world_event_log = []
        self.protected_cities = []  # a list of city locations with a timer  (50 years) that ticks down
        # eg. , [[13, 6], 2349], ... works as a sort of truce timer, since other civilizations cant go to war with a
        # civ that has a protected city, maybe fix this

    """
    Generating the whole game
    """

    def generate_game(self, water_multiplier, temperature, mountain_multiplier, island_multiplier):
        self.generate_map(water_multiplier, temperature, mountain_multiplier, island_multiplier)
        self.generate_civs()

    """
    Generating a random map that makes sense (e.g. water next to other water tiles, jungle along the equator...)
    """

    def generate_map(self, water_multiplier, temperature, mountain_multiplier, island_multiplier):
        tiles_left = (9 * self.mapsize) * (16 * self.mapsize)
        self.set_map_size()
        self.generate_place_names()
        self.place_random_water(tiles_left, water_multiplier)
        self.place_land()
        self.map_cleanup(1)
        self.set_ocean_tiles()
        self.island_generation(island_multiplier)
        self.place_random_mountains(mountain_multiplier)
        self.place_random_desert_and_jungle(temperature)
        self.place_random_snow(temperature)
        self.place_random_snow(temperature)
        self.set_hills(mountain_multiplier)
        self.set_forest(temperature, water_multiplier)
        self.map_cleanup(3)
        self.set_rivers()
        self.world_event_log.append("The world was created!")

    """
    Helper methods for generating the map:
    """

    def set_map_size(self):
        self.load_screen_text = "Setting map size..."
        for row in range(0, int(9*self.mapsize)):
            c = []
            n = []
            for col in range(0, int(16*self.mapsize)):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                c.append("-")  # tile is empty string at first
                n.append("-")
            self.map.append(c)
            self.place_names.append(n)

    def place_random_water(self, tiles_left, water_multiplier):
        # place 40 - 70 water tiles
        print("Creating water...")
        self.load_screen_text = "Creating water..."
        tiles_to_place = int(tiles_left * water_multiplier)
        fixed_placement = self.mapsize * self.mapsize//8
        tiles = tiles_to_place - fixed_placement
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        attempts = 0
        # print(self.map[0][0][0])
        for i in range(0, fixed_placement):
            x = r.randint(0, 16 * self.mapsize - 1)
            y = r.randint(0, 9 * self.mapsize - 1)
            if self.map[y][x] == "-":
                self.map[y][x] = "w"  # place water tiles randomly
                self.place_names[y][x] = self.ocean_names_list.pop()
            # print(self.map[y][x][0])
        while tiles > 0:  # select a random square on the map, check if a square adjacent has a water tile
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            col = r.randint(0, 16 * self.mapsize - 1)
            row = r.randint(0, 9 * self.mapsize - 1)
            if self.map[row][col] == "-":  # only check empty square
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    # loop over map boundaries
                    if 0 < new_row < 9 * self.mapsize - 1:  # inside longitude boundaries
                        if new_col < 0:
                            new_col = 16 * self.mapsize - 1
                        elif new_col > 16 * self.mapsize - 1:
                            new_col = 0
                        if self.map[new_row][new_col] == "w":
                            self.map[row][col] = "w"  # water next to water tiles
                            tiles -= 1
                            break  # break out of the direction for loop to not place overlapping tiles
            if attempts > 1000000:
                break
            attempts += 1
        print("Water created!")

    def set_ocean_tiles(self):
        print("Creating oceans...")
        self.load_screen_text = "Creating oceans..."
        shore_water_distance = int(self.mapsize/10)
        direction_list = []
        for i in range(-shore_water_distance, shore_water_distance):
            for k in range(-shore_water_distance, shore_water_distance):
                direction_list.append([i, k])  # the distance to shore check list dependant on mapsize
        # check each square if water and close to land
        for row in range(0, 9 * self.mapsize):
            for col in range(0, 16 * self.mapsize):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                if self.map[row][col] == "w":  # water tile found
                    close_land = False
                    land_tiles = 0
                    for direction in direction_list:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if new_row < 0:
                            new_row = 0
                        elif new_row > 9 * self.mapsize - 1:
                            new_row = 9 * self.mapsize - 1
                        if new_col < 0:
                            new_col = 16 * self.mapsize + new_col
                        elif new_col > (16 * self.mapsize) - 1:
                            new_col = new_col % 16
                        if self.map[new_row][new_col] != "w" and self.map[new_row][new_col] != "o":  # land found :(
                            land_tiles += 1
                        if land_tiles > self.mapsize//10:  # to allow islands in oceans
                            close_land = True
                            break
                        else:
                            close_land = False
                    if not close_land:  # land not found
                        # print("Ocean placed!")
                        self.map[row][col] = "o"  # set to ocean
        print("Oceans now created!")

    def place_land(self):
        print("Creating land...")
        self.load_screen_text = "Creating land..."
        # place rest of map as land and then override with other map generation functions
        for row in range(0, 9 * self.mapsize):
            for col in range(0, 16 * self.mapsize):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                # print("checking square: " + str((row, col)))
                if self.map[row][col] == "-":
                    self.map[row][col] = "g"
        print("Land now created!")

    def place_random_mountains(self, mountain_multiplier):
        # TODO: not make thick mountain ranges pls
        # place a few random sole mountains, and a few mountain ranges
        sole_mountains = int(9 * self.mapsize * 16 * self.mapsize * (mountain_multiplier/20))
        mountain_ranges = int(9 * self.mapsize * 16 * self.mapsize * (mountain_multiplier/300))
        print("Adding", sole_mountains, "mountains and", mountain_ranges, "mountain ranges...")
        self.load_screen_text = "Adding " + str(sole_mountains) + \
                                " mountains and " + str(mountain_ranges) + " mountain ranges..."
        while sole_mountains > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] == "g":  # random square is land
                self.map[row][col] = "m"
                sole_mountains -= 1
        while mountain_ranges > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            average_range = int(mountain_multiplier*8)*self.mapsize*self.mapsize
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] == "g":
                self.place_names[row][col] = self.mountain_names_list.pop()
                while self.map[row][col] == "g" or self.map[row][col] == "m" \
                        and average_range > 0:  # random square is land or mountain
                    self.map[row][col] = "m"
                    average_range -= 1
                    row += r.randint(-1, 1)
                    col += r.randint(-1, 1)
                    # inside map boundaries/wrap around world
                    if row > 9 * self.mapsize - 1:
                        row = 9 * self.mapsize - 1
                    elif row < 0:
                        row = 0
                    if col < 0:
                        col = 16 * self.mapsize - 1
                    elif col > 16 * self.mapsize - 1:
                        col = 0
                mountain_ranges -= 1
        print("Mountains added!")

    def place_random_desert_and_jungle(self, temperature):
        # biased directions:
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1),
                      (-1, 1), (-1, -1), (0, 1), (0, -1), (0, 1), (0, -1),
                      (0, 1), (0, -1), (0, 1), (0, -1), (0, 1), (0, -1), (0, 1), (0, -1)]
        print("Adding deserts...")
        self.load_screen_text = "Adding deserts..."
        nr_deserts = self.mapsize // 2
        while nr_deserts > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            max_latitude = 3 * self.mapsize
            col = r.randint(0, 16 * self.mapsize - 1)
            row = r.randint(max_latitude, 9 * self.mapsize - 1 - max_latitude)
            latidtude_bias = 9*self.mapsize//3 if row < (9*self.mapsize)//2 else (9*self.mapsize//3)*2
            if self.map[row][col] == "g":
                chance_to_place = r.randint(0, (abs(row - latidtude_bias)+1)*100)
                if chance_to_place == 0:
                    self.map[row][col] = "d"
                    nr_deserts -= 1
                    # print("Desert center placed")
        for i in range(0, 2*self.mapsize):
            attempts = 0
            average_tiles_per_desert = int(temperature*10) * self.mapsize // 2
            while average_tiles_per_desert > 0:
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                # place on land tiles
                attempts += 1
                row = r.randint(0, (9 * self.mapsize) - 1)
                col = r.randint(0, (16 * self.mapsize) - 1)
                if self.map[row][col] == "g":  # land found!
                    biased_direction = directions[r.randint(0, len(directions) - 1)]
                    new_row = row + biased_direction[0]
                    new_col = col + biased_direction[1]
                    if new_row > 9 * self.mapsize - 1:
                        new_row = 9 * self.mapsize - 1
                    elif new_row < 0:
                        new_row = 0
                    if new_col < 0:
                        new_col = 16 * self.mapsize - 1
                    elif new_col > 16 * self.mapsize - 1:
                        new_col = 0
                    if self.map[new_row][new_col] == "d":  # adjacent desert found!
                        self.map[row][col] = "d"
                        average_tiles_per_desert -= 1
                # if attempts % 10000 == 0:
                    # print("Attempt limit", attempts/1000, "% reached!")
                if attempts > 100000:
                    # print("Desert failed")
                    break
        print("Desert generation complete!")
        print("Adding jungle...")
        self.load_screen_text = "Adding jungle..."
        nr_jungle = self.mapsize // 2
        while nr_jungle > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            max_latitude = 3 * self.mapsize
            col = r.randint(0, 16 * self.mapsize - 1)
            row = r.randint(max_latitude, 9 * self.mapsize - 1 - max_latitude)
            latidtude_bias = 9 * self.mapsize // 2
            if self.map[row][col] == "g":
                chance_to_place = r.randint(0, (abs(row - latidtude_bias) + 1)*100)
                if chance_to_place == 0:
                    self.map[row][col] = "j"
                    nr_jungle -= 1
                    # print("Jungle center placed")
        for i in range(0, 2 * self.mapsize):
            attempts = 0
            average_tiles_per_jungle = int(temperature*10) * self.mapsize
            while average_tiles_per_jungle > 0:
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                # place on land tiles
                attempts += 1
                row = r.randint(0, 9 * self.mapsize - 1)
                col = r.randint(0, 16 * self.mapsize - 1)
                if self.map[row][col] == "g":  # land found!
                    biased_direction = directions[r.randint(0, len(directions) - 1)]
                    new_row = row + biased_direction[0]
                    new_col = col + biased_direction[1]
                    if new_row > 9 * self.mapsize - 1:
                        new_row = 9 * self.mapsize - 1
                    elif new_row < 0:
                        new_row = 0
                    if new_col < 0:
                        new_col = 16 * self.mapsize - 1
                    elif new_col > 16 * self.mapsize - 1:
                        new_col = 0
                    if self.map[new_row][new_col] == "j":  # adjacent jungle found!
                        self.map[row][col] = "j"
                        average_tiles_per_jungle -= 1
                if attempts > 100000:
                    break
        print("Jungle generation complete!")

    def place_random_snow(self, temperature):
        print("Adding snow on poles")
        self.load_screen_text = "Adding snow on poles"
        # make first and last row land snow and some random tiles on second and third rows
        snow_probability = temperature
        for row in range(0, 9 * self.mapsize):
            for col in range(0, 16 * self.mapsize):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                if self.map[row][col] == "g":
                    snow = r.randint(0, 100)
                    if row >= (9 * self.mapsize - 1) // 2:  # lower hemisphere
                        if abs(row - ((9 * self.mapsize) - 1)) * 200 * snow_probability < snow * self.mapsize:
                            self.map[row][col] = "s"
                    else:  # upper hemisphere
                        if row * 200 * snow_probability < snow * self.mapsize:  # a weird algorithm that works?
                            self.map[row][col] = "s"
        print("Snow now placed!")

    def map_cleanup(self, harshness):
        print("Cleaning up...")
        self.load_screen_text = "Cleaning up map..."
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        number = 0
        # not checking edges i guess for simpler code
        for row in range(1, 9 * self.mapsize - 1):
            for col in range(1, 16 * self.mapsize - 1):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                tile_type = self.map[row][col]
                if tile_type != "m":  # not checking mountains
                    same_type_found = 0
                    for direction in directions:
                        if tile_type == self.map[row + direction[0]][col + direction[1]]:  # same type found!
                            same_type_found += 1
                    if same_type_found < harshness:
                        random_direction = directions[r.randint(0, 7)]  # select a random direction to copy square
                        self.map[row][col] = self.map[row + random_direction[0]][col + random_direction[1]]
                        number += 1
        print("Cleaned up", number, "squares!")

    def set_hills(self, mountain_multiplier):
        print("Generating hills...")
        self.load_screen_text = "Generating hills..."
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        # place hills next to mountains:
        for row in range(1, 9 * self.mapsize - 1):
            for col in range(1, 16 * self.mapsize - 1):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                adjacent_mountain = False
                r.shuffle(directions)
                for d in range(6):
                    if self.map[row + directions[d][0]][col + directions[d][1]] == "m":  # mountain is adjacent
                        adjacent_mountain = True
                        # print("Adjacent mountain found!")
                        break
                if adjacent_mountain and self.map[row][col] != "m":
                    if self.map[row][col] == "g":  # if grassland
                        self.map[row][col] = "h"  # then hills
                    elif self.map[row][col] == "s":  # if snow
                        self.map[row][col] = "a"  # then hills
                    elif self.map[row][col] == "j":  # if jungle
                        self.map[row][col] = "k"  # then hilly jungle
        # place a few random hills on grassland
        random_hills = int((9 * self.mapsize * 16 * self.mapsize) * (self.mapsize/5) * mountain_multiplier//5)
        print("Amount of random hills:", random_hills)
        attempts = 0
        while random_hills > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] == "g":  # if grassland
                self.map[row][col] = "h"
                random_hills -= 1
            else:
                attempts += 1
            if attempts > 10000:
                break
        print("Hills generated!")

    def set_forest(self, temperature, water_multiplier):
        print("Adding trees...")
        self.load_screen_text = "Adding trees..."
        # first place random sources of trees depending on mapsize and expand from there, similar to water generation
        source_trees = int(self.mapsize * 10 * temperature)
        while source_trees > 0:
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] != "w" and self.map[row][col] != "o" and self.map[row][col] != "m":  # valid land tile
                if self.map[row][col] == "g":  # grassland
                    self.map[row][col] = "f"  # forested grassland
                    source_trees -= 1
                elif self.map[row][col] == "h":  # hills
                    self.map[row][col] = "i"  # forested hills
                    source_trees -= 1
                elif self.map[row][col] == "s":  # snow
                    self.map[row][col] = "t"  # taiga
                    source_trees -= 1
                elif self.map[row][col] == "a":  # snowy hills
                    self.map[row][col] = "y"  # forested snowy hills
                    source_trees -= 1
        map_tiles = (9 * self.mapsize) * (16 * self.mapsize)
        water_tiles = int(map_tiles * water_multiplier)
        land_tiles = map_tiles - water_tiles
        tree_tiles = land_tiles * temperature * water_multiplier * 2
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        attempts = 0
        while tree_tiles > 0:
            attempts += 1
            r.shuffle(directions)
            col = r.randint(0, 16 * self.mapsize - 1)
            row = r.randint(0, 9 * self.mapsize - 1)
            if self.map[row][col] != "w" and self.map[row][col] != "o" and self.map[row][col] != "m":  # valid squares
                for direction in directions:
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    # loop over map boundaries
                    if 0 < new_row < 9 * self.mapsize - 1:  # inside longitude boundaries
                        if new_col < 0:
                            new_col = 16 * self.mapsize - 1
                        elif new_col > 16 * self.mapsize - 1:
                            new_col = 0
                        # forested = f, t, y, i
                        if self.map[new_row][new_col] == "f" or self.map[new_row][new_col] == "t" or \
                                self.map[new_row][new_col] == "y" or self.map[new_row][new_col] == "i":
                            if self.map[row][col] == "g":  # tile is grassland
                                self.map[row][col] = "f"  # set tile to forest
                                tree_tiles -= 1
                                break  # break out of the direction for loop to not place overlapping tiles
                            elif self.map[row][col] == "s":  # tile is snow
                                self.map[row][col] = "t"  # set tile to taiga
                                tree_tiles -= 1
                                break  # break out of the direction for loop to not place overlapping tiles
                            elif self.map[row][col] == "h":  # tile is hills
                                self.map[row][col] = "i"  # set tile to forested hills
                                tree_tiles -= 1
                                break  # break out of the direction for loop to not place overlapping tiles
                            elif self.map[row][col] == "a":  # tile is snowy hill
                                self.map[row][col] = "y"  # set tile to forested snowy hill
                                tree_tiles -= 1
                                break  # break out of the direction for loop to not place overlapping tiles
            if attempts > 100000:
                break
        print("Trees added!")

    def set_rivers(self):
        print("Setting rivers...")
        self.load_screen_text = "Adding rivers..."
        # Selects a random mountain tile and follows lowlands
        hill_types = {"h", "m", "y", "i", "a", "k"}
        lowland_types = {"g", "s", "d", "j", "f", "t"}
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        temp = []
        nr_rivers = self.mapsize * 4
        while nr_rivers > 0:
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            tile = self.map[row][col]
            if tile in hill_types:  # water source from mountain or hill
                river = True

                length = 0
                while river:
                    # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                    for d in directions:
                        temp.append(d)
                    new_source = False
                    check_directions = []
                    for i in range(5):  # add random directions to check for valid square
                        x = r.randint(0, len(temp) - 1)
                        check_direction = temp.pop(x)
                        check_directions.append(check_direction)
                    for direction in check_directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if new_row > 9 * self.mapsize - 1:
                            new_row = 9 * self.mapsize - 1
                        elif new_row < 0:
                            new_row = 0
                        if new_col < 0:
                            new_col = 16 * self.mapsize - 1
                        elif new_col > 16 * self.mapsize - 1:
                            new_col = 0
                        new_tile = self.map[new_row][new_col]
                        if new_tile in lowland_types:
                            self.map[new_row][new_col] = "w"
                            row = new_row  # set the new source point
                            col = new_col
                            new_source = True
                            length += 1
                            break  # break the for loop
                    if not new_source or length == 0:
                        nr_rivers -= 1
                        # self.place_names[row][col] = self.river_names.pop()
                        # print("River complete with length", length)
                        river = False

    def island_generation(self, island_multiplier):
        self.load_screen_text = "Adding islands..."
        # generates small islands in oceans
        nr_islands = int(self.mapsize * (island_multiplier * 10))
        print("Adding", nr_islands, "islands")
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for i in range(0, nr_islands):
            attempts = 0
            row = r.randint(0, 9 * self.mapsize - 1)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] == "o":
                self.place_names[row][col] = self.island_names_list.pop()
                # print("Generating island...")
                average_tiles_per_island = r.randint(self.mapsize, self.mapsize * 2 * self.mapsize)
                # nr_tiles = average_tiles_per_island
                while average_tiles_per_island > 0:
                    attempts += 1
                    # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                    peninsula = True
                    r.shuffle(directions)  # shuffle the directions
                    for k in range(0, 4):
                        attempts += 1
                        new_row = row + directions[k][0]
                        new_col = col + directions[k][1]
                        # setting new pos inside map and looping around:
                        if new_row > 9 * self.mapsize - 1:
                            new_row = 9 * self.mapsize - 1
                        elif new_row < 0:
                            new_row = 0
                        if new_col < 0:
                            new_col = 16 * self.mapsize - 1
                        elif new_col > 16 * self.mapsize - 1:
                            new_col = 0
                        if self.map[new_row][new_col] != "g":  # adjacent water, other land types not generated yet
                            self.map[row][col] = "g"  # set the origin tile to land
                            row = new_row
                            col = new_col  # set the new origin point
                            average_tiles_per_island -= 1
                            peninsula = False
                            break  # out of the for loop
                    if peninsula or attempts > 10000:
                        # print("Generated a peninsula with length", nr_tiles - average_tiles_per_island)
                        # attempts = 0
                        break  # out of the while loop
                    # if average_tiles_per_island == 0:
                        # print("Generated a full sized island!")
            # else:  # water tile not found
                # print("Island generation failed :(")
        print("Island generation complete!")

    """
    Place names
    """

    def generate_place_names(self):
        self.generate_ocean_names()
        self.generate_island_names()
        self.generate_continent_names()
        self.generate_mountain_names()

    def generate_ocean_names(self):
        names = ["Specefic", "Wellingtham", "Garbriand", "irririor", "Gretvons", "Itumeuse", "Easttois", "Wareway",
                 "Traypawa", "Hampgue", "Rugronto", "Havercouche", "Kiniling", "Hilly", "Gilgeo", "Limingmar", "Birson",
                 "Readriden", "Tamgough", "Berthiertara", "Midason", "Ingerland", "Duparnear", "Smithgar", "Glasbiens",
                 "Passons", "Kirkpawa", "Troliers", "Corville", "Causater", "Glengough", "Gorock", "Salismond",
                 "Latchacouche", "Huntinggrave", "Waterset", "Rutpawa", "Gallancour", "Menter", "Herechill",
                 "Crossding", "Lavalview", "Birwall", "Twilcarres", "Delishill", "Pilriden", "Milrich", "Flemheller",
                 "Wakaterel", "Petroboro", "Marlman", "Cochton", "Blackbrook", "Brolan", "Somerdes", "Islingsano",
                 "Chiboutry", "Cresmore", "Dedford", "Killingnet", "Langhazy", "Clerlisle", "Rostone", "Mayguay",
                 "Innisbel", "Bainfail", "Moojour", "Northtry", "Lintois", "Humwe"]
        prefix = ["The Deep of ", "The Waters of ", "The Depths of ", "The Sea of ", "The Bay of ",
                  "The Tides of ", "The Waves of ", "The Ocean of ", "The Abyss of ", "The Expanse of ", "The Gulf of "]
        suffix = [" Sea", " Ocean", " Bay", " Gulf"]
        r.shuffle(names)
        for name in names:
            i = r.randint(0, 2)
            if i == 0:  # prefix
                ocean_name = prefix[r.randint(0, len(prefix) - 1)] + name + " o"
            else:
                ocean_name = "The "+name+suffix[r.randint(0, len(suffix) - 1)] + " o"
            self.ocean_names_list.append(ocean_name)

    def generate_island_names(self):
        names = ["Islingheim", "Leides", "Grotown", "Tecumrial", "Huntcam", "Dunsomin", "Roheim", "Prespool",
                 "Virthon", "Shipgough", "Wrentmer", "Lavalcord", "Trengar", "Stonemore", "Stelswell", "Wabel",
                 "Presnan", "Irritane", "Kipview", "Colecoln", "Haverrane", "Emerbrook", "Chamling", "Allerry",
                 "Stamree", "Kirgonie", "Irobour", "Elmbour", "Trebridge", "Wrentminster", "Falney", "Milpawa",
                 "Kapusswell", "Kearcouche", "Coalsoll", "Norcona", "Ashmont", "Pasver", "Leidurn", "Kearchouche",
                 "Pilfait", "Durvons", "Kerrowich", "Wasanola", "Moocoln", "Durry", "Caleval", "Limingna", "Smiwell",
                 "Whiteterel", "Cumbersea", "Appelhazy", "Smithforte", "Dolbour", "Rossnoque", "Mildover", "Anwaki",
                 "Robsend", "Maglem", "Pencam", "Pasver", "Chelbel", "Niastead", "Coililet", "Menspond", "Verfolk"]
        r.shuffle(names)
        suffix = [" Island", " Islet", " Holm", " Islands", " Reef", " Archipelago", " Isles", " Atoll", " Isle"]
        for name in names:
            island_name = name + suffix[r.randint(0, len(suffix) - 1)] + " i"
            self.island_names_list.append(island_name)

    def generate_continent_names(self):
        names = ["Iolagux", "Ibaegen", "Datriubrush", "Niutretand", "Eafifax", "Ocaucira", "Bluafoyix", "Ofoces",
                 "Fikromath", "Qudriugreron", "Kleadoqoa", "Wriuhorera", "Uabivoth", "Braubiles", "Fliuzutul",
                 "Mecutora", "Laicrapros", "Kleasaqis", "Euzoqin", "Kruagivor", "Iazumari", "Isaexoris", "Duaslelora",
                 "Qeibucrane", "Iofekane", "Iquaduth", "Eututela", "Qiuyudios", "Iokilune", "Aihatun", "Gufiugix"]
        r.shuffle(names)
        for name in names:
            self.continent_names_list.append(name + " c")

    def generate_mountain_names(self):
        names = ["Outguay", "Torringman", "Mencord", "Norrose", "Chanbour", "Cammer", "Bredencana", "Sagry", "Nanterel",
                 "Kinimore", "Hfforte", "Gansano", "Wareling", "Darwaki", "Beavermond", "Shawtawa", "Gilwood", "Mahoton",
                 "Clarensevain", "Wilchill", "Ponojour", "Chesterbo", "Rosegan", "Churchbiens", "Colicouche", "Outnet",
                 "Scartague", "Thesisle", "Estertawa", "Brookduff", "Ellismar", "Sagtry", "Stoketonas", "Carasend",
                 "Wasato", "Glaspids", "Vegreris", "Hasrose", "Buxlow", "Efiingburn", "Hasttham", "Labo", "Boothbron",
                 "Niadosa", "Weyhurst", "Plaintown", "Bloomriden", "Matasay", "Milforte", "Hudsend", "Dignia", "Basly"]
        suffix = [" Tips", " Highland", " Highlands", " Slopes", " Heights", " Summit", " Peaks", "Mountains",
                  " Mountain", " Peak", " Tops"]
        r.shuffle(names)
        for name in names:
            mountain_name = name + suffix[r.randint(0, len(suffix) - 1)] + " m"
            self.mountain_names_list.append(mountain_name)

    """
    Civilization generation
    """

    def generate_civs(self):
        self.set_civ_map()
        self.set_civ_names()
        self.generate_civ_capitals()
        self.load_screen = False

    def set_civ_map(self):
        self.load_screen_text = "Generating civilization map..."
        for row in range(0, 9 * self.mapsize):
            c = []
            for col in range(0, 16 * self.mapsize):
                # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
                c.append("-")
            self.civilization_map.append(c)

    def set_civ_names(self):
        # TODO: add more civ names
        self.load_screen_text = "Generating civilization names..."
        print("Generating civilizations...")
        names = ["Qohuol", "Duilueg", "Pegith", "Shimzoq", "Thiedroh", "Vranpih", "Oqtond", "Zudqien", "Biusnaira",
                 "Webunea", "Swephiqi", "Xerleke", "Whophreku", "Swuapsesa", "Sleunusi", "Snarwaqo", "Sirdemi",
                 "Flueffellua", "Krulguaria", "Wromatu", "Scazegi", "Vlosriko", "Jucriqee", "Washilou", "Shaiheose",
                 "Vulwogu", "Xuczeqe", "Oggora", "Voaphlata", "Muithmiqee", "Gnoinlote", "Blonfota", "Ipzoku",
                 "Vikhusi", "Grunculli", "Dirhauqo", "Sechaneo", "Shatnaso", "Erweta", "Kaprella", "Sprastrego",
                 "Hastoge", "Auhhorua", "Gnakzeakiu", "Chinrondia", "Prusphethaa", "Reehnunuo", "Paumbauxo",
                 "Sincousha", "Tromthoto", "Wenthosu", "Doudguli", "Pronzoonda", "Iesseelee", "Smuackumu", "Sleontugi",
                 "Uelhucuu", "DaTe", "Heenshooshie", "Dustruhi", "Wresmotu", "Gnokliuhu", "Chekate", "Uctatho",
                 "Krulguaria", "Tropothe", "Genithrogi", "Ciwille", "Snezutu", "Threrthemo", "Vrankusua", "Stoklushi",
                 "Clusduha", "Zostugi", "Thresbesha", "Quahmeha", "Guikshusaa", "Chithnoga", "Ulm", "Vlinitilli",
                 "Strakdeme", "Vlogomeo", "Crirphomeu", "Oikthukae", "Scustralo", "Smoulrande", "Anqetu", "Truphilinoa",
                 "Imtoelu", "Fluruuthea", "Klenshueca", "Susthulu", "Hepqige", "Sprulpheru", "Doudguli", "Glaemtheke",
                 "Zatnandu", "Stipsuma", "Fluruuthea", "Hatlose", "Wheumhielli", "Iklaarue", "Inqice", "Iflueka",
                 "Blephuoloo", "Vlupzoucu", "Wuurpaxia", "Kalnindo", "Cetchara", "Brahgoxeu", "Thrikleaso", "Fopruca",
                 "Vlumbondia", "Phron", "Heogia", "Xyphria", "Traspo", "Oukhia", "Iaphia", "Aentia", "Zia", "Ilospia",
                 "Gyria", "Rhephia", "Aso Benaire", "Voof", "Striaa Saintbu", "Pamo", "Bulke", "Para Nare",
                 "Lyngo Veanion", "Laandla", "Antarc", "Puasaand", "Tunor Bajan", "Damon", "Uthe", "Ticca", "Isgeorma",
                 "Sauzil Igiea", "Pierrepines", "Toco Sotu", "Ruoftar", "Boher", "Udom", "Naquene", "Risland", "Biba",
                 "Ofblic", "Purabiatope", "Riaalra", "Mosaint", "Rogypia", "Themo", "Zamye Ui", "Vepal Staxie", "Lesia",
                 "Grod", "Tindra Edo", "Landmar", "Zastanpai", "Vichi", "Bramacao", "Purako", "Mowalesmac", "Guipalstan",
                 "Landfri", "Liania Hacro", "Hrainpa", "Ngavofi", "Candildives", "Liau Duama", "Nei", "Loupeje",
                 "Salvir", "Byaranbia", "Kicathe", "Nybelri", "Bisrida", "Babwesta Zerbripa", "Gassamor", "Domli",
                 "Riatia Isu", "Pacosland", "Apia", "Jitiofri", "Kucook", "Landa", "Bailu", "Miin", "Djitachten",
                 "Netoxem", "Biago Niabo", "Pariai", "Retic", "Saoraka", "Tomyanko", "Outwannia", "Paha Toto", "Bapa",
                 "Rkeyof Laco", "Tonasierna", "Siapu", "Quastannorbonla", "Slandsva", "Marblic", "Puvo", "Mykong",
                 "Aof Poreelli", "Guaygako", "Diauli", "Fusoras", "Jivir", "Blicge", "Velands", "Gitri", "Shallberzil",
                 "Costa Para Efavo", "Sato", "Como", "Thehege", "Abia", "Vissu Gosaumoa", "Slosu Reno", "Tugypt",
                 "Ratesda", "Bocu Kingoru", "Cosdia", "Maneardan", "Masial", "Ofnorna", "Mayotteene", "Sangatrea",
                 "Memaba", "Rinegha", "Gingia Seyui", "Densval", "Quebou", "Siaibai", "Stanmarcra", "Abuddin",
                 "Aldorria", "Aldovia", "Amestris", "Annexia", "Arulco", "Arvee", "Baracas", "Barama"]
        r.shuffle(names)
        print("Possible civilizations:", len(names))
        # Biased towards republics, kingdoms and empires
        suffix_list = [" Republic", " Kingdom", " Empire", " Federation", " Union", " Island", " Islands", " Lands",
                       " Principality", " Sultanate", " Confederation", " Republic", " Kingdom", " Republic", " Kingdom",
                       " Republic", " Kingdom", " Republic", " Kingdom", " Republic", " Kingdom", " Empire", " Empire",
                       " Empire", " Empire", " Empire", " Empire", " Territory"]
        prefix_list = ["the Republic of ", "South ", "North ", "East ", "West ", "United ", "Isle of ",
                       "Southern ", "Northern ", "Eastern ", "Western ", "Principality of ", "the Commonwealth of ",
                       "Union of ", "the State of ", "the Sultanate of ", "the Federation of ", "United Kingdom of ",
                       "Empire of ", "the Republic of ", "United Kingdom of ", "Empire of ", "the Republic of ",
                       "United Kingdom of ", "Empire of ", "the Republic of ", "United Kingdom of ", "Empire of ",
                       "the Republic of ", "Kingdom of ", "Kingdom of ", "Kingdom of ", "Kingdom of ", "Kingdom of ",
                       "Kingdom of ", "Kingdom of ", "Kingdom of "]
        for name in names:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            if r.randint(0, 2) == 0:  # Add government 1/3 (changeable) of time
                r.shuffle(suffix_list)
                government = suffix_list[0]
                the = "the " if r.randint(0, 1) == 1 else ""  # random amount of "the's"
                full_name = the + name + government
            elif r.randint(0, 2) == 0:  # add prefix 1/3 (changeable) of time
                r.shuffle(prefix_list)
                prefix = prefix_list[0]
                full_name = prefix + name
            else:
                full_name = name
            self.civ_name_list.append(full_name)
        # print(len(self.civ_name_list))
        # print(self.civ_name)

    def get_number_of_civs(self):
        return len(self.civ_name_list) - 1

    def generate_civ_capitals(self):
        self.load_screen_text = "Placing capitals..."
        if self.mapsize * 10 < 100:
            number_of_civs = self.mapsize * 10 - r.randint(0, self.mapsize)
        else:
            number_of_civs = 100  # max 200 civs
        print("Placing", number_of_civs, "civilizations!")
        directions = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1], [0, 0]]
        attempts = 0
        civs_placed = 0
        first = True
        placed = False
        center_bias = 1
        while number_of_civs > 0:
            # Game.display_loading(screen, self.load_screen_text, self.load_screen_bar)
            row = r.randint(center_bias * self.mapsize, 9 * self.mapsize - 1 - center_bias*self.mapsize)
            col = r.randint(0, 16 * self.mapsize - 1)
            if self.map[row][col] != "w" and self.map[row][col] != "o" and self.map[row][col] != "m":  # legal square
                if first:
                    first = False
                    placed = True
                    # print("First civilization placed!")
                else:
                    for cap_pos in self.civ_capital_pos:
                        attempts += 1
                        distance_to_other_caps = abs(cap_pos[0] - row) + abs(cap_pos[1] - col)  # euclidean distance
                        if distance_to_other_caps <= 4:  # successful placement
                            placed = False
                            break  # break out of the innermost for loop
                        placed = True
                if placed:
                    civ = self.civ_name_list.pop()
                    area = []  # create a new list id
                    for direction in directions:
                        new_row = row + direction[0]
                        new_col = col + direction[1]
                        if new_row > 9 * self.mapsize - 1:
                            new_row = 9 * self.mapsize - 1
                        elif new_row < 0:
                            new_row = 0
                        if new_col < 0:
                            new_col = 16 * self.mapsize + new_col
                        elif new_col > 16 * self.mapsize - 1:
                            new_col = new_col % 16
                        self.civilization_map[new_row][new_col] = civ
                        area.append([new_row, new_col])
                    self.civ_name.append(civ)
                    self.civ_capital_pos.append([row, col])
                    self.protected_cities.append([[row, col], r.randint(0, 18000)])  # adds a random truce timer to civ
                    self.civ_color_index.append(row*10000+col)
                    self.civ_area_list.append(area)
                    self.civ_cities.append([[row, col]])
                    self.civ_army_power.append(1)
                    self.civ_tech.append(1)
                    self.civ_population.append(1)
                    self.civ_food.append(1)
                    self.civ_production.append(1)
                    number_of_civs -= 1
                    civs_placed += 1
                    # print("Civilization", civ, "placed!")
            if attempts > 100000:
                break
            attempts += 1
            placed = False  # reset the thing
            # print("Checked", attempts, "squares...")
        print("Civilization generation complete! Placed", civs_placed, "civilizations!")
        self.world_event_log.append(str(civs_placed) + "Number of civilizations generated!")


    def get_civ(self, index):
        return self.civ_name[index]

    def get_capital_pos(self, civ_index):
        return self.civ_capital_pos[civ_index]

    def get_civname_from_capital_pos(self, row, col):
        pos = [row, col]
        for i in range(0, len(self.civ_capital_pos)):
            if self.civ_capital_pos[i] == pos:
                return self.civ_name[i]
        return "No capital found"

    def get_civname_from_pos(self, row, col):
        name = self.civilization_map[row][col]
        if name != "-":
            # print(name)
            return name
        # print(name)
        return "-"

    def get_civ_area_dir(self, civ_index):
        return self.civ_area_list[civ_index]

    def get_civ_index_from_name(self, name):
        for civ in range(0, len(self.civ_name)):
            if name == self.civ_name[civ]:
                return civ

    def add_civ_tile(self, civ_index, tile):
        # update the civmap
        self.civilization_map[tile[0]][tile[1]] = self.civ_name[civ_index]
        # update the direction list for civ
        area_list = self.civ_area_list[civ_index]
        area_list.append(tile)
        self.civ_area_list[civ_index] = area_list

    """
    Civ decisions (expansion and war/politics):
    """

    def civ_decisions(self, civ, time, starting_year, sound):
        self.war_and_politics(civ, time, starting_year, sound)
        self.civ_expansion(civ, time, starting_year, sound)

    """
    Procedural civilization expansion:
    """

    def civ_expansion(self, civ, time, starting_year, sound):
        # TODO: tweak civ expansion
        self.calculate_food_and_pro_for_civ(civ, time)
        self.add_tile(civ)
        self.add_city(civ, time, starting_year, sound)
        self.delete_area_list_duplicates(civ)
        self.calculate_armypower(civ, time)
        self.calculate_tech(civ, time)
        self.calculate_population(civ)

    def calculate_population(self, civ):
        # function - area, food
        food_per_pop = 12
        self.civ_population[civ] = self.civ_food[civ] // food_per_pop

    def add_tile(self, civ):
        # dependent on population, tech, amount of cities and civ area
        # max 4 (*mapsize?) tiles from city center
        city_centers = self.civ_cities[civ]
        nr_of_cities = len(city_centers)
        civ_areas = self.civ_area_list[civ]
        civ_total_area = len(civ_areas)
        tweaker = 9
        chance_to_add_tile = (civ_total_area*tweaker)/(1 + nr_of_cities)  # TODO: tweak this tile function
        if int(chance_to_add_tile) > 100:
            tile = 100
        else:
            tile = r.randint(int(chance_to_add_tile), 100)
        if tile >= 99:  # success!
            # print("Success!")
            if len(self.civ_area_list[civ]) < 16 * len(self.civ_cities[civ]):  # max 16 tiles per city basically
                good_tile = self.find_good_tile(civ)
                if good_tile != "-":
                    self.add_civ_tile(civ, good_tile)

    def calculate_armypower(self, civ, time):
        # pop is always 2 times larger than army
        # army is function of production
        production_per_army = 5
        self.civ_army_power[civ] = self.civ_production[civ] // production_per_army

    def calculate_tech(self, civ, time):
        # TODO: tweak tech function
        # Tech could simply be a function of pop, time and area (larger empire = less tech = historically accurate)
        area = len(self.civ_area_list[civ])
        time_nerf = 1 + time//36000
        pop = self.civ_population[civ]
        area_tweak = 10  # tweak this
        self.civ_tech[civ] = (pop / 2) - (area / area_tweak) - time_nerf

    def add_city(self, civ, time, starting_year, sound):
        # dependant on production and food and civilization population
        # TODO: tweak city chance
        pop_per_city = 4
        tweaker = 50
        if self.civ_population[civ] > pop_per_city * len(self.civ_cities[civ]):  # civ has pop
            lower = self.civ_production[civ]
            chance = r.randint(int(lower), 10000 * len(self.civ_cities[civ]) * 2)
            if chance >= (10000 - tweaker) * len(self.civ_cities[civ]):  # place a city
                # print("Placing new city...")
                possible_locations = []
                max_distance = 6 + self.mapsize//10
                min_distance = 5
                for city in self.civ_cities[civ]:
                    for i in range(-max_distance, max_distance):
                        for k in range(-max_distance, max_distance):
                            row = city[0] + i
                            col = city[1] + k
                            if 0 < row < 9 * self.mapsize - 1:  # inside map
                                possible_locations.append([row, col])
                # print("Length of city locations with duplicates:", len(possible_locations))
                # next, delete if location is duplicated
                location = len(possible_locations) - 1
                while location >= 2:
                    # go through the list backwards,
                    # and scheck all elements up to that point for duplicates and delete them
                    # OMG THIS IS SOOO EPIC SORTING SOLUTION WTF
                    # the list gets shorter when we pop so the same location gets checked again when we pop,
                    # which is what we want since there can be multiple duplicates
                    for duplicate in range(location - 1, - 1, - 1):
                        if possible_locations[location] == possible_locations[duplicate]:
                            possible_locations.pop(duplicate)
                            break
                    location -= 1
                # print("Lenth of city locations without duplicates", len(possible_locations))
                # next, check if location is too close to own city
                for city in self.civ_cities[civ]:
                    for location in range(len(possible_locations) - 1, -1, -1):  # go through the list backwards to pop properly
                        loc = possible_locations[location]
                        distance = abs(loc[0] - city[0]) + abs(loc[1] - city[1])
                        if distance < min_distance:
                            possible_locations.pop(location)
                            break  # out of the city for loop since the tile is invalid anyway
                # print("Length of city locations not too close to own cities:", len(possible_locations))
                r.shuffle(possible_locations)  # to randomize location placement a bit
                for location in possible_locations:
                    for civlization in self.civ_cities:
                        for city in civlization:
                            euc_distance = abs(city[0] - location[0]) + abs(city[1] - location[1])
                            if euc_distance >= max_distance - 1:  # a city is not too close, valid placement?
                                # check the east, west loop
                                if location[1] < 0:
                                    location[1] = 16 * self.mapsize + location[1]
                                elif location[1] > 16 * self.mapsize - 1:
                                    location[1] = location[1] % 16
                                # check if tile owned:
                                if self.civilization_map[location[0]][location[1]] == "-":  # unoccupied square found!
                                    if self.map[location[0]][location[1]] != "w" and \
                                            self.map[location[0]][location[1]] != "o" and \
                                            self.map[location[0]][location[1]] != "m":
                                        # valid tile found!
                                        # print("Valid city tile found!")
                                        self.civ_cities[civ].append([location[0], location[1]])  # updated city list
                                        # the new city is protected for max 10 years
                                        self.protected_cities.append([[location[0], location[1]], r.randint(0, 3600)])
                                        directions = [[0, 1], [0, -1], [1, 0], [-1, 0], [0, 0]]
                                        for direction in directions:
                                            new_row = location[0] + direction[0]
                                            new_col = location[1] + direction[1]
                                            if new_row > 9 * self.mapsize - 1:
                                                new_row = 9 * self.mapsize - 1
                                            elif new_row < 0:
                                                new_row = 0
                                            if new_col < 0:
                                                new_col = 16 * self.mapsize + new_col
                                            elif new_col > 16 * self.mapsize - 1:
                                                new_col = new_col % 16
                                            self.civilization_map[new_row][new_col] = self.civ_name[civ]  # update occupied squares
                                            self.civ_area_list[civ].append([new_row, new_col])  # Update area list for city
                                        # print("City placement complete!")
                                        date = Game.convert_time_to_date(time, starting_year)
                                        numerical = self.get_numerical(len(self.civ_cities[civ]))
                                        # update immersion stuff:
                                        if sound:
                                            Game.play_sound("city")
                                        string = " settled their "+numerical+" city"
                                        self.world_event_log.append(date + self.civ_name[civ] + string)
                                        return

    """
    Helper functions for helper functions
    """

    def calculate_food_and_pro_for_civ(self, civ, time):
        # print("Updating", self.civ_name[civ])
        food = 0
        production = 0
        tech_tweaker = 5
        food_per_pop = 3
        for location in self.civ_area_list[civ]:
            tile = self.map[location[0]][location[1]]
            food += tile_to_food[tile] + ((self.civ_tech[civ]/tech_tweaker)/(1 + 360000/time))  # add tech here?
            production += tile_to_production[tile] + ((self.civ_tech[civ]/tech_tweaker)/(1 + 360000/time))
        # TODO: maybe tweak food and production calculations
        self.civ_food[civ] = food  # update the variable for easy access in other functions
        self.civ_production[civ] = production

    def find_good_tile(self, civ):
        # finds the best tile outside civilization borders that is not occupied, and returns it
        # max range 3 from each city
        check_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # North, South, West, East
        civ_locs = self.civ_area_list[civ]
        r.shuffle(civ_locs)
        # print(civ_locs)
        city_locations = self.civ_cities[civ]
        r.shuffle(city_locations)  # shuffle to increase chance to add tile from settled city
        # print("Finding a good tile...")
        total_worth = 0
        reach = 5
        best_tile = [0, 0]
        for civ_loc in civ_locs:  # check each tile owned by the civilization
            for check_direction in check_directions:  # check each direction from that tile
                row = civ_loc[0] + check_direction[0]
                col = civ_loc[1] + check_direction[1]
                # print("Checking tile: ", [row, col])
                outside_range = True
                # check if tile is inside civ reach
                if len(city_locations) > 1:
                    for city in range(1, len(city_locations) - 1):
                        euc_distance = abs(city_locations[city][0] - row) + abs(city_locations[city][1] - col)
                        if euc_distance <= reach:
                            # print("Not outside range")
                            outside_range = False
                else:
                    euc_distance = abs(self.civ_capital_pos[civ][0] - row) + abs(self.civ_capital_pos[civ][1] - col)
                    # print("Capital pos: ", self.civ_capital_pos[civ])
                    if euc_distance <= reach:
                        outside_range = False
                # check inside map borders first and possibly loop around map
                if row < 0 or row > 9 * self.mapsize - 1:
                    break  # if over north pole or under south pole
                # loop around map
                if col >= 16 * self.mapsize:
                    col = 16 * self.mapsize - col
                elif col < 0:
                    col = 16 * self.mapsize + col
                # only check unoccupied tile:
                if self.civilization_map[row][col] == "-":
                    if not outside_range:
                        tile_type = self.map[row][col]
                        worth = tile_to_food[tile_type] + tile_to_production[tile_type]
                        if worth > total_worth:  # new best
                            total_worth = worth  # update variables
                            best_tile = [row, col]
        if total_worth != 0:
            # print("Good tile found!")
            # print("Tile found worth:", total_worth)
            return best_tile
        else:
            # print("No tile found :(")
            return "-"

    def delete_area_list_duplicates(self, civ):
        location = len(self.civ_area_list[civ]) - 1
        while location >= 2:
            for duplicate in range(0, location):
                if self.civ_area_list[civ][location] == self.civ_area_list[civ][duplicate]:
                    self.civ_area_list[civ].pop(duplicate)
                    print("Deleted area duplicate :)")
                    break
            location -= 1

    def get_numerical(self, number):
        if 10 < number < 20:
            return str(number)+"th"
        elif number % 10 == 1:
            if number > 20:
                return str(number)+"st"
            else:
                return "1st"
        elif number % 10 == 2:
            if number > 20:
                return str(number)+"nd"
            else:
                return "2nd"
        elif number % 10 == 3:
            if number > 20:
                return str(number)+"rd"
            else:
                return "3rd"
        else:
            return str(number)+"th"

    """
    Helper functions for displaying category leader:
    """

    def get_area_leader_index(self):
        area_list = []
        for civ in range(len(self.civ_name)):
            area_list.append(len(self.civ_area_list[civ]))
        max_area_index = area_list.index(max(area_list))
        return max_area_index

    def get_pop_leader_index(self):
        return self.civ_population.index(max(self.civ_population))

    def get_tech_leader_index(self):
        return self.civ_tech.index(max(self.civ_tech))

    def get_army_leader_index(self):
        return self.civ_army_power.index(max(self.civ_army_power))

    """
    War and politics decisions:
    - if another civ is too close:
      - low chance to inherit civ if armypower is strong enough
      - high chance to go to war, take city if armypower is larger than other civ, and halve the army power or something
    - chance to lose a city to revolt
      - dependant on low armypower, high tech, distance from capital and population
    - chance to add colony
      - dependant on year (-500, 1800), population, production, civ has a water tile
      - adds a city far away from capital
    """

    def war_and_politics(self, civ, time, starting_year, sound):
        self.too_close_civ_decisions(civ, time, starting_year, sound)
        self.city_revolt(civ, time, starting_year, sound)

    """
    Helper functions for war and politics
    """

    def get_too_close_civ(self, civ):
        # print("Finding close civs...")
        # TODO: fix function to not have 4 nested for loops
        min_distance = 7 + self.mapsize//10  # tweak this maybe
        own_city_locations = self.civ_cities[civ]
        for civilization in range(len(self.civ_cities)):
            if civilization != civ:  # not own civs citites
                civ_has_protected = self.get_if_civ_has_protected_city(civilization)
                if not civ_has_protected:
                    for own_city in own_city_locations:
                        for city in range(len(self.civ_cities[civilization])):
                            # TODO: fix to include map looping
                            distance = abs(own_city[0] - self.civ_cities[civilization][city][0]) + \
                                       abs(own_city[1] - self.civ_cities[civilization][city][1])  # euc distance
                            # print("Distance from", self.civ_name[civ], "to", self.civ_name[civilization], "=", distance)
                            if distance < min_distance:
                                # print("Found a city too close!")
                                return civilization, True
        return civ, False
        # return other_civ, True

    def too_close_civ_decisions(self, civ, time, starting_year, sound):
        other_civ, close = self.get_too_close_civ(civ)
        if close:
            # print("A civ is too close!")
            inherit = self.get_inherit_civ(civ, other_civ, time, starting_year, sound)
            if inherit:
                # print("Inheritance happening")
                # Turn over each tile and city to own civ
                for location in self.civ_area_list[other_civ]:
                    self.civ_area_list[civ].append(location)
                    self.civilization_map[location[0]][location[1]] = self.civ_name[civ]
                for city in self.civ_cities[other_civ]:
                    self.civ_cities[civ].append(city)
                    self.protected_cities.append([city, r.randint(0, 3600)])  # adds a max 10 year truce period
                name = self.pop_civ_from_all(other_civ)
                self.civ_name_list.append(name)
                # returns the inherited civs name back to the name list so it can be used by a revolting city
            else:
                winner, loser, war = self.get_war(civ, other_civ, time, starting_year, sound)
                if war:  # return the last city placed by the losing civ
                    # print("War is happening")
                    city = self.civ_cities[loser].pop()  #
                    self.civ_cities[winner].append(city)  # take the last city cettled
                    self.protected_cities.append([city, r.randint(0, 3600)])  # adds a max 10 year truce for city/civ
                    tiles = self.get_adjacent_tiles_to_city(city)  # get area tiles close to that city
                    for tile in tiles:
                        self.civ_area_list[winner].append(tile)
                        self.civilization_map[tile[0]][tile[1]] = self.civ_name[winner]

    def pop_civ_from_all(self, civ):
        name = self.civ_name.pop(civ)
        self.civ_capital_pos.pop(civ)
        self.civ_color_index.pop(civ)
        self.civ_area_list.pop(civ)
        self.civ_cities.pop(civ)
        self.civ_army_power.pop(civ)
        self.civ_tech.pop(civ)
        self.civ_population.pop(civ)
        self.civ_food.pop(civ)
        self.civ_production.pop(civ)
        return name

    def get_inherit_civ(self, own_civ, other_civ, time, starting_year, sound):
        # returns an True if army power is over 3x the other civ, maybe change to a chance based system?
        ratio = 3
        if self.civ_army_power[own_civ] > self.civ_army_power[other_civ] * ratio:
            if sound:
                Game.play_sound("inherit")
            date = Game.convert_time_to_date(time, starting_year)
            self.world_event_log.append(date + "- {0} inherited {1}".format(self.civ_name[own_civ], self.civ_name[other_civ]))
            return True
        return False

    def get_war(self, own_civ, other_civ, time, starting_year, sound):
        if self.civ_army_power[own_civ] * 0.66 > self.civ_army_power[other_civ] * 0.75:
            if len(self.civ_cities[other_civ]) > 1:  # losing civ has another city
                date = Game.convert_time_to_date(time, starting_year)
                if sound:
                    Game.play_sound("war")
                self.world_event_log.append(date + "- {0} took a city from {1}".format(self.civ_name[own_civ], self.civ_name[other_civ]))
                return own_civ, other_civ, True
        return own_civ, other_civ, False

    def get_adjacent_tiles_to_city(self, city):
        # returns a list of tiles adjacent to the city
        directions = [(0, 1), (1, 0), (-1, 0), (0, -1), (0, 0)]
        tiles = []
        for direction in directions:
            new_row = city[0] + direction[0]
            new_col = city[1] + direction[1]
            if new_row > 9 * self.mapsize - 1:
                continue  # jump over this tile, since its outside the map
            elif new_row < 0:
                continue
            if new_col < 0:
                new_col = 16 * self.mapsize - 1
            elif new_col > 16 * self.mapsize - 1:
                new_col = 0
            tiles.append([new_row, new_col])
        return tiles

    def city_revolt(self, civ, time, starting_year, sound):
        # the main city revolt function
        nr_of_cities = len(self.civ_cities[civ])
        if nr_of_cities > 1:
            revolt_city = self.get_revolt_city(civ)
            if revolt_city != "-":
                tweaker = 2000
                if nr_of_cities > self.civ_tech[civ] * 10:
                    chance = nr_of_cities  # always revolt if empire is too large for its tech
                else:
                    chance = r.randint(nr_of_cities, int(tweaker/nr_of_cities) + int(self.civ_tech[civ] * 100))  # smaller range the more cities a civ has
                if chance == nr_of_cities:  # a city revolts
                    self.new_civ_from_revolted_city(revolt_city, civ, time, starting_year, sound)

    def get_revolt_city(self, civ):
        possible_revolt_cities = []
        # not counting the capital, since a capital revolting would break the game
        for city in range(1, len(self.civ_cities[civ])):
            protected = False
            for protected_city in self.protected_cities:
                if city == protected_city[0]:
                    # this city is protected
                    protected = True
            if not protected:
                possible_revolt_cities.append(self.civ_cities[civ][city])
        if len(possible_revolt_cities) > 0:
            return possible_revolt_cities[r.randint(0, len(possible_revolt_cities) - 1)]  # returns a random city
        return "-"

    def new_civ_from_revolted_city(self, city, parent, time, starting_year, sound):
        directions = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1], [0, 0]]
        area = []
        civ_name = self.civ_name_list.pop(0)  # gets the oldest not used name
        self.civ_name.append(civ_name)
        for direction in directions:
            new_row = city[0] + direction[0]
            new_col = city[1] + direction[1]
            if new_row > 9 * self.mapsize - 1:
                new_row = 9 * self.mapsize - 1
            elif new_row < 0:
                new_row = 0
            if new_col < 0:
                new_col = 16 * self.mapsize + new_col
            elif new_col > 16 * self.mapsize - 1:
                new_col = new_col % 16
            # pop the city's adjacent area from parent civ
            if [new_row, new_col] in self.civ_area_list[parent]:
                index = self.civ_area_list[parent].index([new_row, new_col])
                tile = self.civ_area_list[parent].pop(index)
                self.civilization_map[tile[0]][tile[1]] = civ_name
                area.append(tile)
        # update the civ variables
        self.civ_capital_pos.append(city)
        self.protected_cities.append([city, 3600])  # adds a 10 year truce timer to the new civ
        self.civ_color_index.append(city[0] * 10000 + city[1])
        self.civ_area_list.append(area)
        self.civ_cities.append([city])
        self.civ_army_power.append(1)
        self.civ_tech.append(1)
        self.civ_population.append(1)
        self.civ_food.append(1)
        self.civ_production.append(1)
        # pop the city from parent civ
        index = self.civ_cities[parent].index(city)
        self.civ_cities[parent].pop(index)
        # update world event log:
        if sound:
            Game.play_sound("rebellion")
        date = Game.convert_time_to_date(time, starting_year)
        self.world_event_log.append(date + "- {0} revolted from {1}".format(civ_name, self.civ_name[parent]))

    def get_if_civ_has_protected_city(self, civ):
        for protected in self.protected_cities:
            for city in self.civ_cities[civ]:
                if protected[0] == city:
                    return True
        return False

    def reduce_truce_timer(self, time):
        # print(self.protected_cities)
        for city in range(len(self.protected_cities) - 1, -1, -1):  # go through the list backwards to be able to pop
            self.protected_cities[city][1] -= time
            if self.protected_cities[city][1] < 0:
                popped = self.protected_cities.pop(city)
                # print("Popped city:", popped)

    def add_colony(self, civ):
        # adds a distant city basically, scales with mapsize
        # chance = self.get_colony_chance(civ)
        pass

    def get_colony_chance(self, civ):
        # returns a range 0 - 100 based on calculations
        pass

    """
    Savegame
    """

    def print_save(self, time, starting_year):
        save_list = [self.map, self.civilization_map, self.civ_area_list, self.civ_cities, self.world_event_log,
                     self.civ_name_list, self.civ_name, self.civ_capital_pos, self.protected_cities,
                     time, starting_year, self.mapsize]
        print("The savegame, copy this and paste in the terminal to continue from save:")
        print(save_list)


def continue_from_save(save):
    gameState.map = save[0]
    gameState.civilization_map = save[1]
    gameState.civ_area_list = save[2]
    gameState.civ_cities = save[3]
    gameState.world_event_log = save[4]
    print(gameState.world_event_log)
    gameState.civ_name_list = save[5]
    gameState.civ_name = save[5]
    gameState.civ_capital_pos = save[6]
    gameState.protected_cities = save[7]
    time = save[8]
    starting_year = save[9]
    gameState.mapsize = save[10]
    return time, starting_year

