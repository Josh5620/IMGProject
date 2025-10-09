import pygame
from game import Level1, BossLevel1
from menus import retry_menu, start_menu, game_level, run_game_intro
from sandbox import sandbox_mode


pygame.init()
WIDTH, HEIGHT = 960, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CAT-ching Mushrooms QUEST FOR GRANDMA")

game_state = "start"



def start_game_wrapper():
    global game_state
    
    print(f"Starting game with Level {game_level}")
    print(game_state)

    run_game_intro(WIDTH, HEIGHT, screen)

    if game_level == 1:
        level1 = Level1(WIDTH, HEIGHT)
        result = level1.run(screen)
    elif game_level == 2:
        
        print("Level 2 not implemented yet, running Level 1")
        result = level1.run(screen)
    else:
        # Default to Level 1
        result = level1.run(screen)
    
    if result == "quit":
        game_state = "quit"
    elif result == "game_over": 
        game_state = "retry"
    elif result == "boss_level1":
        game_state = "boss_level1"
    else:
        game_state = "start"

def quit_to_start():
    global game_state
    game_state = "start"

running = True
while running:
    # Check for sandbox mode trigger from menu
    if hasattr(pygame, '_game_state') and pygame._game_state == 'sandbox':
        game_state = 'sandbox'
        delattr(pygame, '_game_state')
    
    if game_state == "start":
        start_menu(WIDTH, HEIGHT, screen, start_game_wrapper)
    elif game_state == "retry":
        retry_menu(WIDTH, HEIGHT, screen, start_game_wrapper, quit_to_start)
    elif game_state == "sandbox":
        result = sandbox_mode(screen)
        if result == "menu":
            game_state = "start"
        elif result == "quit":
            running = False
    elif game_state == "quit":
        running = False
    elif game_state == "boss_level1":
        boss_level1 = BossLevel1(WIDTH, HEIGHT)
        boss_level1.run(screen)
        
    else:
        running = False

pygame.quit()
