import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
import sys

#----- Initialisation -----#

#-- Initialise the display
pygame.init()
pygame.display.set_mode()

#-- Initialise the clock
clock = pygame.time.Clock()

#-- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0,  0.0)
space.damping = 0.1 # Adds friction to the ground for all objects

#-- Initialise
pygame.display.set_caption('Capture The Flag')
font = pygame.font.SysFont("Arial", 30)

#-- Import from the ctf framework
import ai
import images
import gameobjects
import maps

#-- Constants
FRAMERATE = 60

#-- Variables
try:
    argument = sys.argv[1]
except:
    raise IndexError("Missing 1 Argument (--singleplayer or --hot-multiplayer)")
    sys.exit()
fog_of_war = False

#   Define the current level
current_map         = maps.map0

#   List of all game objects
game_objects_list   = []
tanks_list          = []
ai_list             = []
starttime           = []

# Load all sounds
wood_break_sound = pygame.mixer.Sound(images.wood_break_sfx)
other_box_break_sound = pygame.mixer.Sound(images.other_box_sfx)
explosion_sound = pygame.mixer.Sound(images.explosion_sfx)
wood_break_sound.set_volume(0.1)
other_box_break_sound.set_volume(0.1)
explosion_sound.set_volume(0.1)

#-- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)

def collision_bullet_box(arb, space, data):
    '''
    creates collision between bullets and create_boxes
    '''
    box = arb.shapes[0]
    bullet = arb.shapes[1]

    if box.parent.destructable:
        box.parent.box_hp += 1
        if bullet.parent in game_objects_list:
            wood_break_sound.play()
            game_objects_list.remove(bullet.parent)
            space.remove(bullet, bullet.body)
        if box.parent.box_hp == 2:
            box.parent.box_hp = 0
            game_objects_list.remove(box.parent)
            space.remove(box, box.body)
            explosion = gameobjects.Explosion(box.body.position[0], box.body.position[1], game_objects_list)
    else:
        if bullet.parent in game_objects_list:
            other_box_break_sound.play()
            game_objects_list.remove(bullet.parent)
            space.remove(bullet, bullet.body)

    return False

handler = space.add_collision_handler(3, 1)
handler.pre_solve = collision_bullet_box

def collision_bullet_tank(arb, space, data):
    '''
    creates collision between bullets and tanks
    '''
    tank = arb.shapes[0]
    bullet = arb.shapes[1]
    if bullet.parent.tank == tank.parent:
        return False

    if tank.parent.spawn_protection <= 0:
        tank.parent.tank_hp += 1
        if tank.parent.tank_hp == 3:
            explosion_sound.play()
            tank.parent.tank_hp = 0
            tank.parent.spawn_protection = 150
            explosion = gameobjects.Explosion(tank.body.position[0], tank.body.position[1], game_objects_list)
            tank.body.position = tank.parent.start_position

    if bullet.parent in game_objects_list:
        game_objects_list.remove(bullet.parent)
        space.remove(bullet, bullet.body)

    if tank.parent.flag == flag:
        gameobjects.Tank.drop_flag(tank.parent, flag)

    return False

handler = space.add_collision_handler(2, 1)
handler.pre_solve = collision_bullet_tank
handler = space.add_collision_handler(1, 2)



#set barriers
static_body = space.static_body
space.add(pymunk.Segment(static_body, (0,0), (current_map.width,0), 0.0))
space.add(pymunk.Segment(static_body, (0,0), (0,current_map.height), 0.0))
space.add(pymunk.Segment(static_body, (current_map.width,0), (current_map.width,current_map.height), 0.0))
space.add(pymunk.Segment(static_body, (0,current_map.height), (current_map.width,current_map.height), 0.0))



#-- Generate the background
background = pygame.Surface(screen.get_size())

#   Copy the grass tile all over the level area
for x in range(0, current_map.width):
    for y in range(0,  current_map.height):
        # The call to the function "blit" will copy the image
        # contained in "images.grass" into the "background"
        # image at the coordinates given as the second argument
        background.blit(images.grass,  (x*images.TILE_SIZE, y*images.TILE_SIZE))


#-- Create the boxes
def create_boxes():
    ''' creates box objects and makes them visible'''
    for x in range(0, current_map.width):
        for y in range(0,  current_map.height):
            # Get the type of boxes
            box_type  = current_map.boxAt(x, y)
            # If the box type is not 0 (aka grass tile), create a box
            if(box_type != 0):
                # Create a "Box" using the box_type, aswell as the x,y coordinates,
                # and the pymunk space
                box = gameobjects.get_box_with_type(x, y, box_type, space)
                game_objects_list.append(box)


