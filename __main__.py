import pygame
from random import randint
import sys
from math import floor, log, sqrt
from time import time

grid_block_pix_size = 16
grid_width = 24
grid_height = 16
game_speed_start = 6
game_speed_step = 0.5
color_bg_primary = (100, 100, 100)
color_bg_secondary = (80, 80, 80)
color_goal = (200, 200, 200)
color_snake_head = (200, 100, 100)
color_snake_body = (100, 200, 100)
color_text = (140, 140, 140)
color_text_bad = (255, 80, 80)
goal_worth = 100
goal_timer = 7.5

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()
clock = pygame.time.Clock()
window_size = window_width, window_height = (grid_width * grid_block_pix_size,
                                             grid_height * grid_block_pix_size)
pygame.mixer.music.load("resources/bg.ogg")
sound_collect = pygame.mixer.Sound("resources/collect.ogg")
sound_death = pygame.mixer.Sound("resources/death.ogg")

scr = pygame.display.set_mode(window_size)
font_atlas = pygame.image.load("resources/font.png")

text_char_size = [3, 5]


def render_text(text, color=color_text):
    text = text.upper()
    surf = pygame.Surface((4 * len(text), 5), flags=pygame.SRCALPHA)
    for i, c in enumerate(text):
        surf.blit(font_atlas, (4 * i, 0), pygame.Rect(4 * ord(c), 0, 4, 5))
    surf_pa = pygame.PixelArray(surf)
    surf_pa.replace((0, 0, 0), color)
    del surf_pa
    return surf


def draw_bg():
    scr.fill(color_bg_primary)


def draw_grid():
    global grid_surf
    try:
        if grid_surf is None or not isinstance(grid_surf, pygame.Surface):
            raise NameError
    except NameError:
        grid_surf = pygame.Surface(window_size, flags=pygame.SRCALPHA)
        for x in range(grid_width):
            x_pos = floor(x * grid_block_pix_size)
            pygame.draw.line(grid_surf, color_bg_secondary, (x_pos, 0),
                             (x_pos, window_height))
        for y in range(grid_width):
            y_pos = floor(y * grid_block_pix_size)
            pygame.draw.line(grid_surf, color_bg_secondary, (0, y_pos),
                             (window_width, floor(y * grid_block_pix_size)))
    scr.blit(grid_surf, (0, 0))


def draw_score(score):
    surf = render_text("%05d" % score)
    x = 1 * grid_block_pix_size
    y = ((grid_height - 3) * grid_block_pix_size) - (grid_block_pix_size / 2)
    surf = pygame.transform.scale(surf, (
    floor((surf.get_width() * grid_block_pix_size) / 2), floor((surf.get_height() * grid_block_pix_size) / 2)))
    scr.blit(surf, (x, y))


def draw_snake(snake_parts):
    surf = pygame.Surface((grid_width, grid_height), pygame.SRCALPHA)
    surf_pa = pygame.PixelArray(surf)
    for i, snek_part in enumerate(snake_parts):
        fake_color = color_snake_body
        color_diff = (6 * (len(snake_parts) - i))
        fake_color = (max(0, fake_color[0] - color_diff),
                      max(0, fake_color[1] - color_diff), max(0, fake_color[2] - color_diff))
        x = snek_part[0]
        y = snek_part[1]
        if i == (len(snake_parts) - 1):
            surf_pa[x, y] = color_snake_head
        else:
            surf_pa[x, y] = fake_color
    del surf_pa
    scr.blit(pygame.transform.scale(surf, (window_width, window_height)), (0, 0))


def draw_goal(goal_location):
    x = goal_location[0] * grid_block_pix_size
    y = goal_location[1] * grid_block_pix_size
    scr.fill((255, 255, 255), pygame.Rect(
        (x, y, grid_block_pix_size, grid_block_pix_size)
    ))


def draw_fail():
    fail_text = "FAIL!"
    surf = render_text(fail_text, color=color_text_bad)
    surf = pygame.transform.scale(surf, (
    (surf.get_width() * grid_block_pix_size), floor(surf.get_height() * grid_block_pix_size)))

    box_surf = pygame.Surface(window_size)
    box_surf.set_alpha(128)
    box_surf.fill(color_bg_secondary)
    scr.blit(box_surf, (0, 0))

    x = (floor(grid_width / 2) - floor(len(fail_text) * 2)) * grid_block_pix_size
    y = (floor(grid_height / 2) - 3) * grid_block_pix_size
    scr.blit(surf, (x, y))

    surf2 = render_text("R TO REPLAY", color=color_text_bad)
    scr.blit(surf2, (grid_block_pix_size, grid_block_pix_size))


