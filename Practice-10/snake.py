import pygame
import random
import sys

# инициализация, просто запускаем все это дело
pygame.init()

# размеры и константы игры
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20          # размер клетки (змейки и еды)
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE   # 30 клеток
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE # тоже 30

# цвета РГБ
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

# игровые переменные
INITIAL_SPEED = 10      # начальная скорость (fps)
current_speed = INITIAL_SPEED
score = 0
level = 1
foods_eaten_for_level = 0
FOODS_NEEDED_FOR_LEVEL = 3  # сколько еды надо чтоб левел ап

# создаем окно
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game - Levels & Speed")

# таймер для FPS
clock = pygame.time.Clock()

# шрифты для текста
font_small = pygame.font.SysFont("Arial", 20)
font_medium = pygame.font.SysFont("Arial", 30)
font_large = pygame.font.SysFont("Arial", 50)

# класс змейки (основная логика тут)
class Snake:
    """сама змейка, двигается, растет и умирает если тупишь"""
    
    def __init__(self):
        # стартуем с 3 сегментов по середине
        self.body = [
            [GRID_WIDTH // 2, GRID_HEIGHT // 2],
            [GRID_WIDTH // 2 - 1, GRID_HEIGHT // 2],
            [GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2]
        ]
        self.direction = "RIGHT"    # куда щас движется
        self.grow_flag = False      # флаг чтоб увеличится
        
    def move(self):
        """движение змеи на 1 шаг"""
        new_head = self.body[0].copy()
        
        # считаем новую позицию головы
        if self.direction == "RIGHT":
            new_head[0] += 1
        elif self.direction == "LEFT":
            new_head[0] -= 1
        elif self.direction == "UP":
            new_head[1] -= 1
        elif self.direction == "DOWN":
            new_head[1] += 1
            
        self.body.insert(0, new_head)
        
        # если не растем — убираем хвост
        if not self.grow_flag:
            self.body.pop()
        else:
            self.grow_flag = False
            
    def grow(self):
        """типа помечаем что надо вырости"""
        self.grow_flag = True
        
    def check_self_collision(self):
        """если в себя врезался (ну бывает)"""
        head = self.body[0]
        return head in self.body[1:]
    
    def check_wall_collision(self):
        """проверка стен, если вышел за границы — гг"""
        head = self.body[0]
        if (head[0] < 0 or head[0] >= GRID_WIDTH or
            head[1] < 0 or head[1] >= GRID_HEIGHT):
            return True
        return False
    
    def change_direction(self, new_direction):
        """смена направления (нельзя резко назад иначе баги)"""
        opposite_directions = {
            "RIGHT": "LEFT",
            "LEFT": "RIGHT",
            "UP": "DOWN",
            "DOWN": "UP"
        }
        if opposite_directions[new_direction] != self.direction:
            self.direction = new_direction
            
    def draw(self, screen):
        """рисуем змею"""
        for i, segment in enumerate(self.body):
            if i == 0:
                color = DARK_GREEN  # голова темнее
            else:
                color = GREEN
            rect = pygame.Rect(segment[0] * GRID_SIZE, 
                              segment[1] * GRID_SIZE,
                              GRID_SIZE - 2, GRID_SIZE - 2)
            pygame.draw.rect(screen, color, rect)
            # глаза 
            if i == 0:
                eye_size = 3
                pygame.draw.circle(screen, BLACK, 
                                 (segment[0] * GRID_SIZE + 5, 
                                  segment[1] * GRID_SIZE + 5), eye_size)
                pygame.draw.circle(screen, BLACK,
                                 (segment[0] * GRID_SIZE + 15,
                                  segment[1] * GRID_SIZE + 5), eye_size)

# класс еды
class Food:
    """еда"""
    
    def __init__(self, snake_body=None):
        self.position = [0, 0]
        self.generate_random_position(snake_body)
        
    def generate_random_position(self, snake_body=None):
        """генерация позиции (чтоб не внутри змеи, а то кринж)"""
        if snake_body is None:
            self.position = [
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            ]
        else:
            while True:
                candidate = [
                    random.randint(0, GRID_WIDTH - 1),
                    random.randint(0, GRID_HEIGHT - 1)
                ]
                if candidate not in snake_body:
                    self.position = candidate
                    break
                    
    def draw(self, screen):
        """рисуем еду как кружок"""
        center_x = self.position[0] * GRID_SIZE + GRID_SIZE // 2
        center_y = self.position[1] * GRID_SIZE + GRID_SIZE // 2
        radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(screen, RED, (center_x, center_y), radius)
        pygame.draw.circle(screen, (255, 100, 100), 
                          (center_x - 2, center_y - 2), radius // 3)

# экран проигрыша
def show_game_over(screen, score, level):
    """показывает что ты проиграл (печально)"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    game_over_text = font_large.render("GAME OVER!", True, RED)
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
    screen.blit(game_over_text, game_over_rect)
    
    score_text = font_medium.render(f"Final Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
    screen.blit(score_text, score_rect)
    
    level_text = font_medium.render(f"Level Reached: {level}", True, WHITE)
    level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
    screen.blit(level_text, level_rect)
    
    restart_text = font_small.render("SPACE чтобы заново или ESC выйти", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
    screen.blit(restart_text, restart_rect)
    
    pygame.display.update()
    
# ресет игры
def reset_game():
    """обнуляем все, типа новая игра"""
    global snake, food, score, level, current_speed, foods_eaten_for_level
    snake = Snake()
    food = Food(snake.body)
    score = 0
    level = 1
    current_speed = INITIAL_SPEED
    foods_eaten_for_level = 0
    
# сетка
def draw_grid(screen):
    """рисует сетку (чисто чтоб удобнее было)"""
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y), 1)

# основная функция игры
def main():
    global score, level, current_speed, foods_eaten_for_level
    
    snake = Snake()
    food = Food(snake.body)
    score = 0
    level = 1
    current_speed = INITIAL_SPEED
    foods_eaten_for_level = 0
    
    running = True
    game_over = False
    
    while running:
        # события
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        snake.change_direction("UP")
                    elif event.key == pygame.K_DOWN:
                        snake.change_direction("DOWN")
                    elif event.key == pygame.K_LEFT:
                        snake.change_direction("LEFT")
                    elif event.key == pygame.K_RIGHT:
                        snake.change_direction("RIGHT")
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        reset_game()
                        snake = Snake()
                        food = Food(snake.body)
                        game_over = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
        
        if not game_over:
            # логика
            snake.move()
            
            if snake.check_wall_collision():
                game_over = True
                continue
                
            if snake.check_self_collision():
                game_over = True
                continue
            
            if snake.body[0] == food.position:
                snake.grow()
                score += 10
                foods_eaten_for_level += 1
                
                if foods_eaten_for_level >= FOODS_NEEDED_FOR_LEVEL:
                    level += 1
                    foods_eaten_for_level = 0
                    current_speed += 2
                    print(f"апнул левел {level}, скорость {current_speed}")
                
                food = Food(snake.body)
            
            # рисуем все
            screen.fill(BLACK)
            draw_grid(screen)
            snake.draw(screen)
            food.draw(screen)
            
            score_text = font_small.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            level_text = font_small.render(f"Level: {level}", True, YELLOW)
            level_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
            screen.blit(level_text, level_rect)
            
            foods_left = FOODS_NEEDED_FOR_LEVEL - foods_eaten_for_level
            progress_text = font_small.render(f"еще {foods_left} до {level + 1}", True, GRAY)
            progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 20))
            screen.blit(progress_text, progress_rect)
            
            pygame.display.update()
            clock.tick(current_speed)
            
        else:
            show_game_over(screen, score, level)
            clock.tick(30)
    
    pygame.quit()
    sys.exit()

# запуск игры
if __name__ == "__main__":
    main()