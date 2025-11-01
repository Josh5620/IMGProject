import pygame
import math
import random

game_level = 2

# ============ MUSIC MANAGER ============
class MusicManager:
    """Manages background music for different game states"""
    
    def __init__(self):
        self.current_track = None
        self.music_volume = 0.5  # 50% volume (adjust as needed)
        self.initialized = False
        
        # Load music files
        self.tracks = {
            'menu': 'assets/Music/IntroBackgroundMusic.mp3',
            'level1': 'assets/Music/ForestLevelBackgroundMusic.mp3',
            'level2': 'assets/Music/DungeonLevelBackgroundMusic.mp3',
            'boss': 'assets/Music/BossLevelBackgroundMusic.mp3'
        }
    
    def play(self, track_name):
        """Play a music track (loops infinitely)"""
        # Initialize mixer on first use (after pygame.init() has been called)
        if not self.initialized:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                self.initialized = True
            except pygame.error:
                print("⚠️ Pygame mixer not initialized yet")
                return
        
        if track_name == self.current_track:
            return  # Already playing this track
        
        if track_name in self.tracks:
            try:
                pygame.mixer.music.load(self.tracks[track_name])
                pygame.mixer.music.play(-1)  # -1 means loop forever
                self.current_track = track_name
                print(f"🎵 Playing {track_name} music")
            except pygame.error as e:
                print(f"⚠️ Could not load music {track_name}: {e}")
        else:
            print(f"⚠️ Track {track_name} not found")
    
    def stop(self):
        """Stop the current music"""
        pygame.mixer.music.stop()
        self.current_track = None
    
    def pause(self):
        """Pause the current music"""
        pygame.mixer.music.pause()
    
    def unpause(self):
        """Resume paused music"""
        pygame.mixer.music.unpause()
    
    def set_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

