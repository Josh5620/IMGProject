import pygame
import pytmx
from entities import mainCharacter
from blocks import block, Spikes
from pickups import Coin, Meat

pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 960, 640
scroll_threshold = WIDTH/4
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainCharacter(300, 300)
tmx_data = pytmx.util_pygame.load_pygame("tilemap.tmx")
pygame.display.set_caption("CAT-ching Mushrooms QUEST FOR GRANDMA")

# Add font for FPS counter
font = pygame.font.Font(None, 36)

scroll = 0
player_prev_x = player.x  # Track player's previous x position

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
            

# Create a coin
coin = Coin(400, 300)

# Create a meat
meat = Meat(200, 300)

# Load heart image once at startup to prevent lag
heart = pygame.image.load('assets/heart.png').convert_alpha()

def rescaleObject(obj, scale_factor):
    scaledObject = pygame.transform.scale_by(obj, scale_factor)
    return (scaledObject)


heart = rescaleObject(heart, 0.05)

def updateLives(player):
    # Draw the lives counter using pre-loaded heart
    for i in range(player.lives):
        screen.blit(heart, (10 + i * 30, 10))

TILE_SIZE = 32
tile_w = TILE_SIZE
tile_h = TILE_SIZE

TILE_FACTORIES = { # change the tile IDs to match your TMX file
    1: lambda x, y: Spikes(x, y),  
    2: lambda x, y: block(x, y),   
    3: lambda x, y: block(x, y)
}

obstacles = []
found_gids = set()
for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        #print(f"Processing layer: {layer.name}")  # Debug line
        for x, y, gid in layer:
            if gid != 0:  # Skip empty tiles
                found_gids.add(gid)
                #print(f"Found tile at ({x}, {y}) with GID: {gid}")  
                #Debug line and used to find corrosponding tileID until we find better method
            if gid in TILE_FACTORIES:
                obstacle = TILE_FACTORIES[gid](x * tile_w, y * tile_h)
                obstacles.append(obstacle)

print(f"All tile IDs found in tilemap: {sorted(found_gids)}")
print(f"Number of obstacles created: {len(obstacles)}")

def draw_map(surface):
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    surface.blit(tile, (x * tile_w, y * tile_h))

running = True
coin_count = 0

while running:
    # Calculate FPS
    fps = clock.get_fps()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.fill((0, 0, 0))
    draw_bg()
    

    # Draw all obstacle objects (blocks, spikes, etc.)
    for obstacle in obstacles:
        obstacle.draw(screen)
    draw_map(screen)
    # Draw game objects
    coin.draw(screen)
    meat.draw(screen)
    player.draw(screen)
    
    # Only scroll when player has moved and is past the thresholds
    current_player_x = player.rect.x
    if current_player_x != player_prev_x:  # Player has moved
        if current_player_x > (WIDTH - scroll_threshold):  # Player is past right threshold
            if player.scroll_speed > 0:  # Only allow rightward scrolling
                scroll += player.scroll_speed
        elif current_player_x < scroll_threshold:  # Player is past left threshold
            if player.scroll_speed < 0 and scroll > 0:  # Only allow leftward scrolling if not at left edge
                scroll += player.scroll_speed
    
    player_prev_x = current_player_x  # Update previous position
    
    pygame.draw.line(screen, (255, 0, 0), (scroll_threshold, 0), (scroll_threshold, HEIGHT))
    pygame.draw.line(screen, (255, 0, 0), (WIDTH - scroll_threshold, 0), (WIDTH - scroll_threshold, HEIGHT))
    

    
    # Check if player collected the coin
    if coin.update(player):
        coin_count += 1
        coin.respawn(obstacles)  # Respawn at random location
        print("Coin count: ", coin_count)
    
    if meat.update(player):
        player.lives += 1
        meat.respawn(obstacles)
    
    updateLives(player)
    
    # Draw FPS counter
    fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
    screen.blit(fps_text, (WIDTH - 150, 10))
    
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

pygame.quit()
