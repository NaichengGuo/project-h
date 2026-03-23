# PPO constants

# PPO hyperparameters
CLIP_EPSILON = 0.2
VALUE_LOSS_COEF = 0.5
ENTROPY_COEF = 0.01
MAX_GRAD_NORM = 0.5
GAE_LAMBDA = 0.95
GAMMA = 0.99

# Model keys
ACTOR_KEY = 'actor'
CRITIC_KEY = 'critic'
OPTIMIZER_KEY = 'optimizer'

# Training constants
BATCH_SIZE = 64
EPOCH_NUM = 10

# User statics info size (same as DQN for compatibility)
USER_STATICS_INFO_SIZE = 6