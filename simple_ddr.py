# simple_ddr_ham.py
# DDR-style game with hamster icons

import pygame
import random
import sys

# Configuration
WIDTH, HEIGHT = 400, 600
BG_COLOR = (30, 30, 30)
TARGET_Y = 100
SPAWN_INTERVAL = 1000    # ms
SPEED = 200              # pixels/sec
TOLERANCE = 30           # pixels

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hamster DDR")
clock = pygame.time.Clock()

# Load hamster icons (PNG with transparency)
icons = {
    pygame.K_LEFT:  pygame.image.load("assets/ham_left.png").convert_alpha(),
    pygame.K_DOWN:  pygame.image.load("assets/ham_down.png").convert_alpha(),
    pygame.K_UP:    pygame.image.load("assets/ham_up.png").convert_alpha(),
    pygame.K_RIGHT: pygame.image.load("assets/ham_right.png").convert_alpha(),
}
# Resize icons if needed
ICON_SIZE = 60
for k in icons:
    icons[k] = pygame.transform.smoothscale(icons[k], (ICON_SIZE, ICON_SIZE))

# Positions where hamsters will scroll
positions = {
    pygame.K_LEFT:  WIDTH * 0.2,
    pygame.K_DOWN:  WIDTH * 0.4,
    pygame.K_UP:    WIDTH * 0.6,
    pygame.K_RIGHT: WIDTH * 0.8,
}

# Game state
notes = []   # each: {"key": K_*, "x": float, "y": float}
score = 0
misses = 0

# Spawn timer
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

running = True
while running:
    dt = clock.tick(60) / 1000.0  # delta in seconds

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == SPAWN_EVENT:
            k = random.choice(list(positions.keys()))
            notes.append({"key": k, "x": positions[k], "y": HEIGHT})
        elif e.type == pygame.KEYDOWN:
            for note in list(notes):
                if note["key"] == e.key and abs(note["y"] - TARGET_Y) < TOLERANCE:
                    score += 1
                    notes.remove(note)
                    break

    # Move notes upward
    for note in list(notes):
        note["y"] -= SPEED * dt
        if note["y"] < TARGET_Y - TOLERANCE:
            misses += 1
            notes.remove(note)

    # Draw
    screen.fill(BG_COLOR)
    # Step zone
    pygame.draw.line(screen, (255,50,50), (0, TARGET_Y), (WIDTH, TARGET_Y), 2)

    # Draw hamster icons
    for note in notes:
        img = icons[note["key"]]
        rect = img.get_rect(center=(note["x"], note["y"]))
        screen.blit(img, rect)

    # HUD
    font = pygame.font.SysFont(None, 36)
    screen.blit(font.render(f"Score: {score}", True, (255,255,255)), (10, 10))
    screen.blit(font.render(f"Miss: {misses}", True, (255,100,100)), (10, 50))

    pygame.display.flip()

pygame.quit()
sys.exit()
