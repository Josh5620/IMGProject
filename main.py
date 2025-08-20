import mainAssets
import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
player = mainAssets.mainCharacter(100, 100)
block = mainAssets.block(200, 200)

def rescaleObject(obj, scale_factor):
    scaledObject = pygame.transform.scale_by(obj, scale_factor)
    return (scaledObject)

player.image = rescaleObject(player.image, 0.2)
player.rect = player.image.get_rect()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    player.draw(screen)
    block.draw(screen)
    
    pygame.display.flip()
    

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.move(-3, 0, [block])
    if keys[pygame.K_RIGHT]:
        player.move(3, 0, [block])
    if keys[pygame.K_UP]:
        player.move(0, -3, [block])
    if keys[pygame.K_DOWN]:
        player.move(0, 3, [block])

    player.startGrav(500)
        
        

pygame.quit()