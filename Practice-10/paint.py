import pygame
import sys
import math

# запускаем пайгейм 
pygame.init()

# размеры окна
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TOOLBAR_HEIGHT = 80  # панелька снизу
CANVAS_HEIGHT = SCREEN_HEIGHT - TOOLBAR_HEIGHT  # остальное под рисование

# цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# список цветов для выбора
COLORS = [BLACK, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, ORANGE, PURPLE]
COLOR_NAMES = ["Black", "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "Orange", "Purple"]

# типы инструментов типо режимы и все такое
TOOL_PEN = "pen"
TOOL_RECTANGLE = "rectangle"
TOOL_CIRCLE = "circle"
TOOL_ERASER = "eraser"

# создаем окно
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint - Draw Shapes, Erase, Choose Colors")

# шрифты
font = pygame.font.SysFont("Arial", 16)
font_small = pygame.font.SysFont("Arial", 12)

# контроль FPS
clock = pygame.time.Clock()

# класс холста (где рисуем)
class DrawingCanvas:
    """типа лист бумаги где все происходит"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # поверхность (как будто экран внутри экрана)
        self.surface = pygame.Surface((width, height))
        self.surface.fill(WHITE)
        self.current_color = BLACK
        self.current_tool = TOOL_PEN
        self.brush_size = 5
        self.drawing = False
        self.start_pos = None  # для фигур
        self.last_pos = None   # для линий
        
    def draw_pen(self, current_pos):
        """рисуем линию как карандашом"""
        if self.last_pos:
            pygame.draw.line(self.surface, self.current_color, 
                           self.last_pos, current_pos, self.brush_size)
        else:
            pygame.draw.circle(self.surface, self.current_color, 
                             current_pos, self.brush_size // 2)
        self.last_pos = current_pos
        
    def draw_eraser(self, current_pos):
        """ластик (по сути просто белым рисуем)"""
        old_color = self.current_color
        self.current_color = WHITE
        self.draw_pen(current_pos)
        self.current_color = old_color
        
    def draw_rectangle(self, start_pos, end_pos):
        """рисует прямоугольник"""
        x = min(start_pos[0], end_pos[0])
        y = min(start_pos[1], end_pos[1])
        width = abs(start_pos[0] - end_pos[0])
        height = abs(start_pos[1] - end_pos[1])
        pygame.draw.rect(self.surface, self.current_color, 
                        (x, y, width, height), self.brush_size)
        
    def draw_circle(self, start_pos, end_pos):
        radius = int(math.hypot(end_pos[0] - start_pos[0], 
                               end_pos[1] - start_pos[1]))
        center = start_pos
        pygame.draw.circle(self.surface, self.current_color, 
                          center, radius, self.brush_size)
        
    def start_drawing(self, pos):
        """начали рисовать"""
        self.drawing = True
        self.start_pos = pos
        self.last_pos = pos
        
        # сразу ставим точку если это кисть или ластик
        if self.current_tool in [TOOL_PEN, TOOL_ERASER]:
            if self.current_tool == TOOL_PEN:
                pygame.draw.circle(self.surface, self.current_color, pos, self.brush_size // 2)
            elif self.current_tool == TOOL_ERASER:
                old_color = self.current_color
                self.current_color = WHITE
                pygame.draw.circle(self.surface, WHITE, pos, self.brush_size // 2)
                self.current_color = old_color
                
    def update_drawing(self, current_pos):
        """обновляем пока мышку двигаем"""
        if not self.drawing:
            return
            
        if self.current_tool == TOOL_PEN:
            self.draw_pen(current_pos)
            self.last_pos = current_pos
        elif self.current_tool == TOOL_ERASER:
            self.draw_eraser(current_pos)
            self.last_pos = current_pos
            
    def finish_drawing(self, end_pos):
        """заканчиваем рисование (для фигур важно)"""
        if not self.drawing:
            return
            
        if self.current_tool == TOOL_RECTANGLE:
            self.draw_rectangle(self.start_pos, end_pos)
        elif self.current_tool == TOOL_CIRCLE:
            self.draw_circle(self.start_pos, end_pos)
            
        self.drawing = False
        self.start_pos = None
        self.last_pos = None
        
    def clear_canvas(self):
        """очищаем все (с нуля типо)"""
        self.surface.fill(WHITE)
        
    def draw(self, target_surface, offset_y=0):
        """выводим холст на экран"""
        target_surface.blit(self.surface, (0, offset_y))

# тулбар (кнопки снизу)
class Toolbar:
    """панель с инструментами и цветами"""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.buttons = []
        self.create_buttons()
        
    def create_buttons(self):
        """создаем все кнопки"""
        button_width = 80
        button_height = 60
        spacing = 10
        start_x = self.rect.x + 10
        
        tools = [
            (TOOL_PEN, "Pen", LIGHT_GRAY),
            (TOOL_RECTANGLE, "Rect", LIGHT_GRAY),
            (TOOL_CIRCLE, "Circle", LIGHT_GRAY),
            (TOOL_ERASER, "Eraser", LIGHT_GRAY)
        ]
        
        x = start_x
        for tool_id, tool_name, color in tools:
            button = ToolButton(x, self.rect.y + 10, button_width, button_height, 
                               tool_name, color, tool_type=tool_id)
            self.buttons.append(button)
            x += button_width + spacing
            
        x += 20  # просто отступ
        
        # кнопки цветов
        for color, color_name in zip(COLORS, COLOR_NAMES):
            button = ToolButton(x, self.rect.y + 10, button_width, button_height,
                               color_name, color, color_value=color)
            self.buttons.append(button)
            x += button_width + spacing
            
        # кнопка очистки
        button = ToolButton(x, self.rect.y + 10, button_width, button_height,
                           "Clear", GRAY, action="clear")
        self.buttons.append(button)
        
        # размер кисти
        x += button_width + 30
        self.size_down_button = ToolButton(x, self.rect.y + 10, 40, 30, "-", LIGHT_GRAY, action="size_down")
        self.buttons.append(self.size_down_button)
        x += 45
        self.size_up_button = ToolButton(x, self.rect.y + 10, 40, 30, "+", LIGHT_GRAY, action="size_up")
        self.buttons.append(self.size_up_button)
        
    def handle_click(self, mouse_pos):
        """обработка кликов по кнопкам"""
        for button in self.buttons:
            if button.rect.collidepoint(mouse_pos):
                return button
        return None
        
    def draw(self, screen, current_tool, current_color, brush_size):
        """рисуем панель"""
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        for button in self.buttons:
            is_active = False
            if hasattr(button, 'tool_type') and button.tool_type == current_tool:
                is_active = True
            elif hasattr(button, 'color_value') and button.color_value == current_color:
                is_active = True
            button.draw(screen, is_active)
            
        size_text = font_small.render(f"Size: {brush_size}", True, BLACK)
        size_rect = size_text.get_rect(topleft=(self.size_up_button.rect.right + 10, 
                                                self.size_down_button.rect.centery - 10))
        screen.blit(size_text, size_rect)

class ToolButton:
    """одна кнопка"""
    
    def __init__(self, x, y, width, height, text, color, 
                 tool_type=None, color_value=None, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.tool_type = tool_type
        self.color_value = color_value
        self.action = action
        
    def draw(self, screen, is_active=False):
        """рисуем кнопку"""
        button_color = self.color
        if is_active:
            button_color = (255, 255, 150)  # подсветка
        pygame.draw.rect(screen, button_color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        if text_surface.get_width() > self.rect.width - 10:
            text_surface = font_small.render(self.text, True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

# превью фигур пока тянешь мышкой
def draw_preview(screen, canvas, start_pos, current_pos, tool, color, brush_size):
    """временный рисунок чтоб видеть что рисуешь"""
    if not start_pos:
        return
        
    preview_surface = canvas.surface.copy()
    
    if tool == TOOL_RECTANGLE:
        x = min(start_pos[0], current_pos[0])
        y = min(start_pos[1], current_pos[1])
        width = abs(start_pos[0] - current_pos[0])
        height = abs(start_pos[1] - current_pos[1])
        pygame.draw.rect(preview_surface, color, (x, y, width, height), brush_size)
    elif tool == TOOL_CIRCLE:
        radius = int(math.hypot(current_pos[0] - start_pos[0], 
                               current_pos[1] - start_pos[1]))
        pygame.draw.circle(preview_surface, color, start_pos, radius, brush_size)
        
    screen.blit(preview_surface, (0, 0))
    return preview_surface

# главная функция
def main():
    canvas = DrawingCanvas(SCREEN_WIDTH, CANVAS_HEIGHT)
    toolbar = Toolbar(0, CANVAS_HEIGHT, SCREEN_WIDTH, TOOLBAR_HEIGHT)
    
    running = True
    preview_active = False
    preview_start = None
    
    while running:
        # события
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if toolbar.rect.collidepoint(mouse_pos):
                    button = toolbar.handle_click(mouse_pos)
                    if button:
                        if button.tool_type:
                            canvas.current_tool = button.tool_type
                        elif button.color_value is not None:
                            canvas.current_color = button.color_value
                        elif button.action == "clear":
                            canvas.clear_canvas()
                        elif button.action == "size_up":
                            canvas.brush_size = min(50, canvas.brush_size + 1)
                        elif button.action == "size_down":
                            canvas.brush_size = max(1, canvas.brush_size - 1)
                else:
                    canvas_x = mouse_pos[0]
                    canvas_y = mouse_pos[1]
                    
                    if 0 <= canvas_x < SCREEN_WIDTH and 0 <= canvas_y < CANVAS_HEIGHT:
                        canvas.start_drawing((canvas_x, canvas_y))
                        
                        if canvas.current_tool in [TOOL_RECTANGLE, TOOL_CIRCLE]:
                            preview_active = True
                            preview_start = (canvas_x, canvas_y)
                            
            elif event.type == pygame.MOUSEBUTTONUP:
                if canvas.drawing:
                    mouse_pos = pygame.mouse.get_pos()
                    canvas_x = mouse_pos[0]
                    canvas_y = mouse_pos[1]
                    
                    if 0 <= canvas_x < SCREEN_WIDTH and 0 <= canvas_y < CANVAS_HEIGHT:
                        canvas.finish_drawing((canvas_x, canvas_y))
                    else:
                        canvas.finish_drawing(canvas.last_pos if canvas.last_pos else (canvas_x, canvas_y))
                    
                    preview_active = False
                    preview_start = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if canvas.drawing:
                    mouse_pos = pygame.mouse.get_pos()
                    canvas_x = mouse_pos[0]
                    canvas_y = mouse_pos[1]
                    
                    if 0 <= canvas_x < SCREEN_WIDTH and 0 <= canvas_y < CANVAS_HEIGHT:
                        canvas.update_drawing((canvas_x, canvas_y))
                    else:
                        canvas.drawing = False
                        canvas.last_pos = None
                        
        # рисуем
        screen.fill(WHITE)
        canvas.draw(screen, 0)
        
        if preview_active and preview_start:
            mouse_pos = pygame.mouse.get_pos()
            canvas_x = mouse_pos[0]
            canvas_y = mouse_pos[1]
            if 0 <= canvas_x < SCREEN_WIDTH and 0 <= canvas_y < CANVAS_HEIGHT:
                draw_preview(screen, canvas, preview_start, (canvas_x, canvas_y),
                           canvas.current_tool, canvas.current_color, canvas.brush_size)
                
        toolbar.draw(screen, canvas.current_tool, canvas.current_color, canvas.brush_size)
        
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()
    sys.exit()

# запуск
if __name__ == "__main__":
    main()