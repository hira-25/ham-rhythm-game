
# simple_ddr.py
# Minimal DDR-style game using Pygame: arrows scroll up, press corresponding arrow keys.

import pygame
import random
import sys

# Configuration
WIDTH, HEIGHT = 400, 600
BG_COLOR = (30, 30, 30)
ARROW_COLOR = (200, 200, 200)
TARGET_Y = 100
SPAWN_INTERVAL = 1000  # milliseconds
SPEED = 200  # pixels per second
TOLERANCE = 30  # pixels

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Hamster DDR")
clock = pygame.time.Clock()

# Load font
font = pygame.font.SysFont(None, 60)

# Arrow mapping
directions = {
    pygame.K_LEFT: ("←", WIDTH * 0.2),
    pygame.K_DOWN: ("↓", WIDTH * 0.4),
    pygame.K_UP:   ("↑", WIDTH * 0.6),
    pygame.K_RIGHT:("→", WIDTH * 0.8),
}

# Game state
arrows = []  # list of dicts: {"dir": key, "x": pos, "y": HEIGHT}
score = 0
misses = 0

# Timer for spawning
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == SPAWN_EVENT:
            key = random.choice(list(directions.keys()))
            arrow_char, x = directions[key]
            arrows.append({"key": key, "char": arrow_char, "x": x, "y": HEIGHT})
        elif event.type == pygame.KEYDOWN:
            for arrow in list(arrows):
                if arrow["key"] == event.key and abs(arrow["y"] - TARGET_Y) < TOLERANCE:
                    score += 1
                    arrows.remove(arrow)
                    break

    # Move arrows
    for arrow in list(arrows):
        arrow["y"] -= SPEED * dt
        if arrow["y"] < TARGET_Y - TOLERANCE:
            misses += 1
            arrows.remove(arrow)

    # Draw
    screen.fill(BG_COLOR)
    # Draw target zone
    pygame.draw.line(screen, (255, 0, 0), (0, TARGET_Y), (WIDTH, TARGET_Y), 2)

    # Draw arrows
    for arrow in arrows:
        text = font.render(arrow["char"], True, ARROW_COLOR)
        rect = text.get_rect(center=(arrow["x"], arrow["y"]))
        screen.blit(text, rect)

    # Draw score
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    miss_text = font.render(f"Miss: {misses}", True, (255, 100, 100))
    screen.blit(miss_text, (10, 60))

    pygame.display.flip()

pygame.quit()
sys.exit()
