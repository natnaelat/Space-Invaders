import pygame
import os
import random

pygame.font.init()

# Pygame window dimensions
WIDTH, HEIGHT = 600, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invader")

# Load images
RED_ENEMY_IMG = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
BLUE_ENEMY_IMG = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))
GREEN_ENEMY_IMG = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
YELLOW_PLAYER_IMG = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

RED_LASER_IMG = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
BLUE_LASER_IMG = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
GREEN_LASER_IMG = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
YELLOW_LASER_IMG = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# Scale background image to fit window
BACKGROUND = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT)
)


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    # Move up for player, down for enemy
    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (height >= self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    # Half-second cooldown between laser shots
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cooldown_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        # Draw lasers if any
        for laser in self.lasers:
            laser.draw(window)

    # Move lasers and handle collisions
    def move_laser(self, vel, player_obj):
        # Wait for cooldown period
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            # Remove laser if off-screen or hits the player
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(player_obj):
                player_obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def shoot(self):
        if self.cooldown_counter == 0:
            # Add laser when player shoots
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            # Start cooldown counter
            self.cooldown_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class PlayerShip(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_PLAYER_IMG
        self.laser_img = YELLOW_LASER_IMG
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    # Move player lasers and handle collisions with enemies
    def move_laser(self, vel, enemy_ships):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for enemy_ship in enemy_ships:
                    # Check for collision with all enemies
                    if laser.collision(enemy_ship):
                        enemy_ships.remove(enemy_ship)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    # Draw health bar for player
    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        # Draw static red rectangle
        pygame.draw.rect(
            window,
            (255, 0, 0),
            (
                self.x,
                (self.y + self.ship_img.get_height() + 10),
                self.ship_img.get_width(),
                10,
            ),
        )
        # Draw dynamic green rectangle representing health
        pygame.draw.rect(
            window,
            (0, 255, 0),
            (
                self.x,
                (self.y + self.ship_img.get_height() + 10),
                self.ship_img.get_width() * (self.health / self.max_health),
                10,
            ),
        )


class EnemyShip(Ship):
    COLOR_MAP = {
        "red": (RED_ENEMY_IMG, RED_LASER_IMG),
        "blue": (BLUE_ENEMY_IMG, BLUE_LASER_IMG),
        "green": (GREEN_ENEMY_IMG, GREEN_LASER_IMG),
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        # Create enemy based on color
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    # Offset lasers' x position
    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x - 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1

    def move(self, vel):
        self.y += vel


# Check if two objects collide based on their masks
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def get_random_enemy_color():
    return random.choice(["red", "blue", "green"])


def main_game():
    # Game variables
    run = True
    FPS = 60

    level = 0
    lives = 5

    enemy_ships = []
    wave_length = 5

    # Velocities
    enemy_vel = 1
    player_vel = 3
    laser_vel = 4

    lost = False
    lost_count = 0

    clock = pygame.time.Clock()

    # Fonts
    main_font = pygame.font.SysFont("Nunito", 30)
    lost_font = pygame.font.SysFont("Nunito", 50)

    player_ship = PlayerShip(WIDTH // 2 - 25, 450)

    def redraw_game_window():
        # Draw background, level, and lives
        WIN.blit(BACKGROUND, (0, 0))
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        # Draw enemies and player
        for enemy_ship in enemy_ships:
            enemy_ship.draw(WIN)

        player_ship.draw(WIN)

        # Draw game over screen if lost
        if lost:
            lost_label = lost_font.render("Game Over", 1, (255, 255, 255))
            WIN.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, 280))

        pygame.display.update()

    # Main game loop
    while run:
        clock.tick(FPS)  # Control frame rate
        redraw_game_window()

        # Check for game over condition
        if lives <= 0 or player_ship.health <= 0:
            lost = True
            lost_count += 1

        # Show game over screen for 3 seconds
        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        # Increase the level after each wave
        if len(enemy_ships) == 0:
            level += 1
            wave_length += 2
            for i in range(wave_length):
                # Initialize random enemy at random position
                enemy_ship = EnemyShip(
                    random.randrange(50, WIDTH - 100),
                    random.randrange(-1200, -100),
                    get_random_enemy_color(),
                )
                enemy_ships.append(enemy_ship)

        # Quit the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # Handle player movements and shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player_ship.x - player_vel > 0:
            player_ship.x -= player_vel
        if keys[pygame.K_d] and player_ship.x + player_vel + player_ship.get_width() < WIDTH:
            player_ship.x += player_vel
        if keys[pygame.K_w] and player_ship.y - player_vel > 0:
            player_ship.y -= player_vel
        if keys[pygame.K_s] and player_ship.y + player_vel + player_ship.get_height() + 15 < HEIGHT:
            player_ship.y += player_vel
        if keys[pygame.K_SPACE]:
            player_ship.shoot()

        for enemy_ship in enemy_ships[:]:
            # Move each enemy and their laser
            enemy_ship.move(enemy_vel)
            enemy_ship.move_laser(laser_vel, player_ship)
            # Enemy shoots at random interval
            if random.randrange(0, 10 * FPS) == 1:
                enemy_ship.shoot()

            # Remove enemy if off screen or collided with player
            if collide(enemy_ship, player_ship):
                player_ship.health -= 20
                enemy_ships.remove(enemy_ship)
            elif enemy_ship.y + enemy_ship.get_height() > HEIGHT:
                lives -= 1
                enemy_ships.remove(enemy_ship)

        # Move player laser with negative velocity
        player_ship.move_laser(-laser_vel, enemy_ships)


def main_menu():
    instr_font = pygame.font.SysFont("Nunito", 50)
    run = True

    while run:
        # Draw main menu
        WIN.blit(BACKGROUND, (0, 0))
        instr_label = instr_font.render("Press Enter to Begin", 1, (255, 255, 255))
        WIN.blit(
            instr_label, (WIDTH / 2 - instr_label.get_width() / 2, HEIGHT / 2 - 30)
        )
        pygame.display.update()

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                main_game()

    pygame.quit()


main_menu()