#-- Create the tanks/bases
# Loop over the starting poistion
def create_tanks_and_bases():
    ''' creates tank/flag objects and makes them visible'''
    for i in range(0, len(current_map.start_positions)):
        # Get the starting position of the tank "i"
        pos = current_map.start_positions[i]
        #create bases
        base = gameobjects.GameVisibleObject(pos[0], pos[1], images.bases[i])
        # Create the tank, images.tanks contains the image representing the tank
        tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)
        # Add the tank to the list of tanks
        tanks_list.append(tank)
        starttime.append(0)
        game_objects_list.append(base)
        game_objects_list.append(tank)
        if argument == "--singleplayer" and i >= 1:
            AI = ai.Ai(tank, game_objects_list, tanks_list[i], space, current_map)
            ai_list.append(AI)
        if argument == "--hot-multiplayer" and i >= 2:
            AI = ai.Ai(tank, game_objects_list, tanks_list[i], space, current_map)
            ai_list.append(AI)

#-- Create the flag
flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
game_objects_list.append(flag)

bg_music = pygame.mixer.music.load("data/music.wav")
pygame.mixer.music.play(-1)



# main loop
def main_loop():
    #-- Control whether the game run
    running = True
    skip_update = 0
    while running:
        #-- Handle the events
        for event in pygame.event.get():
            # Check if we receive a QUIT event (for instance, if the user press the
            # close button of the wiendow) or if the user press the escape key.
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

            if argument == "--singleplayer":

                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        tanks_list[0].accelerate()
                    if event.key == K_DOWN:
                        tanks_list[0].decelerate()
                    if event.key == K_RIGHT:
                        tanks_list[0].turn_right()
                    if event.key == K_LEFT:
                        tanks_list[0].turn_left()
                if event.type == KEYUP:
                    if (event.key == K_DOWN or event.key == K_UP):
                        tanks_list[0].stop_moving()
                    if (event.key == K_RIGHT or event.key == K_LEFT):
                        tanks_list[0].stop_turning()
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        tanks_list[0].shoot(space, tanks_list[0], game_objects_list)

            if argument == "--hot-multiplayer":
                #player one
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        tanks_list[0].accelerate()
                    if event.key == K_DOWN:
                        tanks_list[0].decelerate()
                    if event.key == K_RIGHT:
                        tanks_list[0].turn_right()
                    if event.key == K_LEFT:
                        tanks_list[0].turn_left()
                if event.type == KEYUP:
                    if (event.key == K_DOWN or event.key == K_UP):
                        tanks_list[0].stop_moving()
                    if (event.key == K_RIGHT or event.key == K_LEFT):
                        tanks_list[0].stop_turning()
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        tanks_list[0].shoot(space,tanks_list[0], game_objects_list)

                #player two
                if event.type == KEYDOWN:
                    if event.key == K_w:
                        tanks_list[1].accelerate()
                    if event.key == K_s:
                        tanks_list[1].decelerate()
                    if event.key == K_d:
                        tanks_list[1].turn_right()
                    if event.key == K_a:
                        tanks_list[1].turn_left()
                if event.type == KEYUP:
                    if (event.key == K_s or event.key == K_w):
                        tanks_list[1].stop_moving()
                    if (event.key == K_d or event.key == K_a):
                        tanks_list[1].stop_turning()
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        tanks_list[1].shoot(space, tanks_list[1], game_objects_list)

        #tank capture the flag
        for i in range(len(tanks_list)):
            tanks_list[i].try_grab_flag(flag)
            if tanks_list[i].has_won():
                running = False

        #start the ai
        for ai in ai_list:
            ai.decide()

        #-- Update physics
        if skip_update == 0:
            # Loop over all the game objects and update their speed in function of their
            # acceleration.
            for obj in game_objects_list:
                obj.update()
            skip_update = 2
        else:
            skip_update -= 1

        #   Check collisions and update the objects position
        space.step(1 / FRAMERATE)

        #   Update object that depends on an other object position (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()


        #-- Update Display

        # Display the background on the screen
        screen.blit(background, (0, 0))


        for obj in game_objects_list:
            obj.update_screen(screen)


        #Fog of War
        if fog_of_war:
            colour = (0, 0, 0)
            fog_screen = pygame.Surface(current_map.rect().size)
            fog_screen.fill(colour)
            pygame.draw.circle(fog_screen, (50, 50, 50), tanks_list[0].body.position * \
             current_map.rect().size[0] // current_map.width, 150)
            #for second player
            if argument == "--hot-multiplayer":
                pygame.draw.circle(fog_screen, (50, 50, 50), tanks_list[1].body.position * \
                    current_map.rect().size[1] // current_map.width, 150)
            fog_screen.set_colorkey((50, 50, 50))
            screen.blit(fog_screen, (0, 0))


        # Update the display of the game objects on the screen


        #   Redisplay the entire screen (see double buffer technique)
        pygame.display.flip()

        #   Control the game framerate
        clock.tick(FRAMERATE)

#call the defined functions
create_boxes()
create_tanks_and_bases()
main_loop()
