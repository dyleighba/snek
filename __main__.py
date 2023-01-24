import pygame
from random import randint
import sys
from math import floor, log, sqrt
from time import time
from enum import Enum

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()

grid_block_pix_size = 16
game_speed_start = 6
game_speed_step = 0.5
color_bg_primary = (100, 100, 100)
color_bg_secondary = (80, 80, 80)
color_goal = (200, 200, 200)
color_snake_head = (200, 100, 100)
color_snake_body = (100, 200, 100)
color_text = (140, 140, 140)
color_text_bad = (255, 80, 80)
font_atlas = pygame.image.load("resources/font.png")
text_char_size = [3, 5]


class GameWorld:
    goal_locations: [[int, int], ]
    #snake: Snake
    width: int = 24
    height: int = 16
    #renderer: Renderer

    def __init__(self):
        self.renderer = Renderer()
        self.reset()

    def reset(self):
        self.goal_locations = []

    def is_food_at(self, x, y):
        for goal in self.goal_locations:
            if goal[0] == x and goal[1] == y:
                return True
        return False

    def place_food(self, x, y):
        if (0 <= x < self.width) and (0 <= y < self.height):
            coords = [x, y]
            if coords in self.goal_locations:
                raise ValueError("Goal already at coordinates")
            self.goal_locations.append([x, y])
        else:
            raise IndexError(f'Coordinates not in game world [{x}, {y}] gw: [{self.width}, {self.height}]')

    def remove_food(self, x, y):
        if (0 <= x < self.width) and (0 <= y < self.height):
            coords = [x, y]
            if coords in self.goal_locations:
                self.goal_locations.remove([x, y])
            else:
                raise ValueError("No goal already at coordinates")
        else:
            raise IndexError(f'Coordinates not in game world [{x}, {y}] gw: [{self.width}, {self.height}]')

    def draw(self):
        # background
        main_window.fill(color_bg_primary)
        if not "snake" in self.__dir__():
            self.renderer.draw_score(0)
        else:
            self.renderer.draw_score(self.snake.score)
        self.renderer.draw_vignette()
        # goal drawing
        for goal_location in self.goal_locations:
            x = goal_location[0] * grid_block_pix_size
            y = goal_location[1] * grid_block_pix_size
            main_window.fill((255, 255, 255), pygame.Rect(
                (x, y, grid_block_pix_size, grid_block_pix_size)
            ))


class Snake:
    class Direction(Enum):
        LEFT = 0
        RIGHT = 1
        UP = 2
        DOWN = 3

    class State(Enum):
        NORMAL = 0
        SCORED = 1
        JUST_DIED = 2
        GAME_OVER = 3

    goal_worth = 100
    goal_timer = 7.5
    last_score_time: float

    movement_queue: [Direction, ]
    body_segments: []
    score: int
    state: State
    game_world: GameWorld

    def __init__(self, game_world: GameWorld):
        self.game_world = game_world
        self.reset()

    def reset(self):
        self.movement_queue = [Snake.Direction.LEFT]
        self.body_segments = [
            [floor(self.game_world.width / 2), floor(self.game_world.height / 2)],
            [floor(self.game_world.width / 2), floor(self.game_world.height / 2) - 1]
        ]
        self.score = 0
        self.state = self.State.NORMAL
        self.last_score_time = time()

    def queue_movement(self, direction: Direction):
        if direction in self.Direction:
            self.movement_queue.append(direction)
        else:
            raise ValueError(f'"{direction}" is not a valid direction.')

    def add_score(self):
        cur_time = time()
        time_taken = ((self.goal_timer - min((cur_time - self.last_score_time), self.goal_timer)) / self.goal_timer)
        score_get = self.goal_worth * time_taken
        self.score += score_get
        self.last_score_time = cur_time

    def do_logic(self):
        if self.state == self.State.JUST_DIED:
            self.state = self.State.GAME_OVER
        if self.state == self.State.GAME_OVER:
            return
        self.state = self.State.NORMAL
        x, y = self.body_segments[-1]
        if self.movement_queue[0] == self.Direction.LEFT:
            x -= 1
        elif self.movement_queue[0] == self.Direction.RIGHT:
            x += 1
        elif self.movement_queue[0] == self.Direction.UP:
            y -= 1
        elif self.movement_queue[0] == self.Direction.DOWN:
            y += 1
        if len(self.movement_queue) > 1:
            self.movement_queue.pop(0)

        if x >= self.game_world.width:
            x = 0
        if x < 0:
            x = self.game_world.width - 1
        if y >= self.game_world.height:
            y = 0
        if y < 0:
            y = self.game_world.height - 1

        snake_head = [x, y]
        self.body_segments.append(snake_head)

        if self.game_world.is_food_at(x, y):
            self.game_world.remove_food(x, y)
            self.add_score()
            self.state = self.State.SCORED
        else:
            self.body_segments.pop(0)

        for i, part in enumerate(self.body_segments):
            if i is not (len(self.body_segments) - 1):
                if part == self.body_segments[-1]:
                    self.state = self.State.JUST_DIED

    def draw(self):
        surf = pygame.Surface((self.game_world.width, self.game_world.height), pygame.SRCALPHA)
        surf_pa = pygame.PixelArray(surf)
        for i, snek_part in enumerate(self.body_segments):
            fake_color = color_snake_body
            color_diff = (6 * (len(self.body_segments) - i))
            fake_color = (max(0, fake_color[0] - color_diff),
                          max(0, fake_color[1] - color_diff), max(0, fake_color[2] - color_diff))
            x = snek_part[0]
            y = snek_part[1]
            if i == (len(self.body_segments) - 1):
                surf_pa[x, y] = color_snake_head
            else:
                surf_pa[x, y] = fake_color
        del surf_pa
        main_window.blit(pygame.transform.scale(surf, (window_width, window_height)), (0, 0))


