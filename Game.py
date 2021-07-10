"""
The Game, responsible for:
- Main
- Displaying the game
- Animations
- Sound
"""

# TODO: dynamic weather? (Change temperature and recalculate basically all landmass)
# TODO: leader dynasties and elections for republics?
# TODO: fix date function (00.02 1345 BC)
# TODO: display place names better, more place names


import pygame as p
from MapGame import Engine
from MapGame import Menu

# assigning global variables
VERSION = "Version Alpha 0.9"
PERFORMANCE = 2  # lower number means chuggier game
SCREENSIZEMULTIPLIER = 2  # for larger screen maybe later
SCREENWIDTH = int(800 * SCREENSIZEMULTIPLIER)
SCREENHEIGHT = int(450 * SCREENSIZEMULTIPLIER)  # screen ratio 16:9
MAPSIZEMULTIPLIER = 2  # scalable map generation. Good range(1, 3)
SQ_SIZE = int(SCREENWIDTH / (16 * MAPSIZEMULTIPLIER))   # = SCREENHEIGHT / 9
MAX_FPS = 15  # for animations
IMAGES = {}  # image list for easy access to sprites
SOUNDS = {}
COLOURS = [p.Color("gold"), p.Color("gold4"), p.Color("goldenrod"), p.Color("firebrick4"),
           p.Color("darkviolet"), p.Color("darkslategray4"), p.Color("darkseagreen2"), p.Color("darksalmon"),
           p.Color("darkorange"), p.Color("darkgray"), p.Color("cyan3"), p.Color("cornsilk3"), p.Color("coral2"),
           p.Color("chocolate4"), p.Color("chartreuse2"), p.Color("cadetblue3"), p.Color("burlywood3"),
           p.Color("brown"), p.Color("blue4"), p.Color("bisque"), p.Color("azure2"), p.Color("aquamarine3"),
           p.Color("lightpink"), p.Color("mediumpurple"), p.Color("orange"), p.Color("orchid"), p.Color("red"),
           p.Color("red4"), p.Color("royalblue"), p.Color("sienna"), p.Color("yellow2"), p.Color("black"),
           p.Color("grey")]

tile_to_color = {"w": "blue", "o": "darkblue", "g": "darkolivegreen4",
                 "f": "forestgreen", "i": "olivedrab", "h": "olivedrab",
                 "s": "snow", "d": "khaki", "j": "darkgreen", "m": "gray", "t": "snow",
                 "a": "snow", "y": "snow", "k": "darkgreen", "-": "black"}
color_to_tile = {v: k for k, v in tile_to_color.items()}


