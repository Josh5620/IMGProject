import pygame

game_level = 1
class baseMenu():
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

def start_menu(WIDTH, HEIGHT, screen, start_game):
    running = True
    start_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2),
        text="Start Game",
        font=pygame.font.Font(None, 50),
        on_activate=start_game
    )
    
    def open_level_select():
        nonlocal running
        level_select_menu(WIDTH, HEIGHT, screen)
    
    level_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Select Level",
        font=pygame.font.Font(None, 50),
        on_activate=open_level_select
    )
    
    def quit_game():
        nonlocal running
        running = False
        pygame.quit()
        exit()
    
    quit_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 200),
        text="Quit",
        font=pygame.font.Font(None, 50),
        on_activate=quit_game
    )
    main_menu = baseMenu ([start_button, level_button, quit_button], pygame.image.load('assets/title.png').convert_alpha(), pygame.image.load('assets/arrow.png').convert_alpha())  # Load an actual arrow image
    while running:
        
        
        main_menu.draw(screen)
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
                    running = False  # Exit menu after button press
                if event.key == pygame.K_p:  # Press P to access sandbox
                    setattr(pygame, '_game_state', 'sandbox')
                    running = False

        pygame.display.flip()

def set_level(level_num):
    global game_level
    game_level = level_num
    print(f"Level selected is {level_num}")

def level_select_menu(WIDTH, HEIGHT, screen):
    running = True
    
    def select_level_and_exit(level_num):
        nonlocal running
        set_level(level_num)
        running = False
    
    def go_back():
        nonlocal running
        running = False
    
    level1_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 - 50),
        text="Level 1",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(1)
    )
    
    level2_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 50),
        text="Level 2",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(2)
    )
    
    back_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 150),
        text="Back",
        font=pygame.font.Font(None, 50),
        on_activate=go_back
    )
    
    level_menu = baseMenu([level1_button, level2_button, back_button],
                         pygame.image.load('assets/diedtitle.png').convert_alpha(),
                         pygame.image.load('assets/arrow.png').convert_alpha())
    
    while running:
        level_menu.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    level_menu.move_selection(-1)
                if event.key == pygame.K_DOWN:
                    level_menu.move_selection(1)
                if event.key == pygame.K_SPACE:
                    level_menu.buttons[level_menu.selected_index].activate()
                    running = False

        pygame.display.flip()

def retry_menu(WIDTH, HEIGHT, screen, retry_function, quit_function):
    running = True
    
    retry_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2),
        text="Retry",
        font=pygame.font.Font(None, 50),
        on_activate=retry_function
    )
    
    quit_button = Button(
        images=(pygame.image.load('assets/button.png').convert_alpha(),
                pygame.image.load('assets/highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Quit",
        font=pygame.font.Font(None, 50),
        on_activate=quit_function
    )
    
    retry_menu_obj = baseMenu([retry_button, quit_button], 
                             pygame.image.load('assets/diedtitle.png').convert_alpha(), 
                             pygame.image.load('assets/arrow.png').convert_alpha())
    
    while running:
        retry_menu_obj.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    retry_menu_obj.move_selection(-1)
                if event.key == pygame.K_DOWN:
                    retry_menu_obj.move_selection(1)
                if event.key == pygame.K_SPACE:
                    retry_menu_obj.buttons[retry_menu_obj.selected_index].activate()
                    running = False  

        pygame.display.flip()