class Renderer:
    vignette_surf: pygame.Surface
    grid_surf: pygame.Surface

    def __init__(self):
        pass

    def draw_vignette(self):
        try:
            if not "vignette_surf" in self.__dir__() or self.vignette_surf is None or not isinstance(self.vignette_surf, pygame.Surface):
                raise NameError
        except NameError:
            self.vignette_surf = pygame.Surface(window_size, flags=pygame.SRCALPHA)
            gradient_length_percent = 0.75
            mid_x = floor(window_width / 2)
            mid_y = floor(window_height / 2)
            iterations = max(mid_x, mid_y)
            gradient_length = int(floor(iterations * gradient_length_percent))

            for x in range(gradient_length):
                opacity = min(255, floor(255 * (sqrt(log(((x / gradient_length) + 1) ** 2)))))
                opacity = 255 - opacity
                radius = floor(iterations * 1.3 - x)

                pygame.draw.circle(self.vignette_surf, (0, 0, 0, opacity), (mid_x, mid_y), radius)
        main_window.blit(self.vignette_surf, (0, 0))

    def draw_fail(self):
        fail_text = "FAIL!"
        surf = self.render_text(fail_text, color=color_text_bad)
        surf = pygame.transform.scale(surf, (
            (surf.get_width() * grid_block_pix_size), floor(surf.get_height() * grid_block_pix_size)))

        box_surf = pygame.Surface(window_size)
        box_surf.set_alpha(128)
        box_surf.fill(color_bg_secondary)
        main_window.blit(box_surf, (0, 0))

        x = (floor(GameWorld.width / 2) - floor(len(fail_text) * 2)) * grid_block_pix_size
        y = (floor(GameWorld.height / 2) - 3) * grid_block_pix_size
        main_window.blit(surf, (x, y))

        surf2 = self.render_text("R TO REPLAY", color=color_text_bad)
        main_window.blit(surf2, (grid_block_pix_size, grid_block_pix_size))

    def draw_score(self, score):
        surf = self.render_text("%05d" % score)
        x = 1 * grid_block_pix_size
        y = ((GameWorld.height - 3) * grid_block_pix_size) - (grid_block_pix_size / 2)
        surf = pygame.transform.scale(surf, (
            floor((surf.get_width() * grid_block_pix_size) / 2), floor((surf.get_height() * grid_block_pix_size) / 2)))
        main_window.blit(surf, (x, y))

    def draw_grid(self):
        try:
            if self.grid_surf is None or not isinstance(self.grid_surf, pygame.Surface):
                raise NameError
        except NameError:
            self.grid_surf = pygame.Surface(window_size, flags=pygame.SRCALPHA)
            for x in range(GameWorld.width):
                x_pos = floor(x * grid_block_pix_size)
                pygame.draw.line(self.grid_surf, color_bg_secondary, (x_pos, 0),
                                 (x_pos, window_height))
            for y in range(GameWorld.height):
                y_pos = floor(y * grid_block_pix_size)
                pygame.draw.line(self.grid_surf, color_bg_secondary, (0, y_pos),
                                 (window_width, floor(y * grid_block_pix_size)))
        main_window.blit(self.grid_surf, (0, 0))

    def render_text(self, text, color=color_text):
        text = text.upper()
        surf = pygame.Surface((4 * len(text), 5), flags=pygame.SRCALPHA)
        for i, c in enumerate(text):
            surf.blit(font_atlas, (4 * i, 0), pygame.Rect(4 * ord(c), 0, 4, 5))
        surf_pa = pygame.PixelArray(surf)
        surf_pa.replace((0, 0, 0), color)
        del surf_pa
        return surf


