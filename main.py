import mainAssets
import pygame
import pytmx

    
    
pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainAssets.mainCharacter(300, 70)
tmx_data = pytmx.util_pygame.load_pygame("tilemap.tmx")

# Create a coin
coin = mainAssets.Coin(400, 300)

# Create a meat
meat = mainAssets.Meat(200, 300)

def rescaleObject(obj, scale_factor):
    scaledObject = pygame.transform.scale_by(obj, scale_factor)
    return (scaledObject)

def updateLives(player):
    # Update the lives display
    heart = pygame.image.load('heart.png')
    heart = rescaleObject(heart, 0.05)
    heart_rect = heart.get_rect()
    heart_rect.topleft = (10, 10)
    
    # Draw the lives counter
    for i in range(player.lives):
        screen.blit(heart, (10 + i * 30, 10))
    
    

TILE_SIZE = 20
tile_w = TILE_SIZE
tile_h = TILE_SIZE

TILE_FACTORIES = { # change the tile IDs to match your TMX file
    1: lambda x, y: mainAssets.block(x, y),  
    2: lambda x, y: mainAssets.Spikes(x, y),   
    3: lambda x, y: mainAssets.Spikes(x, y),    
}

# Load obstacles from tilemap
obstacles = []
found_gids = set()
for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        
        for x, y, gid in layer:
            if gid != 0:  # Skip empty tiles
                found_gids.add(gid)
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
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    

    screen.fill((0, 0, 0))
    
    # Draw all obstacle objects (blocks, spikes, etc.)
    for obstacle in obstacles:
        obstacle.draw(screen)
    draw_map(screen)
    # Draw game objects
    coin.draw(screen)
    meat.draw(screen)
    player.draw(screen)
    
    # Check if player collected the coin
    if coin.update(player):
        coin_count += 1
        coin.respawn(obstacles)  # Respawn at random location
        print("Coin count: ", coin_count)
    
    if meat.update(player):
        player.lives += 1
        meat.respawn(obstacles)
    
    updateLives(player)
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
    

    clock.tick(30)

    
        
        

pygame.quit()