import time
from collections import defaultdict

click_history = defaultdict(list)
last_action = {}

MAX_CLICKS_PER_MINUTE = 30
MIN_ACTION_INTERVAL = 0.3


def is_spam(user_id):
    now = time.time()
    if user_id in last_action:
        if now - last_action[user_id] < MIN_ACTION_INTERVAL:
            return True
    last_action[user_id] = now
    h = click_history[user_id]
    h.append(now)
    click_history[user_id] = [t for t in h if now - t < 60]
    return len(click_history[user_id]) > MAX_CLICKS_PER_MINUTE
