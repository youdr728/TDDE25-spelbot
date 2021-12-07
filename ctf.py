import pygame
from pygame.locals import *
from pygame.color import *
import pymunk

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


#-- Import from the ctf framework
import ai
import images
import gameobjects
import maps

#-- Constants
FRAMERATE = 60

#-- Variables
#   Define the current level
current_map         = maps.map0
#   List of all game objects
game_objects_list   = []
tanks_list          = []
ai_list             = []
bullet_list         = []
box_list            = []
starttime           = []

#-- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)

def collision_bullet_box(arb, space, data):
    box = arb.shapes[0]
    bullet = arb.shapes[1]

    if box.parent.destructable:
        if bullet.parent in game_objects_list:
            wood_break_sfx = pygame.mixer.Sound("data/wood_box_break.wav")
            pygame.mixer.Sound.play(wood_break_sfx)

            box_list.remove(box.parent)
            game_objects_list.remove(bullet.parent)
            game_objects_list.remove(box.parent)
            space.remove(bullet, bullet.body)
            space.remove(box, box.body)
    else:
        if bullet.parent in game_objects_list:
            other_box_sfx = pygame.mixer.Sound("data/other_box_sfx.wav")
            pygame.mixer.Sound.play(other_box_sfx)

            game_objects_list.remove(bullet.parent)
            space.remove(bullet, bullet.body)

    return False

handler = space.add_collision_handler(3, 1)
handler.pre_solve = collision_bullet_box

def collision_bullet_tank(arb, space, data):
    tank = arb.shapes[0]
    bullet = arb.shapes[1]
    if bullet.parent.tank == tank.parent:
        return False

    if bullet.parent in game_objects_list and tank.parent.spawn_protection <= 0:
        tank.body.position = tank.parent.start_position
        #explosion = pygame.mixer.Sound("data/explosion.wav")
        #pygame.mixer.Sound.play(explosion)
        #bullet_list.remove(bullet.parent)
        game_objects_list.remove(bullet.parent)
        space.remove(bullet, bullet.body)
        tank.parent.spawn_protection = 150
    if tank.parent.flag == flag:
        gameobjects.Tank.drop_flag(tank.parent, flag)


    return False

handler = space.add_collision_handler(2, 1)
handler.pre_solve = collision_bullet_tank

def collision_bullet_bullet(arb, space, data):
    bullet = arb.shapes[0]
    if bullet.parent in game_objects_list:
        bullet_list.remove(bullet.parent)
        game_objects_list.remove(bullet.parent)
    space.remove(bullet, bullet.body)



    """if bullet.parent in game_objects_list:
        bullet_list.remove(bullet1.parent)
        game_objects_list.remove(bullet1.parent)
        space.remove(bullet, bullet1.body)
        bullet_list.remove(bullet2.parent)
        game_objects_list.remove(bullet2.parent)
        space.remove(bullet, bullet2.body)"""

    return False

handler = space.add_collision_handler(1, 0)
handler.pre_solve = collision_bullet_bullet

def collision_bullet_barrier(arb, space, data):
    bullet = arb.shapes[0]
    if bullet.parent in game_objects_list:
        #bullet_list.remove(bullet.parent)
        game_objects_list.remove(bullet.parent)
    space.remove(bullet, bullet.body)

    return False

handler = space.add_collision_handler(1, 0)
handler.pre_solve = collision_bullet_barrier



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
                box_list.append(box)


#-- Create the tanks/bases
# Loop over the starting poistion
def create_tanks_and_bases():
    for i in range(0, len(current_map.start_positions)):
        # Get the starting position of the tank "i"
        pos = current_map.start_positions[i]
        #create bases
        base = gameobjects.GameVisibleObject(pos[0], pos[1], images.bases[i])
        # Create the tank, images.tanks contains the image representing the tank
        tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)
        # Add the tank to the list of tanks
        AI = ai.Ai(tank, game_objects_list, tanks_list, space, current_map)
        ai_list.append(AI)
        tanks_list.append(tank)
        starttime.append(0)
        game_objects_list.append(base)
        game_objects_list.append(tank)

#-- Create the flag

flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
game_objects_list.append(flag)

#bg_music = pygame.mixer.music.load("data/music.wav")
#pygame.mixer.music.play(-1)

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
            if event.type == KEYDOWN:
                if event.key == K_w:
                    tanks_list[1].accelerate()
                if event.key == K_s:
                    tanks_list[1].decelerate()
                if event.key == K_d:
                    tanks_list[1].turn_right()
                if event.key == K_a:
                    tanks_list[1].turn_left()
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
                if (event.key == K_w or event.key == K_s):
                    tanks_list[1].stop_moving()
                if (event.key == K_d or event.key == K_a):
                    tanks_list[1].stop_turning()
            if event.type == KEYDOWN:
                if event.key == K_RSHIFT:
                    if tanks_list[0].shoot_tick >= 60:
                        bullet = tanks_list[0].shoot(space,tanks_list[0])
                        game_objects_list.append(bullet)
                        bullet_list.append(bullet)



                if event.key == K_LSHIFT:
                    if tanks_list[1].shoot_tick >= 60:
                        bullet = tanks_list[1].shoot(space)
                        game_objects_list.append(bullet)
                        bullet_list.append(bullet)
                if event.key == K_c:
                    pass
                if event.key == K_x:
                    pass

        tanks_list[0].try_grab_flag(flag)
        tanks_list[1].try_grab_flag(flag)

        for i in range(len(tanks_list)):
            tanks_list[i].try_grab_flag(flag)
            if tanks_list[i].has_won():
                running = False

        #for ai in ai_list:
         #   ai.decide()

        #tile_neighbors = ai_list[0].get_tile_neighbors(tanks_list[0].body.position)

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
        handler = space.add_collision_handler(1, 2)

        space.step(1 / FRAMERATE)

        #   Update object that depends on an other object position (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()


        #-- Update Display

        # Display the background on the screen
        screen.blit(background, (0, 0))


        for obj in game_objects_list:
            obj.update_screen(screen)



        # Update the display of the game objects on the screen


        #   Redisplay the entire screen (see double buffer technique)
        pygame.display.flip()

        #   Control the game framerate
        clock.tick(FRAMERATE)


create_boxes()
create_tanks_and_bases()
main_loop()
