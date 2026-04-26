"""
launcher.py — Entry point for TSIS 4 Snake.
Flow: Main Menu → Name Entry → Game → Game Over → retry / menu
      Main Menu → Leaderboard
      Main Menu → Settings
"""

import sys
import pygame
from gameconf import BOARD_WIDTH, BOARD_HEIGHT, RENDER_FPS
from datastore import ensure_schema
from engine import SnakeRound, load_user_prefs
from screens import LeaderboardScreen, MainMenuScreen, NameEntryScreen, SettingsScreen


def main():
    pygame.init()
    window     = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))
    pygame.display.set_caption("Snake — TSIS 4")
    tick_clock = pygame.time.Clock()

    # Initialise DB (create tables if they don't exist)
    db_ready = ensure_schema()
    if not db_ready:
        print("[WARNING] Could not connect to PostgreSQL. "
              "Leaderboard and score saving will be disabled.")

    prefs         = load_user_prefs()
    player_handle = None

    while True:
        menu_action = MainMenuScreen().run(window, tick_clock)

        if menu_action == "leaderboard":
            LeaderboardScreen().run(window, tick_clock)

        elif menu_action == "settings":
            SettingsScreen().run(window, tick_clock)
            prefs = load_user_prefs()

        elif menu_action == "play":
            if player_handle is None:
                player_handle = NameEntryScreen().run(window, tick_clock)

            while True:
                prefs         = load_user_prefs()
                round_session = SnakeRound(window, tick_clock, player_handle, prefs)
                run_outcome   = round_session.run()   # "retry" or "menu"

                if run_outcome == "retry":
                    continue
                else:
                    player_handle = None
                    break

        elif menu_action == "quit":
            pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()
