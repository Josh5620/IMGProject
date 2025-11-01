import pygame
from game import Level1, Level2, FinalBossLevel
from menus import retry_menu, start_menu, game_level, run_game_intro, run_BossIntro, getLevel, pause_menu, music_manager, run_level2_tutorial
from sandbox import sandbox_mode

pygame.init()
WIDTH, HEIGHT = 960, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shroomlight : The Last Bloom")
game_state = "start"

level1 = Level1(WIDTH, HEIGHT)
level2 = Level2(WIDTH, HEIGHT)

def start_game_wrapper():
    global game_state
    game_level = getLevel()
    print(f"Starting game with Level {game_level}")
    print(game_state)

    run_game_intro(WIDTH, HEIGHT, screen)
    

    if game_level == 1:
        run_level2_tutorial(WIDTH, HEIGHT, screen)
        music_manager.play('level1')  # Play Level 1 music
        result = level1.run(screen)
    elif game_level == 2:
        run_level2_tutorial(WIDTH, HEIGHT, screen)  # Show controls tutorial
        music_manager.play('level2')  # Play Level 2 music
        result = level2.run(screen)
    else:
        # Default to Level 1
        music_manager.play('level1')  # Play Level 1 music
        result = level1.run(screen)
    
    if result == "quit":
        game_state = "quit"
    elif result == "game_over":
        game_state = "retry"
    elif result == "boss_level1":
        game_state = "boss_level1"
    elif result == "boss_level_easy":
        game_state = "boss_level_easy"
    elif result == "boss_level_normal":
        game_state = "boss_level_normal"
    elif result == "boss_level_hard":
        game_state = "boss_level_hard"
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
        run_BossIntro(WIDTH, HEIGHT, screen)
        music_manager.play('boss')  # Play boss music
        if result == "quit":
            running = False
        elif result == "game_over":
            game_state = "retry"
        else:
            game_state = "start"
    elif game_state in ["boss_level_easy", "boss_level_normal", "boss_level_hard"]:
        # Determine difficulty from game state
        if game_state == "boss_level_easy":
            difficulty = "easy"
        elif game_state == "boss_level_hard":
            difficulty = "hard"
        else:
            difficulty = "normal"
        
        run_BossIntro(WIDTH, HEIGHT, screen)
        music_manager.play('boss')  # Play boss music
        
        # Create and run the boss level
        boss_level = FinalBossLevel(WIDTH, HEIGHT, difficulty)
        result = boss_level.run(screen)
        
        if result == "quit":
            running = False
        elif result == "game_over":
            game_state = "retry"
        elif result == "victory":
            # Player won the boss fight - could go to credits or back to menu
            game_state = "start"
        else:
            game_state = "start" 
    else:
        running = False

pygame.quit()
