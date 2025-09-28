# surfer/env.py
import random, pygame
from .config import (
    WIDTH, HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT, LANES, LANE_WIDTH,
    GROUND_Y, OBSTACLE_Y, MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL,
    DIFFICULTY_SCALING, MAX_OBSTACLE_SPEED, BASE_OBSTACLE_SPEED
)
from .core import compute_lane_centers, spawn_obstacle

OBS_LOOKAHEAD = 1  # exactly one obstacle per lane
FAR_TTC_SEC = 5.0  # anything >= this is considered "far"

def extract_state(player, cur_lane, obstacles, obstacle_speed):
    """
    Observation (length 6):
      [ lane_one_hot(3), lane0_ttc, lane1_ttc, lane2_ttc ]
    - TTC is time (sec) until obstacle bottom reaches player top.
    - Normalize to [0,1] by clipping to [0, FAR_TTC_SEC] then dividing by FAR_TTC_SEC.
    - If a lane has no upcoming obstacle, its TTC = 1.0 (far).
    """
    # one-hot lane
    lane_oh = [0, 0, 0]
    lane_oh[cur_lane] = 1

    # find the *closest* upcoming obstacle per lane
    nearest_ttc = [FAR_TTC_SEC] * LANES
    for obs, lane_id in obstacles:
        if obs.bottom >= player.top:
            continue  # already passed or overlapping
        dy = player.top - obs.bottom
        t = dy / max(obstacle_speed, 1e-6)
        if t >= 0 and t < nearest_ttc[lane_id]:
            nearest_ttc[lane_id] = t

    # normalize to [0,1]
    ttcs_norm = [min(FAR_TTC_SEC, t) / FAR_TTC_SEC for t in nearest_ttc]
    return lane_oh + ttcs_norm  # length = 3 + 3 = 6

class SurferEnv:
    """Actions: 0=stay, 1=left, 2=right"""
    def __init__(self, seed: int = 0, render: bool = False, target_fps: int = 60):
        self.rand = random.Random(seed)
        self.render_enabled = render
        self.target_fps = target_fps

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) if render else pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.lane_centers = compute_lane_centers(WIDTH, LANES, LANE_WIDTH)
        self.player = pygame.Rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.reset()

    def reset(self):
        self.obstacle_speed = BASE_OBSTACLE_SPEED
        self.obstacles = []
        self.obstacle_spawn_timer = 0.0
        self.next_spawn_time = self.rand.uniform(MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL)
        self.cur_lane = 1
        self.player.centerx = self.lane_centers[self.cur_lane]
        self.player.centery = GROUND_Y
        self.time_survived = 0.0
        self.score = 0
        self.done = False
        return self._obs()

    def step(self, action: int):
        if self.done:
            return self._obs(), 0.0, True, {}

        dt = 1.0 / self.target_fps

        prev_lane = self.cur_lane
        if action == 1 and self.cur_lane > 0:
            self.cur_lane -= 1
        elif action == 2 and self.cur_lane < LANES - 1:
            self.cur_lane += 1
        self.player.centerx = self.lane_centers[self.cur_lane]

        # difficulty & spawns
        self.time_survived += dt
        self.score += int(self.time_survived * 2)
        self.obstacle_speed = min(self.obstacle_speed + ((self.time_survived ** 0.5) * DIFFICULTY_SCALING), MAX_OBSTACLE_SPEED)

        diff_mult = self.obstacle_speed / BASE_OBSTACLE_SPEED
        cur_min_spawn = min(MIN_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL / diff_mult)
        cur_max_spawn = min(MAX_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL / diff_mult)

        self.obstacle_spawn_timer += dt
        if self.obstacle_spawn_timer >= self.next_spawn_time:
            new_obstacle, lane_id = spawn_obstacle(self.lane_centers, LANE_WIDTH, OBSTACLE_Y)
            self.obstacles.append((new_obstacle, lane_id))
            self.obstacle_spawn_timer = 0.0
            self.next_spawn_time = self.rand.uniform(cur_min_spawn, cur_max_spawn)

        # move obstacles & prune
        rm = []
        for i, (obs, _) in enumerate(self.obstacles):
            obs.y += self.obstacle_speed * dt
            if obs.top > HEIGHT:
                rm.append(i)
        for i in reversed(rm):
            self.obstacles.pop(i)

        # collision
        collided = any(self.player.colliderect(obs) for obs, _ in self.obstacles)

        # reward shaping (simple)
        reward = 1.0
        if self.cur_lane != prev_lane:
            reward -= 0.01
        if collided:
            reward -= 100.0
            self.done = True

        if self.render_enabled:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    # End the episode cleanly
                    try:
                        if pygame.display.get_surface() is not None:
                            pygame.display.quit()
                    finally:
                        self.done = True
                    return self._obs(), 0.0, True, {"score": self.score, "time": self.time_survived}
            self.screen.fill((20,20,20))
            for obs, _ in self.obstacles:
                pygame.draw.rect(self.screen, "WHITE", obs)
            pygame.draw.rect(self.screen, "RED", self.player)
            pygame.display.flip()
            self.clock.tick(self.target_fps)

        return self._obs(), reward, self.done, {"score": self.score, "time": self.time_survived}

    def _obs(self):
        return extract_state(self.player, self.cur_lane, self.obstacles, self.obstacle_speed)

    def close(self):
        pygame.quit()