def main():
    # for savegame import:
    # time, starting_year, mapsize_multiplier = Engine.continue_from_save(input("Type "))
    # gs = Engine.gameState(mapsize_multiplier)
    p.init()
    screen = p.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    p.display.set_caption("Civilization observing simulator")
    screen.fill(p.Color('gray'))
    clock = p.time.Clock()
    load_music()
    # set the initial variables
    displaytrees = False
    civ_info = False
    leader_info = False
    display_date = False
    hide_controls = False
    events = False
    running = True
    paused = False
    menu = True
    menu_state = 0
    sound = True
    music = True
    not_implemented = False
    create_button_coordinates = get_create_button_dimensions()
    load_button_coordinates = get_load_button_dimensions()
    exit_button_coordinates = get_exit_button_dimensions()
    civ_index = 0
    calculate_civ = 0
    while running:
        # to not get errors when exiting:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            if not menu:
                # key handler for game
                if e.type == p.KEYDOWN:
                    if e.key == p.K_SPACE:  # pause button
                        paused = not paused
                        if music:
                            if paused:
                                pause_music()
                            else:
                                unpause_music()
                    elif e.key == p.K_l:
                        leader_info = not leader_info
                    elif e.key == p.K_t:
                        display_date = not display_date
                    elif e.key == p.K_h:
                        hide_controls = not hide_controls
                    elif e.key == p.K_e:
                        events = not events
                    elif e.key == p.K_s:
                        paused = True
                        gs.print_save(time, starting_year)
                        pause_music()
                # mouse handler for game
                elif e.type == p.MOUSEMOTION:
                    mouse_pos = p.mouse.get_pos()  # x, y pos of mouse
                    mouse_row = mouse_pos[1] // SQ_SIZE
                    mouse_col = mouse_pos[0] // SQ_SIZE
                    civ_name = gs.get_civname_from_pos(mouse_row, mouse_col)
                    # print(civ_name)
                    if civ_name != "-":
                        civ_index = gs.get_civ_index_from_name(civ_name)
                        # print(civ_index)
                        civ_info = True
                    else:
                        civ_info = False
            else:  # mouse handler for menu screen
                if e.type == p.MOUSEBUTTONDOWN:
                    mouse_pos = p.mouse.get_pos()  # x, y pos of mouse
                    if menu_state == 0:  # main menu:
                        button_pressed = get_main_menu_button_pressed(mouse_pos)
                        if button_pressed == "create":
                            menu_state = -1
                            not_implemented = False
                            if sound:
                                play_sound("button")
                        elif button_pressed == "load":
                            not_implemented = True
                            if sound:
                                play_sound("button")
                        elif button_pressed == "exit":
                            running = False
                            if sound:
                                play_sound("button")
                        elif button_pressed == "sound":
                            sound = not sound
                            if sound:
                                play_sound("button")
                        elif button_pressed == "music":
                            music = not music
                            if sound:
                                play_sound("button")
                            if not music:
                                pause_music()
                            else:
                                unpause_music()
                        elif button_pressed == "-":
                            not_implemented = False  # reset the thing when user clicks somewhere on the screen
        if not menu:
            draw_game(screen, gs, displaytrees, time, starting_year, civ_index, leader_info,
                      display_date, civ_info, hide_controls, events)
        else:
            menu_state = draw_menu_screen(screen, not_implemented, menu_state, sound, music)
            if menu_state == -1:  # exit menu screen and enter game screen
                menu = False
                time, starting_year, gs = get_map_generation()  # generate the map from settings from menu
                load_game_images()  # load the images
        if not paused and not menu:  # game logic keeps running and updating
            civs = len(gs.civ_name)
            intensity = civs // PERFORMANCE
            time += intensity  # basically calculate at most 20 civs per tick
            if calculate_civ + intensity > civs:
                intensity = civs - calculate_civ
            for i in range(0, intensity):
                gs.civ_decisions(calculate_civ + i, time, starting_year, sound)  # calculating basically 10% of civs at a time
            calculate_civ += intensity
            if calculate_civ >= civs:  # looped through each civ
                calculate_civ = 0
                gs.reduce_truce_timer(civs)  # reduce the truce time for protected cities
        elif not menu:
            display_paused(screen)
        clock.tick(MAX_FPS)
        p.display.flip()


"""
Load the images for easy access later
"""


def load_game_images():
    global SQ_SIZE, MAPSIZEMULTIPLIER, SCREENWIDTH, SCREENHEIGHT
    # objects = {"trees", "hills", "mountain", "snow", "waves"}
    objects = {"tree", "mountain", "snowy-tree", "jungletree", "capital"}
    for objekt in objects:
        IMAGES[objekt] = p.transform.scale(p.image.load('images/' + objekt + '.png'), (SQ_SIZE, SQ_SIZE))
        # allows us to just call IMAGES[image] for easy access to the image


"""
Drawing stuff on the screen
"""


def draw_game(screen, gs, displaytrees, time, starting_year, civ_index, leader_info, display_date, civ_info, hide, event):
    draw_map(screen, gs)
    if displaytrees:
        draw_hills(screen, gs)
        draw_trees(screen, gs)
    display_civs(screen, gs)
    display_place_names(screen, gs)
    if display_date:
        display_time(screen, time, starting_year)
    if civ_info:
        display_civ_info(screen, gs, civ_index)
    if event:
        display_events(screen, gs)  # events before leader info to overlap correctly
    if leader_info:
        display_top_civ(screen, gs)
    display_controls(screen, hide)

