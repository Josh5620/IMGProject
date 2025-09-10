import pygame

class MainMenu():
    def __init__(self,  buttons, title_img, selected_img):
        self.title_image = title_img
        self.selected_img = selected_img
        self.buttons = buttons
        self.selected_index = 0
        self.font = pygame.font.Font(None, 50)
    
    def move_selection(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.buttons)
        print(self.selected_index)

    def draw(self, screen):
        screen.fill((0, 0, 0))  # Clear screen with black
        if self.title_image:
            title_rect = self.title_image.get_rect(center=(screen.get_width() // 2, 150))
            screen.blit(self.title_image, title_rect)
        for i, button in enumerate(self.buttons):
            button.update(i == self.selected_index)
            button.draw(screen)
            if i == self.selected_index: 
                selectArrowPos = [button.topLeft[0] - 40, button.topLeft[1]  + 18]
                screen.blit(self.selected_img, selectArrowPos)

        pygame.display.flip()


class Button():
    def __init__(self, images, pos, text,font, on_activate):
        self.default_image, self.selected_image = images
        self.image = self.default_image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.topLeft = self.rect.topleft
        self.font = font
        self.text = self.font.render(text, True, (255, 255, 255))
        
        

        if self.image == None:
            self.image = self.text
        self.selected = False    
        self.on_activate = on_activate
        
    def update(self, is_selected):
        self.image = self.selected_image if is_selected else self.default_image
        
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def activate(self):
        if self.on_activate:
            self.on_activate()
            print(self.topLeft)