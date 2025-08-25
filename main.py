import mainAssets
import pygame


    
    
pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainAssets.mainCharacter(300, 70)

# Create a coin
coin = mainAssets.Coin(400, 300)


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
cols = WIDTH // TILE_SIZE   # 40
rows = HEIGHT // TILE_SIZE  # 3


tilemap = []
for r in range(rows):
    row = []
    for c in range(cols):
        if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
            row.append(1)  # wall
        else:
            row.append(0)  # empty
    tilemap.append(row)

obstacles = []
for row in range(rows):
    for col in range(cols):
        if tilemap[row][col] == 1:
            # Create spikes for the left wall (col == 0), blocks for other walls
            if col == 0:
                spike = mainAssets.Spikes(col * TILE_SIZE, row * TILE_SIZE)
                obstacles.append(spike)
            else:
                block = mainAssets.block(col * TILE_SIZE, row * TILE_SIZE)
                obstacles.append(block)

running = True
coin_count = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    

    screen.fill((0, 0, 0))
    
    
    for block in obstacles:
        block.draw(screen)
    player.draw(screen)
    coin.draw(screen)
    
    # Check if player collected the coin
    if coin.update(player):
        coin_count += 1
        coin.respawn(obstacles)  # Respawn at random location
        print("Coin count: ", coin_count)
    
    updateLives(player)
    if player.lives <= 0:
        print("Game Over")
        running = False

    pygame.display.flip()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        if not player.invulnerable:
            life_counter -= 1
            player.iFrame()
    
    
    player.update(keys, obstacles)
    

    clock.tick(30)

    
        
        

pygame.quit()