# helper functions for draw_game:


def draw_map(screen, gs):
    # same order as the types for ease of use
    for row in range(0, 9 * MAPSIZEMULTIPLIER):
        for col in range(0, 16 * MAPSIZEMULTIPLIER):
            color = tile_to_color[gs.map[row][col]]
            p.draw.rect(screen, p.Color(color), p.Rect((col * SQ_SIZE), (row * SQ_SIZE), SQ_SIZE, SQ_SIZE))
            # epic trick with getting the tile type and the color with same index


def draw_hills(screen, gs):
    pass


def draw_trees(screen, gs):
    for row in range(0, 9 * MAPSIZEMULTIPLIER):
        for col in range(0, 16 * MAPSIZEMULTIPLIER):
            tile_type = gs.map[row][col]
            if tile_type == "f" or tile_type == "i":  # forested grassland or hills
                screen.blit(IMAGES["tree"], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            elif tile_type == "t" or tile_type == "y":  # taiga or forested snowy hills
                screen.blit(IMAGES["snowy-tree"], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            elif tile_type == "j":  # jungle
                screen.blit(IMAGES["jungletree"], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def display_civs(screen, gs):
    global SQ_SIZE, MAPSIZEMULTIPLIER, SCREENWIDTH, SCREENHEIGHT
    for civ in range(0, len(gs.civ_name)):
        civ_area_loc = gs.get_civ_area_dir(civ)
        cap_pos = gs.get_capital_pos(civ)
        for location in civ_area_loc:
            row = location[0]
            col = location[1]
            color_index = gs.civ_color_index[civ] % len(COLOURS)
            rect = (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            draw_transparent_rect(screen, COLOURS[color_index], rect)  # TODO: transparent civ color
            # p.draw.rect(screen, COLOURS[color_index], rect)
        screen.blit(IMAGES["capital"], p.Rect(cap_pos[1] * SQ_SIZE, cap_pos[0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_transparent_rect(surface, color, rect):
    shape_surf = p.Surface(p.Rect(rect).size, p.SRCALPHA)
    p.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)


def display_place_names(screen, gs):
    for row in range(0, 9 * MAPSIZEMULTIPLIER):
        for col in range(0, 16 * MAPSIZEMULTIPLIER):
            name = gs.place_names[row][col]
            if name != "-":
                if name[-1] == "i":
                    text_size = 6
                    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
                    text = font.render(name[:-1], False, p.Color("white"))
                elif name[-1] == "o":
                    text_size = 10
                    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
                    text = font.render(name[:-1], False, p.Color("lightblue"))
                elif name[-1] == "m":
                    text_size = 8
                    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
                    text = font.render(name[:-1], False, p.Color("lightgray"))
                elif name[-1] == "c":
                    text_size = 8
                    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
                    text = font.render(name[:-1], False, p.Color("black"))
                else:
                    text_size = 10
                    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
                    text = font.render(name[:-1], False, p.Color("black"))
                text.get_width()
                text_rect = text.get_rect()
                text_rect.center = (col * SQ_SIZE, row * SQ_SIZE)
                screen.blit(text, text_rect)


def display_civ_info(screen, gs, civ_index):
    try:
        # info box on top of screen
        boxwidth = SCREENWIDTH - SCREENWIDTH//6
        boxheight = SCREENHEIGHT // 12
        linewidth = 5
        # draw a box with lines for a clear infodisplay:
        p.draw.rect(screen, p.Color("white"), p.Rect(0, 0, boxwidth, boxheight))
        p.draw.line(screen, p.Color("black"), (0, boxheight), (boxwidth, boxheight), linewidth)
        p.draw.line(screen, p.Color("black"), (boxwidth, 0), (boxwidth, boxheight), linewidth)
        # print(civ_data)
        area = len(gs.civ_area_list[civ_index])
        pop = round(gs.civ_population[civ_index], 1)
        food = round(gs.civ_food[civ_index], 1)
        production = round(gs.civ_production[civ_index], 1)
        tech = round(gs.civ_tech[civ_index], 1)
        army = round(gs.civ_army_power[civ_index], 1)
        civname = gs.civ_name[civ_index]
        text_string = civname+"   Area: " + str(area) + " Pop: " + str(pop) + " Tech: " + str(tech) + " Army: " + str(army) + " Food: " + str(food) + " Prodution: " + str(production)
        font = p.font.Font('freesansbold.ttf', int(14 * SCREENSIZEMULTIPLIER))
        text = font.render(text_string, False, p.Color("Black"))
        text.get_width()
        text_rect = text.get_rect()
        text_rect.center = (boxwidth//2, boxheight//2)
        screen.blit(text, text_rect)
    except:
        print("Error 404")


def display_top_civ(screen, gs):
    # fills bottom of screen with stats of top dogs by category
    # first draw line
    linewidth = 5
    start = 8  # change this to chance height of stat display, lower = higher
    font = p.font.Font('freesansbold.ttf', int(14 * SCREENSIZEMULTIPLIER))
    line_y = SCREENHEIGHT - SCREENHEIGHT // start
    height = SCREENHEIGHT // start
    p.draw.line(screen, p.Color("black"), (0, line_y), (SCREENWIDTH, line_y), linewidth)
    rect = p.Rect(0, line_y, SCREENWIDTH, height)
    draw_transparent_rect(screen, p.Color("white"), rect)
    # The draw each category separately
    draw_leader_info(height, font, screen)
    draw_area_leader(gs.get_area_leader_index(), height, font, screen, gs)
    draw_pop_leader(gs.get_pop_leader_index(), height, font, screen, gs)
    draw_tech_leader(gs.get_tech_leader_index(), height, font, screen, gs)
    draw_army_leader(gs.get_army_leader_index(), height, font, screen, gs)


def draw_leader_info(height, font, screen):
    # draws the info table
    width = SCREENWIDTH // 5
    string1 = "Leading civ:"
    string2 = "Category:"
    text1 = font.render(string1, False, p.Color("Black"))
    text2 = font.render(string2, False, p.Color("Black"))
    text_rect1 = text1.get_rect()
    text_rect2 = text2.get_rect()
    text_rect1.center = (width//2, SCREENHEIGHT - height + height//3)
    text_rect2.center = (width//2, SCREENHEIGHT - height//3)
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)


def draw_area_leader(index, height, font, screen, gs):
    width = SCREENWIDTH / 5
    string1 = gs.civ_name[index]
    string2 = "Area - "+str(len(gs.civ_area_list[index]))
    text1 = font.render(string1, False, p.Color("Black"))
    text2 = font.render(string2, False, p.Color("Black"))
    text_rect1 = text1.get_rect()
    text_rect2 = text2.get_rect()
    text_rect1.center = (width + width // 2, SCREENHEIGHT - height + height // 3)
    text_rect2.center = (width + width // 2, SCREENHEIGHT - height // 3)
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)


def draw_pop_leader(index, height, font, screen, gs):
    width = SCREENWIDTH / 5
    string1 = gs.civ_name[index]
    string2 = "Population - " + str(gs.civ_population[index])
    text1 = font.render(string1, False, p.Color("Black"))
    text2 = font.render(string2, False, p.Color("Black"))
    text_rect1 = text1.get_rect()
    text_rect2 = text2.get_rect()
    text_rect1.center = (2*width + width // 2, SCREENHEIGHT - height + height // 3)
    text_rect2.center = (2*width + width // 2, SCREENHEIGHT - height // 3)
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)


def draw_tech_leader(index, height, font, screen, gs):
    width = SCREENWIDTH / 5
    string1 = gs.civ_name[index]
    string2 = "Technology - " + str(round(gs.civ_tech[index], 2))
    text1 = font.render(string1, False, p.Color("Black"))
    text2 = font.render(string2, False, p.Color("Black"))
    text_rect1 = text1.get_rect()
    text_rect2 = text2.get_rect()
    text_rect1.center = (3 * width + width // 2, SCREENHEIGHT - height + height // 3)
    text_rect2.center = (3 * width + width // 2, SCREENHEIGHT - height // 3)
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)


def draw_army_leader(index, height, font, screen, gs):
    width = SCREENWIDTH / 5
    string1 = gs.civ_name[index]
    string2 = "Army - " + str(gs.civ_army_power[index])
    text1 = font.render(string1, False, p.Color("Black"))
    text2 = font.render(string2, False, p.Color("Black"))
    text_rect1 = text1.get_rect()
    text_rect2 = text2.get_rect()
    text_rect1.center = (4 * width + width // 2, SCREENHEIGHT - height + height // 3)
    text_rect2.center = (4 * width + width // 2, SCREENHEIGHT - height // 3)
    screen.blit(text1, text_rect1)
    screen.blit(text2, text_rect2)


"""
Time and date logic and displaying
"""


def display_time(screen, time, starting_year):
    boxheight = SCREENHEIGHT//16
    boxwidth = SCREENWIDTH//7
    # background box with borders
    p.draw.rect(screen, p.Color("gray"), p.Rect(SCREENWIDTH - boxwidth, 0, boxwidth, boxheight))
    linewidth = 2
    # horizontal line
    p.draw.line(screen, p.Color("black"), (SCREENWIDTH - boxwidth, boxheight), (SCREENWIDTH, boxheight), linewidth)
    # vertical line
    p.draw.line(screen, p.Color("black"), (SCREENWIDTH - boxwidth, 0), (SCREENWIDTH - boxwidth, boxheight), linewidth)
    text = convert_time_to_date(time, starting_year)
    font = p.font.Font('freesansbold.ttf', int(14 * SCREENSIZEMULTIPLIER))
    textsurface = font.render(text, False, p.Color("black"))
    textRect = textsurface.get_rect()
    textRect.center = (SCREENWIDTH - (boxwidth//2), boxheight//2)  # upper right corner
    screen.blit(textsurface, textRect)


def convert_time_to_date(time, starting_year):
    if time % 30 < 10:
        day = "0"+str(time % 30)
    else:
        day = str(time % 30)
    if ((time//30) % 12) + 1 < 10:
        month = "0"+str(((time//30) % 12) + 1)
    else:
        month = str(((time//30) % 12) + 1)
    year = starting_year + (time//360)
    if year >= 0:
        millennium = "AD "
    else:
        millennium = "BC "
    text = day + "." + month + " " + str(abs(year)) + millennium
    return text


"""
Pause menu eventually
"""


def display_paused(screen):
    text_size = 28
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text = font.render("Paused!", True, p.Color("Black"))
    textRect = text.get_rect()
    textRect.center = (SCREENWIDTH//2, SCREENHEIGHT//2)
    screen.blit(text, textRect)


"""
Controls info
"""


def display_controls(screen, hide):
    size = 12  # change this to scale
    gap = 8
    start = int(SCREENHEIGHT * 2 / 3)
    if hide:
        controls = ["(H)"]
    else:
        # stupid game calculates spaces as different length characters
        controls = ["Controls     (H)",
                    "Pause game    (Spacebar)",
                    "Top Civilizations   (L)",
                    "Display date    (T)",
                    "Event log      (E)",
                    "Save game       (S)",
                    "Display info   (Mouse)"]
    font = p.font.Font('freesansbold.ttf', int(size * SCREENSIZEMULTIPLIER))
    for control in range(len(controls)):
        text = font.render(controls[control], False, p.Color("Black"))
        textRect = text.get_rect()
        textRect.center = (gap + (text.get_width() // 2), start + control * text.get_height())
        screen.blit(text, textRect)


def display_events(screen, gs):
    text_size = 10
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    start = SCREENHEIGHT - (SCREENHEIGHT // 4)
    # draw the box first
    boxheight = start + text_size
    boxwidth = (SCREENWIDTH) // 2
    p.draw.rect(screen, p.Color("white"), p.Rect(SCREENWIDTH - boxwidth, boxheight - 2 * text_size, boxwidth, boxheight))
    linewidth = 2
    # the horizontal line:
    p.draw.line(screen, p.Color("black"), (SCREENWIDTH-boxwidth, boxheight - 2 * text_size),
                (SCREENWIDTH, boxheight - 2 * text_size), linewidth)
    # the vertical line:
    p.draw.line(screen, p.Color("black"), (SCREENWIDTH - boxwidth, boxheight - 2 * text_size),
                (SCREENWIDTH - boxwidth, SCREENHEIGHT), linewidth)
    # then draw the text
    event_list = []
    length_cap = 21
    right_gap = 8  # pixels from right edge
    length = len(gs.world_event_log)
    if length < length_cap:
        for i in range(-1, -length, -1):
            event_list.append(gs.world_event_log[i])
    else:
        for i in range(-1, -length_cap, -1):
            event_list.append(gs.world_event_log[i])
    for event in range(len(event_list)):
        found_name = False
        for name in range(len(gs.civ_name)):
            if gs.civ_name[name] in event_list[event]:
                color_index = gs.civ_color_index[name] % len(COLOURS)  # get the color for the civ in the event log
                found_name = True
                text = font.render(event_list[event], False, COLOURS[color_index])
                textRect = text.get_rect()
                textRect.center = (SCREENWIDTH - right_gap - text.get_width() // 2, start + event * text.get_height())
                screen.blit(text, textRect)
                break  # out of the for loop
        if not found_name:
            text = font.render(event_list[event], False, p.Color("Black"))
            textRect = text.get_rect()
            textRect.center = (SCREENWIDTH - right_gap - text.get_width() // 2, start + event * text.get_height())
            screen.blit(text, textRect)


"""
Menu screen:
- contains basically new game, load game (eventually), sound volume
"""


def get_map_generation():
    global SQ_SIZE, MAPSIZEMULTIPLIER, SCREENWIDTH, SCREENHEIGHT, SCREENSIZEMULTIPLIER, MAX_FPS
    menu = Menu.Menu()
    # set random variables for
    menu.random_initial_vatiables()
    # update global variables
    MAPSIZEMULTIPLIER = menu.mapsize_slider
    SQ_SIZE = int(SCREENWIDTH / (16 * MAPSIZEMULTIPLIER))
    gs = Engine.gameState(MAPSIZEMULTIPLIER)
    gs.generate_game(menu.water_slider, menu.temperature_slider, menu.mountain_slider, menu.island_slider)
    time = 1  # the time variable used to get the date displayed
    starting_year = menu.starting_year  # purely visual
    for i in range(0, len(gs.civ_name)):
        gs.calculate_food_and_pro_for_civ(i, time)
    return time, starting_year, gs


def draw_main_menu_screen(screen, sound, music):
    draw_main_menu_buttons_and_text(screen)
    draw_main_menu_misc(screen, sound, music)


def draw_create_game_screen():
    # displays the the create map parameters sliders and a big create button :)
    pass


def draw_menu_screen(screen, not_implemented, menu_state, sound, music):
    draw_background_image(screen)
    # draw the buttons for the screen
    if menu_state == 0:  # main menu
        draw_main_menu_screen(screen, sound, music)
    elif menu_state == 1:  # create game
        draw_create_game_screen()
    elif menu_state == 2:  # load game
        not_implemented = True
    if not_implemented:
        display_feature_not_implemented(screen)
    return menu_state


"""
Misc stuff in main menu
"""


def draw_background_image(screen):
    background = p.transform.scale(p.image.load('images/background.png'), (SCREENWIDTH, SCREENHEIGHT))
    screen.blit(background, p.Rect(0, 0, SCREENWIDTH, SCREENHEIGHT))


def draw_volume_icons(screen, sound, music):
    width = height = SCREENWIDTH // 30
    start_y = SCREENHEIGHT - SCREENHEIGHT // 8
    gap_between_icons = 20
    start_x = SCREENWIDTH // 2 - width - (gap_between_icons // 2)
    outline_width = 4
    line_thickness = 4
    icons = ["sound", "music"]
    images = {}
    # draw the boxes
    for i in range(0, 2):
        p.draw.rect(screen, p.Color("black"),
                    p.Rect(start_x + i * (width + gap_between_icons), start_y,
                           width, height))
        p.draw.rect(screen, p.Color("white"),
                    p.Rect(start_x + i * (width + gap_between_icons) + outline_width, start_y + outline_width,
                           width - 2 * outline_width, height - 2 * outline_width))
    # draw the icons
    size = width - 2 * outline_width
    gap = int(size * 0.1)
    for icon in range(0, 2):
        images[icons[icon]] = p.transform.scale(p.image.load('images/' + icons[icon] + '.png'), (size - 2 * gap, size - 2 * gap))
        screen.blit(images[icons[icon]], p.Rect(start_x + icon * (width + gap_between_icons) + outline_width + gap,
                                                start_y + outline_width + gap, size - (2 * gap), size - (2 * gap)))
    # draw the cross-over if False
    if not sound:
        p.draw.line(screen, p.Color("black"), (start_x + outline_width, start_y + outline_width),
                    (start_x + width - outline_width, start_y + height - outline_width), line_thickness)
    if not music:
        x = start_x + width + gap_between_icons
        y = start_y
        p.draw.line(screen, p.Color("black"), (x + outline_width, y + outline_width),
                    (x + width - outline_width, y + height - outline_width), line_thickness)


def get_sound_buttons_coordinates():
    width = height = SCREENWIDTH // 30
    start_y = SCREENHEIGHT - SCREENHEIGHT // 8
    gap_between_icons = 20
    start_x = SCREENWIDTH // 2 - width - (gap_between_icons // 2)
    sound_button = [[start_x, start_y], [start_x + width, start_y + height]]
    music_button = [[start_x + width + gap_between_icons, start_y],
                    [start_x + width + gap_between_icons + width, start_y + height]]
    return sound_button, music_button


def draw_game_title(screen):
    text_size = 28
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text = font.render("Civilization Observer Simulator", True, p.Color("Black"))
    textRect = text.get_rect()
    textRect.center = (SCREENWIDTH // 2, SCREENHEIGHT // 4)
    screen.blit(text, textRect)


def draw_version(screen):
    text_size = 12
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text = font.render(VERSION, False, p.Color("Black"))
    textRect = text.get_rect()
    textRect.center = (SCREENWIDTH - (SCREENWIDTH // 14), SCREENHEIGHT - (SCREENHEIGHT // 18))
    screen.blit(text, textRect)


def draw_main_menu_misc(screen, sound, music):
    draw_volume_icons(screen, sound, music)
    draw_game_title(screen)
    draw_version(screen)


"""
Main menu buttons
"""


def draw_main_menu_buttons_and_text(screen):
    draw_main_menu_buttons(screen)


def draw_main_menu_buttons(screen):
    boxheight = SCREENHEIGHT // 8
    boxwidth = SCREENWIDTH // 3
    pixels_for_effect = 5
    gap_between_buttons = SCREENHEIGHT // 40
    text_size = 18
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text_list = ["Create new world!", "Load world", "Exit :("]
    # background box with borders
    for i in range(0, 3):
        p.draw.rect(screen, p.Color("black"), p.Rect((SCREENWIDTH // 2) - (boxwidth // 2),
                                                     (SCREENHEIGHT // 2) - (boxheight // 2) + i * (boxheight + gap_between_buttons), boxwidth, boxheight))
        p.draw.rect(screen, p.Color("white"), p.Rect((SCREENWIDTH // 2) - (boxwidth // 2) + pixels_for_effect,
                                                         (SCREENHEIGHT // 2) - (boxheight // 2) + i * (boxheight + gap_between_buttons) + pixels_for_effect,
                                                     boxwidth - 2 * pixels_for_effect, boxheight - 2 * pixels_for_effect))
        text = font.render(text_list[i], False, p.Color("Black"))
        textRect = text.get_rect()
        textRect.center = (SCREENWIDTH // 2, (SCREENHEIGHT // 2) + i * (gap_between_buttons + boxheight))
        screen.blit(text, textRect)


def get_create_button_dimensions():
    boxheight = SCREENHEIGHT // 10
    boxwidth = SCREENWIDTH // 4
    upper_left = [(SCREENWIDTH // 2) - (boxwidth // 2), (SCREENHEIGHT // 2) - (boxheight // 2)]
    lower_right = [(SCREENWIDTH // 2) + (boxwidth // 2), (SCREENHEIGHT // 2) + (boxheight // 2)]
    return [upper_left, lower_right]


def get_load_button_dimensions():
    boxheight = SCREENHEIGHT // 8
    boxwidth = SCREENWIDTH // 3
    gap_between_buttons = SCREENHEIGHT // 40
    upper_left = [(SCREENWIDTH // 2) - (boxwidth // 2),
                  (SCREENHEIGHT // 2) - (boxheight // 2) + boxheight + gap_between_buttons]
    lower_right = [(SCREENWIDTH // 2) + (boxwidth // 2),
                   (SCREENHEIGHT // 2) + (boxheight // 2) + boxheight + gap_between_buttons]
    return [upper_left, lower_right]


def get_exit_button_dimensions():
    boxheight = SCREENHEIGHT // 8
    boxwidth = SCREENWIDTH // 3
    gap_between_buttons = SCREENHEIGHT // 40
    upper_left = [(SCREENWIDTH // 2) - (boxwidth // 2),
                  (SCREENHEIGHT // 2) - (boxheight // 2) + 2 * (boxheight + gap_between_buttons)]
    lower_right = [(SCREENWIDTH // 2) + (boxwidth // 2),
                   (SCREENHEIGHT // 2) + (boxheight // 2) + 2 * (boxheight + gap_between_buttons)]
    return [upper_left, lower_right]


def get_main_menu_button_pressed(mouse_pos):
    exit = get_exit_button_dimensions()
    create = get_create_button_dimensions()
    load = get_load_button_dimensions()
    sound, music = get_sound_buttons_coordinates()
    if exit[0][0] < mouse_pos[0] < exit[1][0] and exit[0][1] < mouse_pos[1] < exit[1][1]:
        return "exit"
    elif create[0][0] < mouse_pos[0] < create[1][0] and create[0][1] < mouse_pos[1] < create[1][1]:
        return "create"
    elif load[0][0] < mouse_pos[0] < load[1][0] and load[0][1] < mouse_pos[1] < load[1][1]:
        return "load"
    elif sound[0][0] < mouse_pos[0] < sound[1][0] and sound[0][1] < mouse_pos[1] < sound[1][1]:
        return "sound"
    elif music[0][0] < mouse_pos[0] < music[1][0] and music[0][1] < mouse_pos[1] < music[1][1]:
        return "music"
    return "-"


def display_feature_not_implemented(screen):
    # just displays the message for a while and nothing happens
    text_size = 28
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text = font.render("Feature not implemented yet!", True, p.Color("Black"))
    textRect = text.get_rect()
    textRect.center = (SCREENWIDTH // 2, SCREENHEIGHT // 6)
    screen.blit(text, textRect)


def display_loading(screen):
    text_size = 28
    font = p.font.Font('freesansbold.ttf', int(text_size * SCREENSIZEMULTIPLIER))
    text = font.render("Loading, please wait...", True, p.Color("Black"))
    textRect = text.get_rect()
    textRect.center = (SCREENWIDTH // 2, SCREENHEIGHT // 2)
    screen.blit(text, textRect)


"""
sounds and music
"""


def play_sound(sound_name):
    sound = p.mixer.Sound("sounds/"+sound_name+".mp3")
    sound.set_volume(0.5)
    p.mixer.Sound.play(sound)


def load_music():
    p.mixer.music.load("sounds/Tribal.mp3")
    p.mixer.music.set_volume(0.3)
    p.mixer.music.play(-1)


def pause_music():
    p.mixer.music.pause()


def unpause_music():
    p.mixer.music.unpause()


if __name__ == "__main__":  # python likes this for some reason
    main()
