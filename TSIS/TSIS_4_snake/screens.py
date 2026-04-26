"""
screens.py — All Pygame screens for TSIS 4 Snake:
  MainMenuScreen, NameEntryScreen, SettingsScreen, GameOverScreen, LeaderboardScreen
"""

import sys
import pygame
from gameconf import (BOARD_WIDTH, BOARD_HEIGHT, RENDER_FPS,
                      COL_BLACK, COL_WHITE, COL_GRAY, COL_LGRAY, COL_DGRAY,
                      COL_GOLD, COL_TEAL, COL_PANEL, COL_ACTIVE,
                      POWERUP_COLOR_MAP, PREFS_PATH, DEFAULT_PREFS)
from datastore import fetch_top_scores
from engine import load_user_prefs, save_user_prefs

BOARD_W, BOARD_H = BOARD_WIDTH, BOARD_HEIGHT

# ── Selectable snake colours ──────────────────────────────────────────────────
SNAKE_PALETTE = [
    ([255, 120, 0],   "Orange"),
    ([220, 220, 220], "White"),
    ([0,   200, 180], "Teal"),
    ([160, 0,   200], "Purple"),
    ([200, 150, 0],   "Gold"),
    ([220, 50,  50],  "Red"),
    ([0,   160, 220], "Blue"),
    ([0,   200, 0],   "Green"),
]

COL_RED_BTN   = (200, 40,  40)
COL_GREEN_BTN = (50,  200, 80)
COL_BLUE_BTN  = (60,  120, 220)


# ─────────────────────────────────────────────
#  UI BUTTON
# ─────────────────────────────────────────────
class MenuButton:
    def __init__(self, rect, text, color=COL_GRAY, text_color=COL_WHITE):
        self.rect       = pygame.Rect(rect)
        self.text       = text
        self.color      = color
        self.text_color = text_color
        self.hover      = False

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface, font):
        tone = tuple(min(255, v + 30) for v in self.color) if self.hover else self.color
        pygame.draw.rect(surface, tone,      self.rect, border_radius=10)
        pygame.draw.rect(surface, COL_WHITE, self.rect, 2, border_radius=10)
        label_surf = font.render(self.text, True, self.text_color)
        surface.blit(label_surf, label_surf.get_rect(center=self.rect.center))


