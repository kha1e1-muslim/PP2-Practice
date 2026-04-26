"""
ui.py — All non-game Pygame screens:
  MainMenuScreen, NameEntryScreen, SettingsScreen, GameOverScreen, LeaderboardScreen
Each screen has a run(window, tick_clock) method that returns a string action.
"""

import sys
import pygame
from persistence import fetch_leaderboard, load_preferences, save_preferences

# ── Colours ───────────────────────────────────────────────────────────────────
COL_BLACK  = (0,   0,   0)
COL_WHITE  = (255, 255, 255)
COL_DGRAY  = (30,  30,  30)
COL_GRAY   = (80,  80,  80)
COL_LGRAY  = (140, 140, 140)
COL_PANEL  = (25,  25,  35)
COL_GOLD   = (255, 200, 0)
COL_RED    = (220, 50,  50)
COL_GREEN  = (50,  200, 80)
COL_BLUE   = (60,  120, 220)
COL_TEAL   = (0,   180, 180)

WIN_W, WIN_H   = 600, 700
FRAMES_PER_SEC = 60

# ── Palette of selectable car colours ────────────────────────────────────────
CAR_PALETTE = [
    ((28,  32,  38),  "Dark"),
    ((255, 100, 0),   "Orange"),
    ((200, 200, 200), "Silver"),
    ((120, 0,   160), "Purple"),
    ((200, 150, 0),   "Gold"),
    ((30,  150, 60),  "Green"),
    ((30,  80,  180), "Blue"),
    ((180, 30,  30),  "Red"),
]