def start_music():
    pygame.mixer.music.rewind()
    pygame.mixer.music.play(loops=-1)


def stop_music():
    sound_death.play()
    pygame.mixer.music.stop()

def draw_vignette():
    global vignette_surf
    try:
        if vignette_surf is None or not isinstance(vignette_surf, pygame.Surface):
            raise NameError
    except NameError:
        vignette_surf = pygame.Surface(window_size, flags=pygame.SRCALPHA)
        gradient_length_percent = 0.75
        mid_x = floor(window_width / 2)
        mid_y = floor(window_height / 2)
        iterations = max(mid_x, mid_y)
        gradient_length = int(floor(iterations * gradient_length_percent))

        for x in range(gradient_length):
            opacity = min(255, floor(255 * (sqrt(log(((x / gradient_length) + 1) ** 2)))))
            opacity = 255 - opacity
            radius = floor(iterations * 1.3 - x)

            pygame.draw.circle(vignette_surf, (0, 0, 0, opacity), (mid_x, mid_y), radius)
    scr.blit(vignette_surf, (0, 0))


class SnakeGame:
    score = 0
    fail = False
    fail_first = False
    snake_heading = ["RIGHT"]
    snake_parts = []
    game_speed = game_speed_start
    goal_location = [0, 0]
    goal_last = 0

    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.fail = False
        self.fail_first = False
        self.snake_heading = ["RIGHT"]
        self.snake_parts = [
            [floor(grid_width / 2), floor(grid_height / 2)],
            [floor(grid_width / 2), floor(grid_height / 2) - 1]
        ]
        self.game_speed = game_speed_start
        self.place_food()
        self.goal_last = time()
        start_music()
    def run_game_cycle(self):
        global fail
        global fail_first
        clock.tick(self.game_speed)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if self.snake_heading[len(self.snake_heading) - 1] != "RIGHT":
                        self.snake_heading.append("LEFT")
                if event.key == pygame.K_RIGHT:
                    if self.snake_heading[len(self.snake_heading) - 1] != "LEFT":
                        self.snake_heading.append("RIGHT")
                if event.key == pygame.K_UP:
                    if self.snake_heading[len(self.snake_heading) - 1] != "DOWN":
                        self.snake_heading.append("UP")
                if event.key == pygame.K_DOWN:
                    if self.snake_heading[len(self.snake_heading) - 1] != "UP":
                        self.snake_heading.append("DOWN")
                if event.key == pygame.K_END:
                    self.fail = True
                    self.fail_first = True
                if event.key == pygame.K_r:
                    self.reset()
            elif event.type == pygame.QUIT:
                sys.exit()
        self.snake_logic()

    def place_food(self):
        while True:
            self.goal_location = [randint(1, grid_width) - 1, randint(1, grid_height) - 1]
            if self.goal_location not in self.snake_parts:
                break
        self.goal_last = time()

    def goal_logic(self):
        if self.snake_parts[-1] == self.goal_location:
            self.game_speed += game_speed_step
            cur_time = time()
            time_taken = ((goal_timer - min((cur_time - self.goal_last), goal_timer)) / goal_timer)
            score_get = goal_worth * time_taken
            self.score += score_get
            self.place_food()
            self.goal_last = cur_time
            sound_collect.play()
            return True
        return False

    def snake_logic(self):
        # Used to freeze the game after game over.
        if self.fail:
            return

        x, y = self.snake_parts[len(self.snake_parts) - 1]
        if self.snake_heading[0] == "LEFT": x -= 1
        if self.snake_heading[0] == "RIGHT": x += 1
        if self.snake_heading[0] == "UP": y -= 1
        if self.snake_heading[0] == "DOWN": y += 1
        if len(self.snake_heading) > 1:
            self.snake_heading.pop(0)

        if x >= grid_width:
            x = 0
        if x < 0:
            x = grid_width - 1
        if y >= grid_height:
            y = 0
        if y < 0:
            y = grid_height - 1

        snake_head = [x, y]
        self.snake_parts.append(snake_head)

        if not self.goal_logic():
            self.snake_parts.pop(0)

        for i, part in enumerate(self.snake_parts):
            if i is not (len(self.snake_parts) - 1):
                if part == self.snake_parts[-1]:
                    self.fail = True
                    self.fail_first = True


game = SnakeGame()
while True:
    # Logic
    game.run_game_cycle()
    # Rendering
    draw_bg()
    draw_score(game.score)
    draw_vignette()
    draw_snake(game.snake_parts)
    draw_goal(game.goal_location)
    if game.fail_first:
        stop_music()
        game.fail_first = False
    if game.fail:
        draw_fail()
        draw_score(game.score)
    pygame.display.flip()
