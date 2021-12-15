import pygame
import os

main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_image(file):
    """ Load an image from the data directory. """
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))
    return surface.convert_alpha()

def load_sound(file):
    """ Loads a sound from the data directory"""
    file = os.path.join(main_dir, 'data', file)
    return file

TILE_SIZE = 40 # Define the default size of tiles

"""SFX"""
wood_break_sfx = load_sound("wood_box_break.wav") # SFX of wood breaking

other_box_sfx = load_sound("other_box_sfx.wav") # SFX of ricocheting bullets

explosion_sfx = load_sound("explosion.wav") # SFX of explosion

flag_sfx = load_sound("pick_flag.wav") # SFX of picking up flag

tank_shoot_sfx = load_sound("tank_shoot.wav") # SFX of shooting

pick_flag_sfx = load_sound("pick_flag.wav")

"""Images"""
explosion = load_image('explosion.png') # Image of an explosion

grass     = load_image('grass.png') # Image of a grass tile

rockbox   = load_image('rockbox.png') # Image of a rock box (wall)

metalbox  = load_image('metalbox.png') # Image of a metal box

woodbox   = load_image('woodbox.png') # Image of a wood box

flag      = load_image('flag.png') # Image of flag

bullet = load_image('bullet.png')
bullet = pygame.transform.scale(bullet, (10, 10))
bullet = pygame.transform.rotate(bullet, -90)

# List of image of tanks of different colors
tanks     = [load_image('tank_orange.png'), load_image('tank_blue.png'), load_image('tank_white.png'),
             load_image('tank_yellow.png'), load_image('tank_red.png'),  load_image('tank_gray.png')]

# List of image of bases corresponding to the color of each tank
bases     = [load_image('base_orange.png'), load_image('base_blue.png'), load_image('base_white.png'),
             load_image('base_yellow.png'), load_image('base_red.png'),  load_image('base_gray.png')]