# ─────────────────────────────────────────────
#  HELPER — simple button
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
#  BACKGROUND helper
# ─────────────────────────────────────────────
def render_backdrop(window, title, subtitle=""):
    window.fill(COL_DGRAY)
    # Top gradient strip
    for i in range(120):
        fade_alpha = int(180 * (1 - i / 120))
        tone = (0, max(0, 60 - i // 2), max(0, 80 - i // 2))
        pygame.draw.line(window, tone, (0, i), (WIN_W, i))

    title_font    = pygame.font.SysFont("arial", 52, bold=True)
    subtitle_font = pygame.font.SysFont("arial", 20)
    title_surf = title_font.render(title, True, COL_GOLD)
    window.blit(title_surf, title_surf.get_rect(center=(WIN_W // 2, 60)))
    if subtitle:
        subtitle_surf = subtitle_font.render(subtitle, True, COL_LGRAY)
        window.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIN_W // 2, 110)))


# ─────────────────────────────────────────────
#  LEADERBOARD SCREEN
# ─────────────────────────────────────────────
class LeaderboardScreen:
    def run(self, window, tick_clock):
        body_font   = pygame.font.SysFont("consolas", 22, bold=True)
        small_font  = pygame.font.SysFont("consolas", 17)
        header_font = pygame.font.SysFont("consolas", 16, bold=True)
        mid_x       = WIN_W // 2
        back_btn    = MenuButton((mid_x - 80, WIN_H - 70, 160, 46), "◀ Back", COL_BLUE)
        roster      = fetch_leaderboard()

        while True:
            tick_clock.tick(FRAMES_PER_SEC)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if back_btn.is_clicked(event):
                    return "back"

            render_backdrop(window, "LEADERBOARD", "Top 10 Drivers")

            # Header row
            header_y   = 140
            col_x_pos  = [50, 160, 340, 440, 530]
            col_titles = ["#", "Name", "Score", "Dist", "Coins"]
            for hx, ht in zip(col_x_pos, col_titles):
                hdr_surf = header_font.render(ht, True, COL_GOLD)
                window.blit(hdr_surf, (hx, header_y))

            pygame.draw.line(window, COL_LGRAY, (30, header_y + 24), (WIN_W - 30, header_y + 24), 1)

            if not roster:
                empty_label = small_font.render("No scores yet — go race!", True, COL_LGRAY)
                window.blit(empty_label, empty_label.get_rect(center=(mid_x, 300)))
            else:
                for place, record in enumerate(roster, 1):
                    row_y     = header_y + 30 + (place - 1) * 36
                    row_color = COL_GOLD if place == 1 else (COL_LGRAY if place > 3 else COL_WHITE)

                    # Alternate row background
                    if place % 2 == 0:
                        pygame.draw.rect(window, (40, 40, 55),
                                         (30, row_y - 4, WIN_W - 60, 30), border_radius=4)

                    cell_values = [
                        str(place),
                        record.get("name", "?")[:12],
                        str(record.get("score", 0)),
                        str(record.get("distance", 0)) + "m",
                        str(record.get("coins", 0)),
                    ]
                    for hx, cell_val in zip(col_x_pos, cell_values):
                        cell_surf = small_font.render(cell_val, True, row_color)
                        window.blit(cell_surf, (hx, row_y))

            back_btn.update(mouse_pos)
            back_btn.draw(window, small_font)
            pygame.display.flip()


# ─────────────────────────────────────────────
#  GAME OVER SCREEN
# ─────────────────────────────────────────────
class GameOverScreen:
    def run(self, window, tick_clock, final_score, final_distance, final_coins, driver_name):
        title_font = pygame.font.SysFont("arial", 48, bold=True)
        body_font  = pygame.font.SysFont("arial", 26, bold=True)
        small_font = pygame.font.SysFont("arial", 20)
        mid_x      = WIN_W // 2

        retry_btn = MenuButton((mid_x - 130, 460, 120, 50), "Retry",     COL_GREEN)
        menu_btn  = MenuButton((mid_x + 10,  460, 120, 50), "Main Menu", COL_BLUE)

        while True:
            tick_clock.tick(FRAMES_PER_SEC)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if retry_btn.is_clicked(event):
                    return "retry"
                if menu_btn.is_clicked(event):
                    return "menu"

            render_backdrop(window, "GAME OVER")

            # Driver name
            name_label = body_font.render(f"Driver: {driver_name}", True, COL_GOLD)
            window.blit(name_label, name_label.get_rect(center=(mid_x, 155)))

            # Stats box
            stats_box = pygame.Rect(mid_x - 180, 200, 360, 230)
            pygame.draw.rect(window, COL_PANEL, stats_box, border_radius=12)
            pygame.draw.rect(window, COL_LGRAY, stats_box, 2, border_radius=12)

            stat_rows = [
                ("Score",    f"{final_score}",       COL_GOLD),
                ("Distance", f"{final_distance} m",  COL_TEAL),
                ("Coins",    f"{final_coins}",        (255, 210, 50)),
            ]
            for i, (label, val, tone) in enumerate(stat_rows):
                row_y = 225 + i * 62
                window.blit(small_font.render(label, True, COL_LGRAY),
                            (stats_box.x + 20, row_y))
                val_surf = body_font.render(val, True, tone)
                window.blit(val_surf, (stats_box.right - val_surf.get_width() - 20, row_y))

            for btn in (retry_btn, menu_btn):
                btn.update(mouse_pos)
                btn.draw(window, small_font)

            pygame.display.flip()


# ─────────────────────────────────────────────
#  SETTINGS SCREEN
# ─────────────────────────────────────────────
class SettingsScreen:
    def run(self, window, tick_clock):
        label_font = pygame.font.SysFont("arial", 24, bold=True)
        mini_font  = pygame.font.SysFont("arial", 18)
        mid_x      = WIN_W // 2
        prefs      = load_preferences()

        # Find current car color index
        def find_color_index():
            cur = tuple(prefs["car_color"])
            for i, (tone, _) in enumerate(CAR_PALETTE):
                if tuple(tone) == cur:
                    return i
            return 0

        color_index_state = find_color_index()

        sound_btn       = MenuButton((mid_x - 80, 200, 160, 44), "", COL_GRAY)
        diff_btn        = MenuButton((mid_x - 80, 290, 160, 44), "", COL_GRAY)
        color_left_btn  = MenuButton((mid_x - 160, 375, 44, 44), "◀", COL_GRAY)
        color_right_btn = MenuButton((mid_x + 116, 375, 44, 44), "▶", COL_GRAY)
        save_btn        = MenuButton((mid_x - 100, 490, 200, 50), "Save & Back", COL_GREEN)
        cancel_btn      = MenuButton((mid_x - 80,  555, 160, 40), "Cancel",      COL_RED)

        difficulty_levels = ["easy", "normal", "hard"]

        def refresh_labels():
            sound_btn.text = f"Sound: {'ON' if prefs['sound'] else 'OFF'}"
            diff_btn.text  = f"Difficulty: {prefs['difficulty'].capitalize()}"

        refresh_labels()

        while True:
            tick_clock.tick(FRAMES_PER_SEC)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if sound_btn.is_clicked(event):
                    prefs["sound"] = not prefs["sound"]
                    refresh_labels()

                if diff_btn.is_clicked(event):
                    cur_diff_idx = difficulty_levels.index(prefs["difficulty"])
                    prefs["difficulty"] = difficulty_levels[(cur_diff_idx + 1) % len(difficulty_levels)]
                    refresh_labels()

                if color_left_btn.is_clicked(event):
                    color_index_state = (color_index_state - 1) % len(CAR_PALETTE)
                    prefs["car_color"] = list(CAR_PALETTE[color_index_state][0])

                if color_right_btn.is_clicked(event):
                    color_index_state = (color_index_state + 1) % len(CAR_PALETTE)
                    prefs["car_color"] = list(CAR_PALETTE[color_index_state][0])

                if save_btn.is_clicked(event):
                    save_preferences(prefs)
                    return "back"

                if cancel_btn.is_clicked(event):
                    return "back"

            render_backdrop(window, "SETTINGS")

            for btn in (sound_btn, diff_btn, color_left_btn, color_right_btn, save_btn, cancel_btn):
                btn.update(mouse_pos)
                btn.draw(window, mini_font)

            # Section labels
            window.blit(mini_font.render("Audio",       True, COL_LGRAY), (mid_x - 160, 175))
            window.blit(mini_font.render("Difficulty",  True, COL_LGRAY), (mid_x - 160, 265))
            window.blit(mini_font.render("Car Colour",  True, COL_LGRAY), (mid_x - 160, 350))

            # Car colour preview swatch
            swatch_box = pygame.Rect(mid_x - 60, 375, 120, 44)
            pygame.draw.rect(window, CAR_PALETTE[color_index_state][0], swatch_box, border_radius=6)
            pygame.draw.rect(window, COL_WHITE, swatch_box, 2, border_radius=6)
            swatch_label = mini_font.render(CAR_PALETTE[color_index_state][1], True, COL_WHITE)
            window.blit(swatch_label, swatch_label.get_rect(center=swatch_box.center))

            pygame.display.flip()


# ─────────────────────────────────────────────
#  NAME ENTRY
# ─────────────────────────────────────────────
class NameEntryScreen:
    def run(self, window, tick_clock):
        title_font = pygame.font.SysFont("arial", 36, bold=True)
        body_font  = pygame.font.SysFont("arial", 24)
        tiny_font  = pygame.font.SysFont("arial", 16)
        mid_x      = WIN_W // 2
        typed_name = ""
        input_box  = pygame.Rect(mid_x - 160, 280, 320, 54)
        start_btn  = MenuButton((mid_x - 100, 370, 200, 50), "Start Racing", COL_GREEN)
        err_msg    = ""

        while True:
            tick_clock.tick(FRAMES_PER_SEC)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if typed_name.strip():
                            return typed_name.strip()
                        err_msg = "Please enter a name!"
                    elif event.key == pygame.K_BACKSPACE:
                        typed_name = typed_name[:-1]
                    else:
                        char_in = event.unicode
                        if char_in.isprintable() and len(typed_name) < 16:
                            typed_name += char_in
                if start_btn.is_clicked(event):
                    if typed_name.strip():
                        return typed_name.strip()
                    err_msg = "Please enter a name!"

            render_backdrop(window, "ENTER YOUR NAME")
            prompt_label = body_font.render("Your racing name:", True, COL_WHITE)
            window.blit(prompt_label, prompt_label.get_rect(center=(mid_x, 250)))

            # Input box
            pygame.draw.rect(window, (50, 50, 70), input_box, border_radius=8)
            pygame.draw.rect(window, COL_GOLD, input_box, 2, border_radius=8)
            name_surf = title_font.render(typed_name + "|", True, COL_WHITE)
            window.blit(name_surf, name_surf.get_rect(center=input_box.center))

            start_btn.update(mouse_pos)
            start_btn.draw(window, body_font)

            if err_msg:
                err_surf = tiny_font.render(err_msg, True, COL_RED)
                window.blit(err_surf, err_surf.get_rect(center=(mid_x, 440)))

            hint_surf = tiny_font.render("Max 16 characters · Press Enter to confirm", True, COL_LGRAY)
            window.blit(hint_surf, hint_surf.get_rect(center=(mid_x, WIN_H - 30)))
            pygame.display.flip()


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainMenuScreen:
    def run(self, window, tick_clock):
        menu_font = pygame.font.SysFont("arial", 28, bold=True)
        hint_font = pygame.font.SysFont("arial", 16)
        mid_x     = WIN_W // 2

        menu_buttons = [
            MenuButton((mid_x - 120, 200, 240, 54), "▶  Play",        COL_GREEN),
            MenuButton((mid_x - 120, 270, 240, 54), "🏆  Leaderboard", COL_BLUE),
            MenuButton((mid_x - 120, 340, 240, 54), "⚙  Settings",    COL_GRAY),
            MenuButton((mid_x - 120, 410, 240, 54), "✕  Quit",        COL_RED),
        ]
        action_keys = ["play", "leaderboard", "settings", "quit"]

        while True:
            tick_clock.tick(FRAMES_PER_SEC)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                for btn, act in zip(menu_buttons, action_keys):
                    if btn.is_clicked(event):
                        return act

            render_backdrop(window, "MERCEDES RACER", "Dodge traffic · Collect power-ups · Set records")
            for btn in menu_buttons:
                btn.update(mouse_pos)
                btn.draw(window, menu_font)

            hint_surf = hint_font.render("Arrow keys to drive", True, COL_LGRAY)
            window.blit(hint_surf, hint_surf.get_rect(center=(mid_x, WIN_H - 30)))
            pygame.display.flip()
