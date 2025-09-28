import random, pygame
from .config import WIDTH, HEIGHT, LANES, LANE_WIDTH

def compute_lane_centers(screen_width:int, num_lanes:int, lane_width:int):
    """Computes the x coordinates for lanes given total width and lane parameters"""
    margin = (screen_width - (num_lanes * lane_width)) // 2
    return [(margin + lane_width*i + lane_width//2) for i in range(num_lanes)]

def draw_lanes(screen: pygame.Surface, centers: list, lane_width: int, screen_height: int):
    """Draws the lanes and separates by lines"""
    for idx, center in enumerate(centers):
        l_bound = center - lane_width//2
        lane = pygame.Rect(l_bound, 0, lane_width, screen_height)
        pygame.draw.rect(screen, "ORANGE", lane)
        if idx !=0:
            pygame.draw.line(screen, "GREEN", (l_bound, 0), (l_bound, screen_height), width=2)


def spawn_obstacle(lane_centers: list, lane_width: int, top_y: int, length: int = random.randint(50, 200)):
    """Generates and returns a pygame rectangle object in a random lane"""
    lane_id = random.randrange(len(lane_centers))
    width, length = int(lane_width*0.7), length
    obstacle = pygame.Rect(0,0,width,length)
    obstacle.centerx = lane_centers[lane_id]
    obstacle.y = top_y
    return obstacle, lane_id