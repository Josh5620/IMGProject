import pygame
import pytmx
from entities import mainCharacter
from blocks import block, Spikes, start, end
from pickups import Coin, Meat
from menus import Button, baseMenu,  retry_menu, start_menu
from sandbox import sandbox_mode

pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 960, 640
scroll_threshold = WIDTH/4
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainCharacter(300, 300)
tmx_data = pytmx.util_pygame.load_pygame("bigMap.tmx")
pygame.display.set_caption("CAT-ching Mushrooms QUEST FOR GRANDMA")
game_state = "start"


# Add font for FPS counter
font = pygame.font.Font(None, 36)

scroll = 0
ground_scroll = 0
player_prev_x = player.x

bg_images = []
for i in range(0,11):
    bg_image = pygame.image.load(f'assets/BGL/Layer_{i}.png').convert_alpha()
    bg_image = pygame.transform.scale(bg_image, (960, 640))
    bg_images.append(bg_image)

bg_width = bg_images[0].get_width()

def draw_bg():

    start_bg_x = int(scroll // bg_width) - 1
    end_bg_x = int((scroll + WIDTH) // bg_width) + 2
    
    for x in range(start_bg_x, end_bg_x):
        speed = 1
        for i in bg_images:
            bg_pos_x = (x * bg_width) - scroll * speed

            if bg_pos_x > -bg_width and bg_pos_x < WIDTH:
                screen.blit(i, (bg_pos_x, 0))
            speed += 0.1
            

coin = Coin(400, 300)
meat = Meat(200, 300)


heart = pygame.image.load('assets/heart.png').convert_alpha()

def rescaleObject(obj, scale_factor):
    scaledObject = pygame.transform.scale_by(obj, scale_factor)
    return (scaledObject)


heart = rescaleObject(heart, 0.05)

def updateLives(player):
    for i in range(player.lives):
        screen.blit(heart, (10 + i * 30, 10))

TILE_SIZE = 32
tile_w = TILE_SIZE
tile_h = TILE_SIZE


obstacles = []
found_gids = set()
start_position = (300, 300)  # Default start position

for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            if gid != 0:
                found_gids.add(gid)
                
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get("type") == "tombstone":
                    obstacle = Spikes(x * tile_w, y * tile_h)
                elif props and props.get("type") == "start":
                    obstacle = start(x * tile_w, y * tile_h)
                    start_position = (x * tile_w + 30, y * tile_h - 70)  # Spawn above the start block
                elif props and props.get("type") == "end":
                    obstacle = end(x * tile_w, y * tile_h)
                else:
                    obstacle = block(x * tile_w, y * tile_h)
                
                obstacles.append(obstacle)

# Debug output
print(f"All tile IDs found in tilemap: {sorted(found_gids)}")
print(f"Number of obstacles created: {len(obstacles)}")

def draw_map(surface):
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    surface.blit(tile, (x * tile_w, y * tile_h))

def start_game():
    global game_state,scroll, ground_scroll, player_prev_x, obstacles, player
    print("Game Started")
    running = True
    coin_count = 0

    while running:
        fps = clock.get_fps()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                
        screen.fill((0, 0, 0))
        draw_bg()
        
        for obstacle in obstacles:
            obstacle.update_position(ground_scroll)
        
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        tile_x = (x * tile_w) - ground_scroll
                        if tile_x > -tile_w and tile_x < WIDTH:
                            screen.blit(tile, (tile_x, y * tile_h))
        
        coin.update_position(ground_scroll)
        meat.update_position(ground_scroll)
        
        # Check if pickups are offscreen and respawn if necessary
        if coin.is_offscreen(screen):
            coin.respawn(obstacles, ground_scroll)
            print("Coin went offscreen - respawned")
        
        if meat.is_offscreen(screen):
            meat.respawn(obstacles, ground_scroll)
            print("Meat went offscreen - respawned")
        
        coin.draw(screen)
        meat.draw(screen)
        player.draw(screen)
        
        current_player_x = player.rect.x
        
        if current_player_x > (WIDTH - scroll_threshold):
            player.rect.x = WIDTH - scroll_threshold
            if player.scroll_speed > 0:
                scroll += player.scroll_speed
                ground_scroll += player.scroll_speed * 6
        elif current_player_x < scroll_threshold:
            if scroll == 0 and ground_scroll == 0:
                pass
            else:
                player.rect.x = scroll_threshold
                if player.scroll_speed < 0:
                    scroll += player.scroll_speed
                    ground_scroll += player.scroll_speed * 6
                    if scroll < 0:
                        scroll = 0
                    if ground_scroll < 0:
                        ground_scroll = 0
        
        player_prev_x = current_player_x
        
        pygame.draw.line(screen, (255, 0, 0), (scroll_threshold, 0), (scroll_threshold, HEIGHT))
        pygame.draw.line(screen, (255, 0, 0), (WIDTH - scroll_threshold, 0), (WIDTH - scroll_threshold, HEIGHT))
        
        if coin.update(player):
            coin_count += 1
            coin.respawn(obstacles, ground_scroll)
            print("Coin count: ", coin_count)
        
        if meat.update(player):
            player.lives += 1
            meat.respawn(obstacles, ground_scroll)
        
        updateLives(player)
        
        # FPS and debug info
        fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        screen.blit(fps_text, (WIDTH - 150, 10))
        
        # Display scroll values for debugging
        bg_scroll_text = font.render(f"BG Scroll: {scroll:.1f}", True, (255, 255, 255))
        ground_scroll_text = font.render(f"Ground Scroll: {ground_scroll:.1f}", True, (255, 255, 255))
        screen.blit(bg_scroll_text, (WIDTH - 250, 50))
        screen.blit(ground_scroll_text, (WIDTH - 250, 90))
        
        if player.lives <= 0:
            print("Game Over")
            running = False
            game_state = "retry"
            return  # Exit the function when game over
        
        if player.won:

            running = False
            game_state = "start"
            return  # Exit the function when game is won

        pygame.display.flip()
        
        

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            if not player.invulnerable:
                player.lives -= 1
                player.iFrame()
        
        player.update(keys, obstacles)
        
        clock.tick(60)

def quit_to_start():
    global game_state
    game_state = "start"

def start_game_wrapper():
    global game_state, scroll, ground_scroll, player_prev_x, player, start_position
    # Reset game values
    player.lives = 35
    player.x = start_position[0]
    player.y = start_position[1]
    player.rect.x = start_position[0]
    player.rect.y = start_position[1]
    scroll = 0
    ground_scroll = 0
    player_prev_x = player.x
    
    game_state = "playing"
    start_game()

def sandbox_mode_wrapper():
    global game_state
    game_state = "sandbox"

# Main game loop
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
    elif game_state == "playing":
        
        pass
    elif game_state == "sandbox":
        result = sandbox_mode()
        if result == "menu":
            game_state = "start"
        elif result == "quit":
            running = False
    else:
        running = False

pygame.quit()