class Sounds:
    def __init__(self):
        pygame.mixer.music.load("resources/bg.ogg")
        self.collect = pygame.mixer.Sound("resources/collect.ogg")
        self.death = pygame.mixer.Sound("resources/death.ogg")

    def start_bgm(self):
        pygame.mixer.music.rewind()
        pygame.mixer.music.play(loops=-1)

    def stop_bgm(self):
        pygame.mixer.music.stop()


class SnakeGame:
    clock: pygame.time.Clock

    game_speed = game_speed_start
    game_world: GameWorld
    snake: Snake

    game_over: bool

    movement_binding = {
        pygame.K_LEFT: Snake.Direction.LEFT,
        pygame.K_RIGHT: Snake.Direction.RIGHT,
        pygame.K_UP: Snake.Direction.UP,
        pygame.K_DOWN: Snake.Direction.DOWN
    }

    def __init__(self):
        self.game_world = GameWorld()
        self.snake = Snake(self.game_world)
        self.game_world.snake = self.snake
        self.setup_pygame()
        self.reset()

    def setup_pygame(self):
        self.clock = pygame.time.Clock()
        pygame.mixer.music.load("resources/bg.ogg")
        self.sound_collect = pygame.mixer.Sound("resources/collect.ogg")
        self.sound_death = pygame.mixer.Sound("resources/death.ogg")

    def start_music(self):
        pygame.mixer.music.rewind()
        pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        pygame.mixer.music.stop()

    def reset(self):
        self.game_world.reset()
        self.snake.reset()
        self.game_speed = game_speed_start
        self.game_over = False
        self.place_food()
        self.start_music()

    def run_game_cycle(self):
        self.clock.tick(self.game_speed)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in self.movement_binding:
                    self.snake.queue_movement(self.movement_binding[event.key])
                elif event.key == pygame.K_END:
                    self.game_over = True
                elif event.key == pygame.K_r:
                    self.reset()
            elif event.type == pygame.QUIT:
                sys.exit()
        if not self.game_over:
            self.snake.do_logic()

    def place_food(self):
        while True:
            location = [randint(1, self.game_world.width) - 1, randint(1, self.game_world.height) - 1]
            if location not in self.snake.body_segments:
                if location not in self.game_world.goal_locations:
                    self.game_world.place_food(location[0], location[1])
                    break

    def draw(self):
        self.game_world.draw()
        self.snake.draw()

game = SnakeGame()
window_size = window_width, window_height = (GameWorld.width * grid_block_pix_size,
                                             GameWorld.height * grid_block_pix_size)
main_window = pygame.display.set_mode(window_size)
renderer = Renderer()
while True:
    # Logic
    game.run_game_cycle()
    # Rendering
    game.draw()
    if game.snake.state == Snake.State.SCORED:
        game.sound_collect.play()
        game.place_food()
    if game.snake.state == Snake.State.JUST_DIED:
        game.stop_music()
    if game.snake.state == Snake.State.GAME_OVER:
        renderer.draw_fail()
        renderer.draw_score(game.snake.score)
    pygame.display.flip()
