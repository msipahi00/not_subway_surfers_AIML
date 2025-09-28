# scripts/evaluate.py
from statistics import mean, median
from surfer.env import SurferEnv
from agents.heuristic import heuristic_policy

def evaluate(policy_fn, episodes=30, render=False, seed=0):
    env = SurferEnv(render=render, seed=seed)
    scores = []
    for _ in range(episodes):
        obs = env.reset()
        done = False
        while not done:
            action = policy_fn(obs)
            obs, reward, done, info = env.step(action)
        scores.append(info["score"])
    env.close()
    print(f"episodes={episodes} mean={mean(scores):.1f} median={median(scores)} "
          f"best={max(scores)} worst={min(scores)}")
    return scores

if __name__ == "__main__":
    evaluate(heuristic_policy, episodes=30, render=True, seed=0)
