import pygame

game_level = 2
class baseMenu():
    def __init__(self,  buttons, title_img, selected_img):
        self.title_image = title_img
        self.selected_img = selected_img
        self.buttons = buttons
        self.selected_index = 0
        self.font = pygame.font.Font(None, 50)
        self.background = pygame.image.load('assets/menuBack.jpeg').convert()
        self.background = pygame.transform.scale(self.background, (960, 640))
    
    def move_selection(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.buttons)
        print(self.selected_index)

    def draw(self, screen):
        screen.fill((0, 0, 0))  # Clear screen with black
        screen.blit(self.background, (0, 0))
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
    
    def open_level_select():
        nonlocal running
        level_select_menu(WIDTH, HEIGHT, screen)
        # After selecting a level, start the game
        start_game()
        running = False
    
    levels_button = Button(
        images=(pygame.image.load('assets/start_button.png').convert_alpha(),
                pygame.image.load('assets/start_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2),
        text="Levels",
        font=pygame.font.Font(None, 50),
        on_activate=open_level_select
    )
    
    def quit_game():
        nonlocal running
        running = False
        pygame.quit()
        exit()
    
    quit_button = Button(
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 200),
        text="Quit",
        font=pygame.font.Font(None, 50),
        on_activate=quit_game
    )
    main_menu = baseMenu ([levels_button, quit_button], pygame.image.load('assets/title.png').convert_alpha(), pygame.image.load('assets/arrow_pointer.png').convert_alpha()) 
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
        images=(pygame.image.load('assets/level_1_button.png').convert_alpha(),
                pygame.image.load('assets/level_1_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 - 50),
        text="Level 1",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(1)
    )
    
    level2_button = Button( 
        images=(pygame.image.load('assets/level_2_button.png').convert_alpha(),
                pygame.image.load('assets/level_2_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 50),
        text="Level 2",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(2)
    )
    
    back_button = Button(
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
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
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
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


def pause_menu(WIDTH, HEIGHT, screen, game_surface):
    """
    Pause menu that overlays the game screen.
    Returns: 'resume', 'restart', or 'main_menu'
    """
    running = True
    action = 'resume'
    
    def resume_game():
        nonlocal running, action
        action = 'resume'
        running = False
    
    def restart_level():
        nonlocal running, action
        action = 'restart'
        running = False
    
    def return_to_main():
        nonlocal running, action
        action = 'main_menu'
        running = False
    
    resume_button = Button(
        images=(pygame.image.load('assets/start_button.png').convert_alpha(),
                pygame.image.load('assets/start_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 - 50),
        text="Resume",
        font=pygame.font.Font(None, 50),
        on_activate=resume_game
    )
    
    restart_button = Button(
        images=(pygame.image.load('assets/retry_button.png').convert_alpha(),
                pygame.image.load('assets/retry_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 50),
        text="Restart",
        font=pygame.font.Font(None, 50),
        on_activate=restart_level
    )
    
    main_menu_button = Button(
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 150),
        text="Main Menu",
        font=pygame.font.Font(None, 50),
        on_activate=return_to_main
    )
    
    # Create a semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    
    pause_menu_obj = baseMenu([resume_button, restart_button, main_menu_button],
                              pygame.image.load('assets/title.png').convert_alpha(),
                              pygame.image.load('assets/arrow.png').convert_alpha())
    
    while running:
        # Draw the frozen game state
        screen.blit(game_surface, (0, 0))
        # Draw semi-transparent overlay
        screen.blit(overlay, (0, 0))
        
        # Draw pause menu on top
        pause_menu_obj.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                action = 'quit'
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pause_menu_obj.move_selection(-1)
                if event.key == pygame.K_DOWN:
                    pause_menu_obj.move_selection(1)
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    pause_menu_obj.buttons[pause_menu_obj.selected_index].activate()
                # Allow ESC or P to resume
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    action = 'resume'
                    running = False
        
        pygame.display.flip()
    
    return action


class DialogueScreen:

    def __init__(self, text, font_size, screen_rect, speed, location, text_color=(255, 255, 255)):

        # --- Main Text Customization ---
        self.text_to_display = text
        self.font = pygame.font.Font("assets/yoster.ttf", font_size)
        self.text_color = text_color
        

        text_height = self.font.size(text)[1] 
        if location == "top":
            y_pos = screen_rect.top + 50
        elif location == "bottom":
            y_pos = screen_rect.bottom - text_height - 50
        else: # Default to "center"
            y_pos = screen_rect.centery - (text_height // 2)
        self.position = (screen_rect.left + 50, y_pos) 

        # --- Typing Logic ---
        self.typing_delay = speed
        self.typing_timer = 0
        self.current_text = ""
        self.text_index = 0
        self.is_finished = False

        # --- Continue Prompt Logic ---
        self.prompt_text = "Press any key to continue..."
        self.prompt_font = self.font
        self.prompt_alpha = 0  # Start fully transparent
        self.prompt_fade_speed = 5 # How quickly the prompt fades in
        prompt_pos_x = screen_rect.centerx
        prompt_pos_y = screen_rect.bottom - 50

        self.prompt_surf = self.prompt_font.render(self.prompt_text, True, self.text_color)
        self.prompt_rect = self.prompt_surf.get_rect(center=(prompt_pos_x, prompt_pos_y))


    def update(self):
        if self.is_finished:
            # If main text is done, fade in the continue prompt
            if self.prompt_alpha < 255:
                self.prompt_alpha = min(255, self.prompt_alpha + self.prompt_fade_speed)
            return

        self.typing_timer += 1
        if self.typing_timer >= self.typing_delay:
            self.typing_timer = 0
            if self.text_index < len(self.text_to_display):
                self.current_text += self.text_to_display[self.text_index]
                self.text_index += 1
            else:
                self.is_finished = True

    def draw(self, surface):
        surface.fill((0, 0, 0))
        
        # Draw the main text
        rendered_text = self.font.render(self.current_text, True, self.text_color)
        surface.blit(rendered_text, self.position)
        
        # If finished, draw the continue prompt with its current alpha
        if self.is_finished:
            self.prompt_surf.set_alpha(self.prompt_alpha)
            surface.blit(self.prompt_surf, self.prompt_rect)

    def skip(self):
        self.current_text = self.text_to_display
        self.text_index = len(self.text_to_display)
        self.is_finished = True



def run_game_intro(WIDTH, HEIGHT, screen):

    intro_dialogue = DialogueScreen(
        text="Red Hood! Search for the Shroomlight!",
        font_size=20,
        screen_rect=screen.get_rect(),
        speed=200, 
        location="center"
    )

    intro_running = True
    while intro_running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit() # Exit the program entirely if window is closed
            
            if event.type == pygame.KEYDOWN:
                if not intro_dialogue.is_finished:
                    # If typing, skip to the end
                    intro_dialogue.skip()
                else:
                    # If finished, any key press will exit the intro
                    intro_running = False

        intro_dialogue.update()

        intro_dialogue.draw(screen)
        
        pygame.display.flip()


def run_BossIntro(WIDTH, HEIGHT, screen):

    intro_dialogue = DialogueScreen(
        text="BOSS BATTLE! GET READY TO FIGHT THE BIG BAD SMTH SMTH!",
        font_size=20,
        screen_rect=screen.get_rect(),
        speed=200, 
        location="center"
    )

    intro_running = True
    while intro_running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit() # Exit the program entirely if window is closed
            
            if event.type == pygame.KEYDOWN:
                if not intro_dialogue.is_finished:
                    # If typing, skip to the end
                    intro_dialogue.skip()
                else:
                    # If finished, any key press will exit the intro
                    intro_running = False

        intro_dialogue.update()

        intro_dialogue.draw(screen)
        
        pygame.display.flip()

def getLevel():
    global game_level
    return game_level