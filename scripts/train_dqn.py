# scripts/train_dqn.py
import math, random, os
from statistics import mean
import numpy as np
import torch, torch.nn as nn, torch.optim as optim

from surfer.env import SurferEnv
from agents.dqn import ReplayBuffer, QNetwork

def set_seed(seed=0):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

def train_dqn(
    episodes=500,
    batch_size=64,
    gamma=0.99,
    lr=1e-3,
    epsilon_start=1.0,
    epsilon_end=0.05,
    epsilon_decay_steps=20_000,   # steps, not episodes
    target_update_steps=1000,
    replay_capacity=100_000,
    warmup_steps=2000,
    grad_clip_norm=5.0,
    render=False,
    seed=0,
    save_path="dqn_agent.pt",
):
    set_seed(seed)
    env = SurferEnv(render=render, target_fps=60, seed=seed)
    obs = env.reset()
    obs_dim = len(obs)        # should be 6 in your 1-lookahead setup
    n_actions = 3

    device = torch.device("cpu")

    qnet = QNetwork(obs_dim, n_actions).to(device)
    target = QNetwork(obs_dim, n_actions).to(device)
    target.load_state_dict(qnet.state_dict())
    target.eval()

    optimizer = optim.Adam(qnet.parameters(), lr=lr)
    loss_fn = nn.SmoothL1Loss()  # Huber

    buffer = ReplayBuffer(capacity=replay_capacity)

    epsilon = epsilon_start
    step = 0
    ep_rewards = []
    best_mean = -1e9

    try:
        for ep in range(1, episodes + 1):
            obs = env.reset()
            done = False
            ep_reward = 0.0

            while not done:
                step += 1

                # Epsilon schedule (exponential-ish decay by steps)
                eps_frac = min(1.0, step / max(1, epsilon_decay_steps))
                epsilon = epsilon_end + (epsilon_start - epsilon_end) * math.exp(-3.0 * eps_frac)  # smooth curve

                # Act
                if random.random() < epsilon:
                    action = random.randrange(n_actions)
                else:
                    with torch.no_grad():
                        q = qnet(torch.tensor(obs, dtype=torch.float32, device=device))
                        action = int(torch.argmax(q).item())

                next_obs, reward, done, info = env.step(action)
                buffer.push(obs, action, reward, next_obs, done)
                ep_reward += reward
                obs = next_obs

                # Learn
                if len(buffer) >= max(batch_size, warmup_steps):
                    b_obs, b_act, b_rew, b_next, b_done = buffer.sample(batch_size)
                    b_obs = b_obs.to(device); b_act = b_act.to(device)
                    b_rew = b_rew.to(device); b_next = b_next.to(device); b_done = b_done.to(device)

                    # Q(s,a)
                    q_sa = qnet(b_obs).gather(1, b_act.unsqueeze(1)).squeeze(1)

                    # Double DQN target
                    with torch.no_grad():
                        next_actions = qnet(b_next).argmax(dim=1, keepdim=True)
                        next_q = target(b_next).gather(1, next_actions).squeeze(1)
                        target_q = b_rew + gamma * next_q * (1.0 - b_done)

                    loss = loss_fn(q_sa, target_q)
                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(qnet.parameters(), grad_clip_norm)
                    optimizer.step()

                # Target net sync
                if step % target_update_steps == 0:
                    target.load_state_dict(qnet.state_dict())

            ep_rewards.append(ep_reward)
            recent = ep_rewards[-20:] if len(ep_rewards) >= 20 else ep_rewards
            print(f"Ep {ep:4d} | reward {ep_reward:7.1f} | eps {epsilon:0.2f} | avg20 {mean(recent):7.1f}")

            # Save best
            if len(ep_rewards) >= 20:
                avg20 = mean(ep_rewards[-20:])
                if avg20 > best_mean:
                    best_mean = avg20
                    torch.save(qnet.state_dict(), save_path)
                    # print(f"Saved best model to {save_path} (avg20={best_mean:.1f})")
    finally:
        env.close()

    # Final save
    if not os.path.exists(save_path):
        torch.save(qnet.state_dict(), save_path)
    print(f"Training done. Model saved at {save_path}")

if __name__ == "__main__":
    # Fast sanity run: drop episodes to e.g. 100 first, then increase.
    train_dqn(episodes=500, render=False, seed=0)
