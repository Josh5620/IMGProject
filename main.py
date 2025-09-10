import pygame
import pytmx
from entities import mainCharacter
from blocks import block, Spikes
from pickups import Coin, Meat
from button import Button, MainMenu

pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 960, 640
scroll_threshold = WIDTH/4
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainCharacter(300, 300)
tmx_data = pytmx.util_pygame.load_pygame("bigMap.tmx")
pygame.display.set_caption("CAT-ching Mushrooms QUEST FOR GRANDMA")

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

# Load heart image once at startup to prevent lag
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
for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            if gid != 0:
                found_gids.add(gid)
                
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get("type") == "tombstone":
                    obstacle = Spikes(x * tile_w, y * tile_h)
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
    global scroll, ground_scroll, player_prev_x, obstacles, player
    print("Game Started")
    running = True
    coin_count = 0

    while running:
        fps = clock.get_fps()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
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

        pygame.display.flip()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            if not player.invulnerable:
                player.lives -= 1
                player.iFrame()
        
        player.update(keys, obstacles)
        
        clock.tick(60)

def main_menu():
    running = True
    start_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2),
        text="Start Game",
        font=pygame.font.Font(None, 50),
        on_activate=start_game
    )
    
    level_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Select Level",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: print("Level Select - Not Implemented")
    )
    
    quit_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 200),
        text="Quit",
        font=pygame.font.Font(None, 50),
        on_activate=pygame.quit
    )
    main_menu = MainMenu(screen, [start_button, level_button, quit_button], pygame.image.load('assets/title.png').convert_alpha(), None)
    while running:
        
        
        main_menu.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    main_menu.move_selection(-1)
                    print("up")
                if event.key == pygame.K_DOWN:
                    main_menu.move_selection(1)
                    print("down")
                if event.key == pygame.K_SPACE:
                    main_menu.buttons[main_menu.selected_index].activate()

        pygame.display.flip()

main_menu()
pygame.quit()
