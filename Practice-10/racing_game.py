import pygame
import sys
import random
import time


# 1. Инициализация и всякая база
pygame.init()

# размеры экрана
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

# цвета (RGB, ну стандарт)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GOLD = (255, 215, 0)      # цвет монетки (если просто рисовать кругляш)

# игровые переменные
SPEED = 5                 # скорость   врагов (потом будет расти)
SCORE = 0                 # очки за уклонение
COINS_COLLECTED = 0       #  сколько монет собрал

# FPS чтобы не лагало
FPS = 60
FramePerSec = pygame.time.Clock()

# создаем окно
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racer Game - Collect Coins!")

# грузим картинки
try:
    background = pygame.image.load("AnimatedStreet.png")
    player_img = pygame.image.load("Player.png")
    enemy_img = pygame.image.load("Enemy.png")
    coin_img = pygame.image.load("Coin.png")  
except:
    # если вдруг файлов нету, делаем просто квадраты (выглядит кринж конечно)
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((50, 50, 50))
    player_img = pygame.Surface((40, 60))
    player_img.fill((0, 255, 0))
    enemy_img = pygame.Surface((40, 60))
    enemy_img.fill((255, 0, 0))
    coin_img = pygame.Surface((20, 20))
    coin_img.fill(GOLD)
    print("Типо фолбэк, добавь норм картинки потом")

# шрифты для текста
font_small = pygame.font.SysFont("Verdana", 20)
font_large = pygame.font.SysFont("Verdana", 60)
game_over_text = font_large.render("Game Over", True, BLACK)


# Классы спрайтов: игрок, враг и монета (новая тема)

class Player(pygame.sprite.Sprite):
    """машинка игрока, двигается влево/вправо"""
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.center = (160, SCREEN_HEIGHT - 80)   # почти внизу

    def move(self):
        """движение стрелками, чтоб не вылазил за экран"""
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.move_ip(-5, 0)
        if pressed[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.move_ip(5, 0)

class Enemy(pygame.sprite.Sprite):
    """враг тупо падает сверху"""
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        # случайная позиция по X
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        """двигается вниз, если ушел вниз — +очко и заново"""
        global SCORE
        self.rect.move_ip(0, SPEED)
        if self.rect.top > SCREEN_HEIGHT:
            SCORE += 1
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

class Coin(pygame.sprite.Sprite):
    """монетка, падает, собираешь — кайф"""
    def __init__(self):
        super().__init__()
        self.image = coin_img
        self.rect = self.image.get_rect()
        # случайно сверху появляется
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), -20)
        self.value = 1   # одна монета = 1

    def move(self):
        """движение вниз, медленнее чем враги"""
        self.rect.move_ip(0, SPEED - 2)   # чуть медленее падает
        # если не подобрал и улетела — удаляем
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# 3. создаем обьекты и группы

player = Player()
enemy = Enemy()
# пока один враг, потом можно больше сделать

# группы для коллизий и рендера
enemies = pygame.sprite.Group()
enemies.add(enemy)

coins_group = pygame.sprite.Group()   # тут все монеты

all_sprites = pygame.sprite.Group()
all_sprites.add(player)
all_sprites.add(enemy)

# 4. таймеры: скорость и спавн монет
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)   # каждую секунду быстрее

SPAWN_COIN = pygame.USEREVENT + 2
pygame.time.set_timer(SPAWN_COIN, 1500)   # монета каждые 1.5 сек

# 5. ГЕЙМ ЛУП
while True:
    #  обработка событий
    for event in pygame.event.get():
        if event.type == INC_SPEED:
            SPEED += 0.5                 # усложняем игру
        if event.type == SPAWN_COIN:
            # создаем новую монету
            new_coin = Coin()
            coins_group.add(new_coin)
            all_sprites.add(new_coin)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    #сначала фон 
    DISPLAYSURF.blit(background, (0, 0))

    #  очки слева, монеты справа
    score_surface = font_small.render(f"Score: {SCORE}", True, BLACK)
    DISPLAYSURF.blit(score_surface, (10, 10))

    # монеты справа сверху
    coins_surface = font_small.render(f"Coins: {COINS_COLLECTED}", True, BLACK)
    coins_rect = coins_surface.get_rect(topright=(SCREEN_WIDTH - 10, 10))
    DISPLAYSURF.blit(coins_surface, coins_rect)

    #  двигаем и рисуем все 
    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)
        entity.move()

    # проверка сбора монет 
    collected_coins = pygame.sprite.spritecollide(player, coins_group, True)
    for coin in collected_coins:
        COINS_COLLECTED += coin.value
        # можно звук добавить если не лень
        # pygame.mixer.Sound('coin.wav').play()

    #  столкновение с врагом 
    if pygame.sprite.spritecollideany(player, enemies):
        # звук краша (если есть файл)
        try:
            pygame.mixer.Sound('crash.wav').play()
        except:
            pass
        time.sleep(0.5)

        # экран проигрыша
        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over_text, (30, 250))
        pygame.display.update()
        time.sleep(2)

        pygame.quit()
        sys.exit()

    # обновление экрана 
    pygame.display.update()
    FramePerSec.tick(FPS)