# ─────────────────────────────────────────────
#  BACKGROUND
# ─────────────────────────────────────────────
def render_backdrop(window, title, subtitle=""):
    window.fill(COL_DGRAY)
    for i in range(100):
        tone = (0, max(0, 50 - i // 2), max(0, 70 - i // 2))
        pygame.draw.line(window, tone, (0, i), (BOARD_W, i))
    title_font    = pygame.font.SysFont("consolas", 46, bold=True)
    subtitle_font = pygame.font.SysFont("consolas", 18)
    title_surf = title_font.render(title, True, COL_GOLD)
    window.blit(title_surf, title_surf.get_rect(center=(BOARD_W // 2, 55)))
    if subtitle:
        sub_surf = subtitle_font.render(subtitle, True, COL_LGRAY)
        window.blit(sub_surf, sub_surf.get_rect(center=(BOARD_W // 2, 100)))


# ─────────────────────────────────────────────
#  LEADERBOARD SCREEN
# ─────────────────────────────────────────────
class LeaderboardScreen:
    def run(self, window, tick_clock):
        body_font   = pygame.font.SysFont("consolas", 20, bold=True)
        small_font  = pygame.font.SysFont("consolas", 16)
        header_font = pygame.font.SysFont("consolas", 15, bold=True)
        mid_x       = BOARD_W // 2
        back_btn    = MenuButton((mid_x - 75, BOARD_H - 62, 150, 44), "◀ Back", COL_BLUE_BTN)
        roster      = fetch_top_scores(10)

        while True:
            tick_clock.tick(RENDER_FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if back_btn.is_clicked(event): return "back"

            render_backdrop(window, "LEADERBOARD", "Top 10 All-Time Scores")

            header_y   = 130
            col_x_pos  = [28, 90, 270, 370, 460]
            col_titles = ["#", "Username", "Score", "Level", "Date"]
            for hx, ht in zip(col_x_pos, col_titles):
                window.blit(header_font.render(ht, True, COL_GOLD), (hx, header_y))
            pygame.draw.line(window, COL_LGRAY,
                             (20, header_y + 22), (BOARD_W - 20, header_y + 22), 1)

            if not roster:
                empty_label = small_font.render("No scores yet — play a game!", True, COL_LGRAY)
                window.blit(empty_label, empty_label.get_rect(center=(mid_x, 280)))
            else:
                for place, record in enumerate(roster, 1):
                    row_y     = header_y + 28 + (place - 1) * 34
                    row_color = COL_GOLD if place == 1 else (COL_WHITE if place <= 3 else COL_LGRAY)
                    if place % 2 == 0:
                        pygame.draw.rect(window, (38, 38, 55),
                                         (20, row_y - 3, BOARD_W - 40, 28), border_radius=4)
                    cell_values = [
                        str(place),
                        record.get("username", "?")[:14],
                        str(record.get("score", 0)),
                        str(record.get("level", 0)),
                        str(record.get("date", ""))[:10],
                    ]
                    for hx, cell_val in zip(col_x_pos, cell_values):
                        window.blit(small_font.render(cell_val, True, row_color), (hx, row_y))

            back_btn.update(mouse_pos)
            back_btn.draw(window, small_font)
            pygame.display.flip()


# ─────────────────────────────────────────────
#  GAME OVER SCREEN
# ─────────────────────────────────────────────
class GameOverScreen:
    def run(self, window, tick_clock, final_score, final_level, best_score, user_handle):
        title_font = pygame.font.SysFont("consolas", 44, bold=True)
        body_font  = pygame.font.SysFont("consolas", 24, bold=True)
        small_font = pygame.font.SysFont("consolas", 19)
        mid_x      = BOARD_W // 2

        retry_btn = MenuButton((mid_x - 125, 450, 115, 48), "Retry",     COL_GREEN_BTN)
        menu_btn  = MenuButton((mid_x + 10,  450, 115, 48), "Main Menu", COL_BLUE_BTN)

        is_new_best = final_score >= best_score and final_score > 0

        while True:
            tick_clock.tick(RENDER_FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if retry_btn.is_clicked(event): return "retry"
                if menu_btn.is_clicked(event):  return "menu"

            render_backdrop(window, "GAME OVER")

            # Player name
            name_label = body_font.render(f"Player: {user_handle}", True, COL_GOLD)
            window.blit(name_label, name_label.get_rect(center=(mid_x, 145)))

            # Stats box
            stats_box = pygame.Rect(mid_x - 170, 185, 340, 240)
            pygame.draw.rect(window, COL_PANEL, stats_box, border_radius=12)
            pygame.draw.rect(window, COL_LGRAY, stats_box, 2, border_radius=12)

            stat_rows = [
                ("Score",          str(final_score), COL_GOLD),
                ("Level Reached",  str(final_level), COL_TEAL),
                ("Personal Best",  str(best_score),
                 (255, 200, 50) if is_new_best else COL_LGRAY),
            ]
            for i, (label, val, tone) in enumerate(stat_rows):
                row_y = 210 + i * 64
                window.blit(small_font.render(label, True, COL_LGRAY), (stats_box.x + 16, row_y))
                val_surf = body_font.render(val, True, tone)
                window.blit(val_surf, (stats_box.right - val_surf.get_width() - 16, row_y))

            if is_new_best:
                best_label = small_font.render("🎉 New Personal Best!", True, (255, 220, 50))
                window.blit(best_label, best_label.get_rect(center=(mid_x, 435)))

            for btn in (retry_btn, menu_btn):
                btn.update(mouse_pos)
                btn.draw(window, small_font)

            pygame.display.flip()


# ─────────────────────────────────────────────
#  SETTINGS SCREEN
# ─────────────────────────────────────────────
class SettingsScreen:
    def run(self, window, tick_clock):
        label_font = pygame.font.SysFont("consolas", 22, bold=True)
        mini_font  = pygame.font.SysFont("consolas", 17)
        mid_x      = BOARD_W // 2
        prefs      = load_user_prefs()

        # Find current color index
        def find_color_idx():
            cur = prefs["snake_color"]
            for i, (tone, _) in enumerate(SNAKE_PALETTE):
                if tone == cur:
                    return i
            return 0

        color_index_state = find_color_idx()

        grid_btn        = MenuButton((mid_x - 70, 195, 140, 40), "", COL_GRAY)
        sound_btn       = MenuButton((mid_x - 70, 255, 140, 40), "", COL_GRAY)
        color_left_btn  = MenuButton((mid_x - 155, 335, 40, 40), "◀", COL_GRAY)
        color_right_btn = MenuButton((mid_x + 115, 335, 40, 40), "▶", COL_GRAY)
        save_btn        = MenuButton((mid_x - 90,  430, 180, 48), "Save & Back", COL_GREEN_BTN)
        cancel_btn      = MenuButton((mid_x - 70,  492, 140, 38), "Cancel",      COL_RED_BTN)

        def refresh_labels():
            grid_btn.text  = f"Grid: {'ON' if prefs['grid'] else 'OFF'}"
            sound_btn.text = f"Sound: {'ON' if prefs['sound'] else 'OFF'}"

        refresh_labels()

        while True:
            tick_clock.tick(RENDER_FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if grid_btn.is_clicked(event):
                    prefs["grid"] = not prefs["grid"]; refresh_labels()
                if sound_btn.is_clicked(event):
                    prefs["sound"] = not prefs["sound"]; refresh_labels()
                if color_left_btn.is_clicked(event):
                    color_index_state = (color_index_state - 1) % len(SNAKE_PALETTE)
                    prefs["snake_color"] = SNAKE_PALETTE[color_index_state][0]
                if color_right_btn.is_clicked(event):
                    color_index_state = (color_index_state + 1) % len(SNAKE_PALETTE)
                    prefs["snake_color"] = SNAKE_PALETTE[color_index_state][0]
                if save_btn.is_clicked(event):
                    save_user_prefs(prefs); return "back"
                if cancel_btn.is_clicked(event):
                    return "back"

            render_backdrop(window, "SETTINGS")

            # Section labels
            for y, label in [(170, "Grid overlay"), (230, "Sound"),
                             (310, "Snake colour")]:
                window.blit(mini_font.render(label, True, COL_LGRAY), (mid_x - 155, y))

            for btn in (grid_btn, sound_btn, color_left_btn, color_right_btn,
                        save_btn, cancel_btn):
                btn.update(mouse_pos)
                btn.draw(window, mini_font)

            # Colour swatch
            swatch_box = pygame.Rect(mid_x - 70, 335, 140, 40)
            pygame.draw.rect(window, SNAKE_PALETTE[color_index_state][0], swatch_box, border_radius=6)
            pygame.draw.rect(window, COL_WHITE, swatch_box, 2, border_radius=6)
            swatch_label = mini_font.render(SNAKE_PALETTE[color_index_state][1], True, COL_WHITE)
            window.blit(swatch_label, swatch_label.get_rect(center=swatch_box.center))

            pygame.display.flip()


# ─────────────────────────────────────────────
#  NAME ENTRY
# ─────────────────────────────────────────────
class NameEntryScreen:
    def run(self, window, tick_clock):
        title_font = pygame.font.SysFont("consolas", 34, bold=True)
        body_font  = pygame.font.SysFont("consolas", 22)
        tiny_font  = pygame.font.SysFont("consolas", 15)
        mid_x      = BOARD_W // 2
        typed_name = ""
        input_box  = pygame.Rect(mid_x - 150, 270, 300, 52)
        start_btn  = MenuButton((mid_x - 90, 350, 180, 48), "Start", COL_GREEN_BTN)
        err_msg    = ""

        while True:
            tick_clock.tick(RENDER_FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if typed_name.strip():
                            return typed_name.strip()
                        err_msg = "Please enter a username!"
                    elif event.key == pygame.K_BACKSPACE:
                        typed_name = typed_name[:-1]
                    else:
                        char_in = event.unicode
                        if char_in.isprintable() and len(typed_name) < 20:
                            typed_name += char_in
                if start_btn.is_clicked(event):
                    if typed_name.strip():
                        return typed_name.strip()
                    err_msg = "Please enter a username!"

            render_backdrop(window, "ENTER USERNAME")
            prompt_label = body_font.render("Your username:", True, COL_WHITE)
            window.blit(prompt_label, prompt_label.get_rect(center=(mid_x, 240)))

            pygame.draw.rect(window, (45, 45, 65), input_box, border_radius=8)
            pygame.draw.rect(window, COL_GOLD, input_box, 2, border_radius=8)
            name_surf = title_font.render(typed_name + "|", True, COL_WHITE)
            window.blit(name_surf, name_surf.get_rect(center=input_box.center))

            start_btn.update(mouse_pos)
            start_btn.draw(window, body_font)

            if err_msg:
                err_surf = tiny_font.render(err_msg, True, (220, 80, 80))
                window.blit(err_surf, err_surf.get_rect(center=(mid_x, 420)))

            hint_surf = tiny_font.render("Max 20 chars · Enter to confirm", True, COL_LGRAY)
            window.blit(hint_surf, hint_surf.get_rect(center=(mid_x, BOARD_H - 28)))
            pygame.display.flip()


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainMenuScreen:
    def run(self, window, tick_clock):
        menu_font = pygame.font.SysFont("consolas", 26, bold=True)
        hint_font = pygame.font.SysFont("consolas", 15)
        mid_x     = BOARD_W // 2

        menu_buttons = [
            MenuButton((mid_x - 110, 190, 220, 52), "▶  Play",        COL_GREEN_BTN),
            MenuButton((mid_x - 110, 258, 220, 52), "🏆  Leaderboard", COL_BLUE_BTN),
            MenuButton((mid_x - 110, 326, 220, 52), "⚙  Settings",    COL_GRAY),
            MenuButton((mid_x - 110, 394, 220, 52), "✕  Quit",        COL_RED_BTN),
        ]
        action_keys = ["play", "leaderboard", "settings", "quit"]

        while True:
            tick_clock.tick(RENDER_FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                for btn, act in zip(menu_buttons, action_keys):
                    if btn.is_clicked(event):
                        return act

            render_backdrop(window, "SNAKE", "Arrow keys to move · Avoid poison · Grab power-ups")
            for btn in menu_buttons:
                btn.update(mouse_pos)
                btn.draw(window, menu_font)

            hint_surf = hint_font.render("P = Pause during game", True, COL_LGRAY)
            window.blit(hint_surf, hint_surf.get_rect(center=(mid_x, BOARD_H - 28)))
            pygame.display.flip()
