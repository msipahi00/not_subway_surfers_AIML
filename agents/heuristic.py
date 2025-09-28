# agents/heuristic.py

# All TTCs are normalized 0..1 where 1.0 is "far" (>= ~5s)
MIN_SAFE_TTC   = 0.55   # destination must be at least this safe
SAFETY_MARGIN  = 0.10   # destination must beat current by this much
CRASH_TTC      = 0.20   # panic threshold: if current is about to crash, pick the best available anyway

def heuristic_policy(obs):
    """
    obs: [onehot(3), lane0_ttc, lane1_ttc, lane2_ttc]
    returns: 0=stay, 1=left, 2=right
    """
    lane_oh = obs[:3]
    ttcs = obs[3:]
    cur_lane = lane_oh.index(1)
    cur_ttc = ttcs[cur_lane]

    # 1) If we are already safe enough, don't move
    if cur_ttc >= MIN_SAFE_TTC:
        return 0

    # 2) Consider only lanes that are meaningfully safer and meet the minimum safety bar
    candidates = [(i, t) for i, t in enumerate(ttcs) if i != cur_lane and t >= max(cur_ttc + SAFETY_MARGIN, MIN_SAFE_TTC)]
    if candidates:
        # choose the lane with the largest TTC
        best_lane = max(candidates, key=lambda x: x[1])[0]
        if best_lane < cur_lane: return 1
        if best_lane > cur_lane: return 2
        return 0

    # 3) Panic logic: if collision is imminent, pick the best lane even if it's not great
    if cur_ttc < CRASH_TTC:
        # pick the lane with the largest TTC (could still be small, but it's the least bad)
        best_lane = max([0,1,2], key=lambda i: ttcs[i])
        if best_lane < cur_lane: return 1
        if best_lane > cur_lane: return 2

    # 4) Otherwise, stay and reassess next step
    return 0
