# scripts/eval_dqn.py
import torch
from statistics import mean, median
from surfer.env import SurferEnv
from agents.dqn import QNetwork

def eval_dqn(model_path="dqn_agent.pt", episodes=50, render=False, seed=0):
    env = SurferEnv(render=render, target_fps=60, seed=seed)
    obs_dim = len(env.reset())
    n_actions = 3

    model = QNetwork(obs_dim, n_actions)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    scores = []
    try:
        for _ in range(episodes):
            obs = env.reset()
            done = False
            while not done:
                with torch.no_grad():
                    a = model(torch.tensor(obs, dtype=torch.float32)).argmax().item()
                obs, r, done, info = env.step(a)
            scores.append(info["score"])
    finally:
        env.close()

    print(f"episodes={episodes} mean={mean(scores):.1f} median={median(scores)} "
          f"best={max(scores)} worst={min(scores)}")

if __name__ == "__main__":
    eval_dqn(model_path="dqn_agent.pt", episodes=20, render=False)
