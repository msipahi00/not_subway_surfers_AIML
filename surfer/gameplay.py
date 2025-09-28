import sys, random
import pygame
from .config import (
    WIDTH, HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT, LANES, LANE_WIDTH,
    GROUND_Y, OBSTACLE_Y, MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL,
    DIFFICULTY_SCALING, MAX_OBSTACLE_SPEED, BASE_OBSTACLE_SPEED,
    NO_CLIP, make_fonts
)
from .core import compute_lane_centers, draw_lanes, spawn_obstacle

def game_loop(screen: pygame.Surface, clock: pygame.time.Clock):
    FONT, SMALL_FONT = make_fonts()

    player = pygame.Rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT)
    lane_centers = compute_lane_centers(WIDTH, LANES, LANE_WIDTH)
    cur_lane = 1
    player.centerx = lane_centers[cur_lane]
    player.centery = GROUND_Y

    obstacle_speed = BASE_OBSTACLE_SPEED
    obstacles = []
    obstacle_spawn_timer = 0.0
    next_spawn_time = random.uniform(MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL)

    dodge_time_needed = LANE_WIDTH / obstacle_speed
    lane_switch_time = dodge_time_needed * 0.7
    lane_switch_speed = LANE_WIDTH / lane_switch_time
    target_x = player.centerx

    score = 0
    time_survived = 0.0

    while True:
        dt = clock.tick(60) / 1000.0
        time_survived += dt
        score += int(time_survived * 2)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False, score
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT and cur_lane > 0:
                    cur_lane -= 1
                if e.key == pygame.K_RIGHT and cur_lane < LANES - 1:
                    cur_lane += 1
                target_x = lane_centers[cur_lane]

        obstacle_speed = min(obstacle_speed + ((time_survived ** 0.5) * DIFFICULTY_SCALING), MAX_OBSTACLE_SPEED)
        dodge_time_needed = LANE_WIDTH / obstacle_speed
        lane_switch_time = dodge_time_needed * 0.7
        lane_switch_speed = LANE_WIDTH / lane_switch_time
        diff_multiplier = obstacle_speed / BASE_OBSTACLE_SPEED
        cur_min_spawn = min(MIN_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL / diff_multiplier)
        cur_max_spawn = min(MAX_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL / diff_multiplier)

        # smooth move toward target lane center
        if abs(player.centerx - target_x) > 2:
            if player.centerx < target_x:
                player.centerx += lane_switch_speed * dt
                if player.centerx > target_x:
                    player.centerx = target_x
            else:
                player.centerx -= lane_switch_speed * dt
                if player.centerx < target_x:
                    player.centerx = target_x

        # spawn/move obstacles
        obstacle_spawn_timer += dt
        if obstacle_spawn_timer >= next_spawn_time:
            new_obstacle, lane_id = spawn_obstacle(lane_centers, LANE_WIDTH, OBSTACLE_Y)
            obstacles.append((new_obstacle, lane_id))
            obstacle_spawn_timer = 0.0
            next_spawn_time = random.uniform(cur_min_spawn, cur_max_spawn)

        obstacles_to_remove = []
        for i, (obstacle, lane_id) in enumerate(obstacles):
            obstacle.y += obstacle_speed * dt
            if obstacle.top > HEIGHT:
                obstacles_to_remove.append(i)
        for i in reversed(obstacles_to_remove):
            obstacles.pop(i)

        # collisions (if enabled)
        if not NO_CLIP:
            for obstacle, _ in obstacles:
                if player.colliderect(obstacle):
                    return True, score

        # render
        screen.fill((20, 20, 20))
        draw_lanes(screen, lane_centers, LANE_WIDTH, HEIGHT)
        pygame.draw.rect(screen, "RED", player)
        for obstacle, _ in obstacles:
            pygame.draw.rect(screen, "WHITE", obstacle)

        score_text = SMALL_FONT.render(f"Score: {score}", True, (220, 220, 220))
        diff_text  = SMALL_FONT.render(f"diff: {round(diff_multiplier, 2)}", True, (220, 220, 220))
        screen.blit(score_text, (WIDTH * 0.8 - score_text.get_width() // 2, HEIGHT * 0.1))
        screen.blit(diff_text,  (WIDTH * 0.8 - diff_text.get_width()  // 2, HEIGHT * 0.1 + 20))
        pygame.display.flip()

def game_over_screen(screen: pygame.Surface, clock: pygame.time.Clock, score: int):
    FONT, SMALL_FONT = make_fonts()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    return True
                elif e.key == pygame.K_ESCAPE:
                    return False
        screen.fill((40, 40, 40))
        game_over_text = FONT.render("GAME OVER", True, (255, 255, 255))
        restart_text   = SMALL_FONT.render("Press SPACE to restart", True, (200, 200, 200))
        quit_text      = SMALL_FONT.render("Press ESC to quit", True, (200, 200, 200))
        score_text     = SMALL_FONT.render(f"Score: {score}", True, (220, 220, 220))
        screen.blit(game_over_text, (screen.get_width()//2 - game_over_text.get_width()//2, screen.get_height()//2 - 100))
        screen.blit(restart_text,   (screen.get_width()//2 - restart_text.get_width()//2,   screen.get_height()//2 + 40))
        screen.blit(quit_text,      (screen.get_width()//2 - quit_text.get_width()//2,      screen.get_height()//2 + 10))
        screen.blit(score_text,     (screen.get_width()//2 - score_text.get_width()//2,     screen.get_height()//2 - 30))
        pygame.display.flip()
        clock.tick(60)

def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    while True:
        continue_game, score = game_loop(screen, clock)
        if not continue_game:
            break
        restart = game_over_screen(screen, clock, score)
        if not restart:
            break
    pygame.quit()
    sys.exit()
