import mainAssets
import pygame


    
    
pygame.init()
clock = pygame.time.Clock()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
player = mainAssets.mainCharacter(300, 300)


def rescaleObject(obj, scale_factor):
    scaledObject = pygame.transform.scale_by(obj, scale_factor)
    return (scaledObject)

player.image = rescaleObject(player.image, 0.2)
old_pos = player.rect.topleft
player.rect = player.image.get_rect()
player.rect.topleft = old_pos

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
            block = mainAssets.block(col * TILE_SIZE, row * TILE_SIZE)
            obstacles.append(block)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    

    screen.fill((0, 0, 0))
    # lags code change it to just pixels 
    for block in obstacles:
        block.draw(screen)
    player.draw(screen)
    pygame.display.flip()

    if player.check_collision(obstacles):
        print("Collision detected!")
    
    

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.move(-5, 0, obstacles)
    if keys[pygame.K_RIGHT]:
        player.move(5, 0, obstacles)
    if keys[pygame.K_UP]:
        player.move(0, -5, obstacles)
    if keys[pygame.K_DOWN]:
        player.move(0, 5, obstacles)
    clock.tick(60)

    
        
        

pygame.quit()