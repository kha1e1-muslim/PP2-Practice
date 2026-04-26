"""
main.py — Entry point for TSIS 3 Racer.
Manages the flow between screens:
  Main Menu → Name Entry → Game → Game Over → (retry / menu)
  Main Menu → Leaderboard
  Main Menu → Settings
"""

import sys
import pygame
from persistence import load_preferences
from racer import RacerGame
from ui import LeaderboardScreen, MainMenuScreen, NameEntryScreen, SettingsScreen

WIN_W, WIN_H    = 600, 700
FRAMES_PER_SEC  = 60


def main():
    pygame.init()
    window     = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Mercedes Racer — TSIS 3")
    tick_clock = pygame.time.Clock()

    # Load saved preferences once at startup
    prefs = load_preferences()

    # Driver name persists across retries in the same session
    driver_name = None

    while True:
        # ── Main Menu ─────────────────────────────────────────────────
        menu_action = MainMenuScreen().run(window, tick_clock)

        if menu_action == "leaderboard":
            LeaderboardScreen().run(window, tick_clock)

        elif menu_action == "settings":
            SettingsScreen().run(window, tick_clock)
            prefs = load_preferences()   # reload after save

        elif menu_action == "play":
            # Ask for name once per session (or if they haven't set one)
            if driver_name is None:
                driver_name = NameEntryScreen().run(window, tick_clock)

            # Game loop — supports retry without re-entering name
            while True:
                prefs          = load_preferences()
                racer_session  = RacerGame(window, tick_clock, driver_name, prefs)
                run_outcome    = racer_session.run()   # returns "retry" or "menu"

                if run_outcome == "retry":
                    continue              # re-create game with same name
                else:
                    driver_name = None    # reset name for next play session
                    break                 # back to main menu

        elif menu_action == "quit":
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    main()