# Create a global music manager instance
music_manager = MusicManager()
class baseMenu():
    def __init__(self,  buttons, title_img, selected_img):
        self.title_image = title_img
        self.selected_img = selected_img
        self.buttons = buttons
        self.selected_index = 0
        self.font = pygame.font.Font(None, 50)
        self.background = pygame.image.load('assets/menuBack.jpeg').convert()
        self.background = pygame.transform.scale(self.background, (960, 640))
        # Ambient particles for menu
        self.menu_particles = []
        for _ in range(20):
            self.menu_particles.append({
                'x': random.randint(0, 960),
                'y': random.randint(0, 640),
                'dx': random.uniform(-0.5, 0.5),
                'dy': random.uniform(-0.5, 0.5),
                'life': random.randint(200, 400),
                'max_life': random.randint(200, 400),
                'size': random.randint(2, 5)
            })
    
    def move_selection(self, direction):
        self.selected_index = (self.selected_index + direction) % len(self.buttons)
        print(self.selected_index)

    def draw(self, screen):
        screen.fill((0, 0, 0))  # Clear screen with black
        screen.blit(self.background, (0, 0))
        
        # Update and draw ambient particles
        for particle in self.menu_particles:
            SPEED = 0.5
            particle['x'] += particle['dx'] * SPEED
            particle['y'] += particle['dy'] * SPEED
            particle['life'] -= 1
            if particle['life'] <= 0:
                particle['x'] = random.randint(0, 960)
                particle['y'] = random.randint(0, 640)
                particle['life'] = random.randint(200, 400)
            
            # Wrap particles
            if particle['x'] < 0:
                particle['x'] = 960
            elif particle['x'] > 960:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = 640
            elif particle['y'] > 640:
                particle['y'] = 0
            
            # Draw sparkle
            alpha = min(255, particle['life'] * 2)
            pygame.draw.circle(screen, (255, 255, 200), (int(particle['x']), int(particle['y'])), particle['size'])
        
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
    music_manager.play('menu')  # Play menu music
    running = True
    
    def open_level_select():
        nonlocal running
        level_selected = level_select_menu(WIDTH, HEIGHT, screen)
        # Only start the game if a level was actually selected (not if they pressed Back)
        if level_selected:
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
    
    def show_manual():
        nonlocal running
        run_game_manual(WIDTH, HEIGHT, screen)
    
    manual_button = Button(
        images=(pygame.image.load('assets/howtoplay_button.png').convert_alpha(),
                pygame.image.load('assets/howtoplay_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Manual",
        font=pygame.font.Font(None, 50),
        on_activate=show_manual
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
    main_menu = baseMenu ([levels_button, manual_button, quit_button], pygame.image.load('assets/title.png').convert_alpha(), pygame.image.load('assets/arrow_pointer.png').convert_alpha()) 
    while running:
        
        
        main_menu.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # Exit the program when window X is clicked
        
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

        pygame.display.flip()

def set_level(level_num):
    global game_level
    game_level = level_num
    print(f"Level selected is {level_num}")
    

def level_select_menu(WIDTH, HEIGHT, screen):
    running = True
    level_selected = False  # Track if a level was selected
    
    def select_level_and_exit(level_num):
        nonlocal running, level_selected
        set_level(level_num)
        level_selected = True
        running = False
    
    def go_back():
        nonlocal running, level_selected
        level_selected = False
        running = False
    
    level1_button = Button(
        images=(pygame.image.load('assets/level_1_button.png').convert_alpha(),
                pygame.image.load('assets/level_1_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 0),
        text="Level 1",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(1)
    )
    
    level2_button = Button( 
        images=(pygame.image.load('assets/level_2_button.png').convert_alpha(),
                pygame.image.load('assets/level_2_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Level 2",
        font=pygame.font.Font(None, 50),
        on_activate=lambda: select_level_and_exit(2)
    )
    
    back_button = Button(
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 200),
        text="Back",
        font=pygame.font.Font(None, 50),
        on_activate=go_back
    )
    
    level_menu = baseMenu([level1_button, level2_button, back_button],
                        pygame.image.load('assets/leveltitle.png').convert_alpha(),
                        pygame.image.load('assets/arrow_pointer.png').convert_alpha())
    
    while running:
        level_menu.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # Exit the program when window X is clicked
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    level_menu.move_selection(-1)
                if event.key == pygame.K_DOWN:
                    level_menu.move_selection(1)
                if event.key == pygame.K_SPACE:
                    level_menu.buttons[level_menu.selected_index].activate()
                    running = False
        
        pygame.display.flip()
    
    return level_selected  # Return True if level was selected, False if Back was pressed
        

def retry_menu(WIDTH, HEIGHT, screen, retry_function, quit_function):
    running = True
    
    retry_button = Button(
        images=(pygame.image.load('assets/retry_button.png').convert_alpha(),
                pygame.image.load('assets/retry_button_highlighted.png').convert_alpha()),
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
                            pygame.image.load('assets/arrow_pointer.png').convert_alpha())
    
    while running:
        retry_menu_obj.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # Exit the program when window X is clicked
        
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
    music_manager.pause()  # Pause music when menu opens
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
    
    def show_controls():
        # Show controls screen, then return to pause menu
        run_level2_tutorial(WIDTH, HEIGHT, screen)
    
    def return_to_main():
        nonlocal running, action
        action = 'main_menu'
        running = False
    
    resume_button = Button(
        images=(pygame.image.load('assets/resume_button.png').convert_alpha(),
                pygame.image.load('assets/resume_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2),
        text="Resume",
        font=pygame.font.Font(None, 50),
        on_activate=resume_game
    )
    
    
    restart_button = Button(
        images=(pygame.image.load('assets/retry_button.png').convert_alpha(),
                pygame.image.load('assets/retry_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 100),
        text="Restart",
        font=pygame.font.Font(None, 50),
        on_activate=restart_level
    )
    
    main_menu_button = Button(
        images=(pygame.image.load('assets/quit_button.png').convert_alpha(),
                pygame.image.load('assets/quit_button_highlighted.png').convert_alpha()),
        pos=(WIDTH // 2, HEIGHT // 2 + 200),
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
                            pygame.image.load('assets/arrow_pointer.png').convert_alpha())
    
    while running:
        # Draw the frozen game state
        screen.blit(game_surface, (0, 0))
        # Draw semi-transparent overlay
        screen.blit(overlay, (0, 0))
        
        # Draw pause menu on top
        pause_menu_obj.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # Exit the program when window X is clicked
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pause_menu_obj.move_selection(-1)
                if event.key == pygame.K_DOWN:
                    pause_menu_obj.move_selection(1)
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    pause_menu_obj.buttons[pause_menu_obj.selected_index].activate()
                # Allow ESC to resume
                if event.key == pygame.K_ESCAPE:
                    action = 'resume'
                    running = False
        
        pygame.display.flip()
    
    # Resume music if player continues playing
    if action == 'resume':
        music_manager.unpause()
    elif action == 'main_menu':
        music_manager.play('menu')  # Return to menu music
    
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


def run_BossIntro(WIDTH, HEIGHT, screen, difficulty="normal"):
    """Show boss battle intro with difficulty-specific message"""
    
    # Difficulty-specific messages
    if difficulty == "easy":
        intro_text = "Through the forest's light path, you face a gentler trial..."
    elif difficulty == "hard":
        intro_text = "The dark path awaits! Prepare for the ultimate challenge!"
    else:
        intro_text = "The final confrontation approaches..."
    
    intro_dialogue = DialogueScreen(
        text=intro_text,
        font_size=24,
        screen_rect=screen.get_rect(),
        speed=150,
        location="center"
    )

    intro_running = True
    while intro_running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.KEYDOWN:
                if not intro_dialogue.is_finished:
                    intro_dialogue.skip()
                else:
                    intro_running = False

        intro_dialogue.update()
        intro_dialogue.draw(screen)
        
        pygame.display.flip()

def run_game_manual(WIDTH, HEIGHT, screen):
    """Interactive game manual/guide with multiple pages"""
    
    # Wait for all keys to be released first
    pygame.event.clear()
    waiting_for_release = True
    while waiting_for_release:
        keys = pygame.key.get_pressed()
        if not any(keys):
            waiting_for_release = False
        pygame.time.wait(50)
        pygame.event.pump()
    
    running = True
    current_page = 0
    
    font_title = pygame.font.Font("assets/yoster.ttf", 48)
    font_section = pygame.font.Font("assets/yoster.ttf", 28)
    font_normal = pygame.font.Font("assets/yoster.ttf", 22)
    font_small = pygame.font.Font("assets/yoster.ttf", 18)  # Same pixelated font
    
    # Define manual pages
    pages = [
        {
            "title": "WELCOME TO SHROOMLIGHT",
            "content": [
                "In this game, you play as Little Red Riding Hood",
                "on her journey through dangerous lands.",
                "",
                "Collect powerups to strengthen yourself and",
                "defeat enemies to progress through levels.",
                "",
                "Your goal: Survive and defeat the final boss!",
                "",
                "Use arrow keys to navigate through this manual."
            ]
        },
        {
            "title": "MOVEMENT BASICS",
            "content": [
                "Left AND Right Arrow  -  Move left and right",
                "",
                "Up Arrow  -  Jump",
                "",
                "Up Arrow Twice  -  Double Jump",
                "",
                "The double jump can help you reach",
                "higher platforms and avoid traps!",
                "",
                "TIP: Timing is everything for platforming!"
            ]
        },
        {
            "title": "COMBAT SYSTEM",
            "content": [
                "A  -  Melee Attack",
                "S  -  Shoot Arrow (uses ammo)",
                "Hold C  -  Charge Shot (more damage)",
                "",
                "Shift  -  Dash -> Dungeon Level 2 only!",
                "",
                "Charged shots do more damage but",
                "take time to charge up.",
                "",
                "TIP: Dash to dodge enemy attacks!"
            ]
        },
        {
            "title": "POWERUP MUSHROOMS",
            "content": [
                "Health Burst  -  Restores health",
                "Fire Cloak  -  Fire resistance",
                "Speed Wind  -  Increases movement speed",
                "Wolf Strength  -  Boosts attack damage",
                "Grandma Amulet  -  Temporary invincibility",
                "Forest Wisdom  -  Special abilities",
                "",
                "Collect these strategically to help you!",
                "",
                "TIP: Don't waste health items!"
            ]
        },
        {
            "title": "LEVEL 2 REQUIREMENTS",
            "content": [
                "In Level 2 Dungeon Level, you must collect",
                "at least 10 mushrooms before you can",
                "fight the boss!",
                "",
                "Watch the mushroom counter in the top",
                "right corner to track your progress.",
                "",
                "Collect more mushrooms to unlock the",
                "boss fight and proceed!",
                "",
                "TIP: Explore thoroughly for hidden items!"
            ]
        },
        {
            "title": "COMBAT TIPS",
            "content": [
                "1. Attack enemies from above when possible",
                "2. Keep moving to avoid enemy attacks",
                "3. Use ranged attacks for flying enemies",
                "4. Don't rush in to attack, observe enemy patterns",
                "5. Save dash for critical moments",
                "6. Charge shot for heavy enemies",
                "",
                "Learn enemy attack patterns!",
                "",
                "TIP: Practice makes perfect!"
            ]
        },
        {
            "title": "SURVIVAL GUIDE",
            "content": [
                "You have 3 hearts as lives, use them wisely!",
                "",
                "If you die, you can retry from the start.",
                "",
                "Take breaks if you're getting frustrated,",
                "and come back with fresh focus!",
                "",
                "Explore every corner! There might be",
                "secret powerups or helpful items!",
                "",
                "TIP: Sometimes retreating is smart!"
            ]
        },
        {
            "title": "READY TO PLAY?",
            "content": [
                "You now know the basics!",
                "",
                "Remember:",
                "1 - Practice the controls",
                "2 - Collect powerups",
                "3 - Learn enemy patterns",
                "4 - Have fun!",
                "",
                "Good luck on your adventure!"
            ]
        }
    ]
    
    # Animation
    fade_alpha = 0
    max_alpha = 255
    fade_speed = 5
    pulse_timer = 0
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    # Previous page
                    if current_page > 0:
                        current_page -= 1
                        fade_alpha = 0  # Reset fade for page transition
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    # Next page
                    if current_page < len(pages) - 1:
                        current_page += 1
                        fade_alpha = 0  # Reset fade for page transition
                elif event.key == pygame.K_SPACE:
                    # Return to menu
                    running = False
        
        # Fade in
        if fade_alpha < max_alpha:
            fade_alpha = min(max_alpha, fade_alpha + fade_speed)
        
        pulse_timer += 0.1
        pulse_brightness = int(50 + abs(math.sin(pulse_timer) * 50))
        
        # Draw
        screen.fill((20, 20, 30))  # Dark blue-gray background
        
        # Get current page
        page = pages[current_page]
        
        # Title
        title_surf = font_title.render(page["title"], True, (255, 220, 120))
        title_surf.set_alpha(fade_alpha)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)
        
        # Draw decorative line under title
        pygame.draw.line(screen, (255, 200, 100), 
                        (WIDTH // 2 - 250, 82), 
                        (WIDTH // 2 + 250, 82), 3)
        
        # Content with color coding - better centered with more width
        y_offset = 120
        for line in page["content"]:
            if line == "":
                y_offset += 35  # Same spacing as regular lines for consistency
                continue
            
            # Determine text color based on content
            if "TIP:" in line:
                text_color = (255, 255, 100)  # Yellow for tips
            elif " - " in line or ":" in line:
                text_color = (200, 255, 200)  # Light green for key bindings
            elif line[0].isdigit() and "." in line:
                text_color = (150, 200, 255)  # Light blue for numbered lists
            else:
                text_color = (230, 230, 230)  # White for normal text
            
            text_surf = font_normal.render(line, True, text_color)
            text_surf.set_alpha(fade_alpha)
            # Center each line properly
            screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y_offset))
            y_offset += 35
        
        # Page indicator with same white color as body text
        page_text = f"Page {current_page + 1} / {len(pages)}"
        page_surf = font_small.render(page_text, True, (220, 220, 220))
        page_rect = page_surf.get_rect(center=(WIDTH // 2, HEIGHT - 120))
        screen.blit(page_surf, page_rect)
        
        # Navigation hints - single centered line with same white color
        nav_y = HEIGHT - 80
        nav_color = (220, 220, 220)  # White, same as body text
        
        # Build navigation text with more spacing
        if current_page < len(pages) - 1:
            nav_text = "<  Previous        |        Next  >"
        else:
            nav_text = "<  Previous"
        
        nav_surf = font_small.render(nav_text, True, nav_color)
        nav_rect = nav_surf.get_rect(center=(WIDTH // 2, nav_y))
        screen.blit(nav_surf, nav_rect)
        
        # SPACE hint below with same white color and more spacing
        space_text = "- Press SPACE to Return to Main Menu -"
        space_surf = font_small.render(space_text, True, nav_color)
        space_rect = space_surf.get_rect(center=(WIDTH // 2, nav_y + 40))
        screen.blit(space_surf, space_rect)
        
        pygame.display.flip()


def run_level2_tutorial(WIDTH, HEIGHT, screen):
    """Tutorial screen showing Level 2 controls and mechanics"""
    
    # Wait for all keys to be released first (prevent key carry-over)
    pygame.event.clear()
    waiting_for_release = True
    while waiting_for_release:
        keys = pygame.key.get_pressed()
        if not any(keys):  # All keys released
            waiting_for_release = False
        pygame.time.wait(50)  # Small delay
        pygame.event.pump()
    
    running = True
    font_title = pygame.font.Font("assets/yoster.ttf", 42)
    font_section = pygame.font.Font("assets/yoster.ttf", 24)
    font_normal = pygame.font.Font("assets/yoster.ttf", 20)
    font_prompt = pygame.font.Font("assets/yoster.ttf", 22)
    
    # Tutorial content - organized by sections
    title = "GAME CONTROLS"
    
    # Animation
    fade_alpha = 0
    max_alpha = 255
    fade_speed = 5
    pulse_timer = 0
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = False
        
        # Fade in
        if fade_alpha < max_alpha:
            fade_alpha = min(max_alpha, fade_alpha + fade_speed)
        
        pulse_timer += 0.1
        pulse_brightness = int(50 + abs(math.sin(pulse_timer) * 50))
        
        # Draw
        screen.fill((20, 20, 30))  # Dark blue-gray background
        
        # Title with glow effect
        title_surf = font_title.render(title, True, (255, 220, 120))
        title_surf.set_alpha(fade_alpha)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)
        
        # Draw decorative line under title
        pygame.draw.line(screen, (255, 200, 100), 
                        (WIDTH // 2 - 250, 82), 
                        (WIDTH // 2 + 250, 82), 3)
        
        y_offset = 110
        
        # === MOVEMENT SECTION ===
        section_surf = font_section.render("MOVEMENT:", True, (120, 220, 255))
        section_surf.set_alpha(fade_alpha)
        screen.blit(section_surf, (WIDTH // 2 - 230, y_offset))
        y_offset += 33
        
        movement_controls = [
            "Left Right Arrow  -  Move left and right",
            "Up Arrow  -  Jump",
            "Up Arrow twice  -  Double Jump"
        ]
        for control in movement_controls:
            text_surf = font_normal.render(control, True, (230, 230, 230))
            text_surf.set_alpha(fade_alpha)
            screen.blit(text_surf, (WIDTH // 2 - 200, y_offset))
            y_offset += 28
        
        y_offset += 15
        
        # === COMBAT SECTION ===
        section_surf = font_section.render("COMBAT:", True, (255, 150, 150))
        section_surf.set_alpha(fade_alpha)
        screen.blit(section_surf, (WIDTH // 2 - 230, y_offset))
        y_offset += 33
        
        combat_controls = [
            "A  -  Melee or Close Attack",
            "S  -  Shoot Arrow",
            "Shift  -  Dash -> For Dungeon Level Only - Level 2",
            "Hold C  -  Charge Shot"
        ]
        for control in combat_controls:
            text_surf = font_normal.render(control, True, (230, 230, 230))
            text_surf.set_alpha(fade_alpha)
            screen.blit(text_surf, (WIDTH // 2 - 200, y_offset))
            y_offset += 28
        
        y_offset += 15
        
        # === POWERUPS SECTION ===
        section_surf = font_section.render("POWERUPS - Mushrooms:", True, (150, 255, 180))
        section_surf.set_alpha(fade_alpha)
        screen.blit(section_surf, (WIDTH // 2 - 230, y_offset))
        y_offset += 33
        
        powerups = [
            "Health Burst  -  Restore health",
            "Fire Cloak  -  Fire protection",
            "Speed Wind  -  Increased speed",
            "Wolf Strength  -  More damage",
            "Grandma Amulet  -  Protection",
            "Forest Wisdom  -  Special ability"
        ]
        for powerup in powerups:
            text_surf = font_normal.render(powerup, True, (230, 230, 230))
            text_surf.set_alpha(fade_alpha)
            screen.blit(text_surf, (WIDTH // 2 - 200, y_offset))
            y_offset += 26
        
        # === PROMPT TO START ===
        y_offset += 25
        # Pulsing "Press SPACE" prompt (clamp values to 255)
        prompt_color = (min(255, pulse_brightness + 150), 
                    min(255, pulse_brightness + 200), 
                    min(255, pulse_brightness + 100))
        prompt_surf = font_prompt.render("Press SPACE to begin!", True, prompt_color)
        prompt_surf.set_alpha(fade_alpha)
        prompt_rect = prompt_surf.get_rect(center=(WIDTH // 2, y_offset))
        screen.blit(prompt_surf, prompt_rect)
        
        pygame.display.flip()


def getLevel():
    global game_level
    return game_level