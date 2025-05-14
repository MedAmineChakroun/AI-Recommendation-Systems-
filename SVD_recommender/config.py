"""
Configuration settings for the recommendation system
"""

# Database settings
DB_CONFIG = {
    'driver': '{SQL Server}',
    'server': 'DESKTOP-QD57IO2\\SQLEXPRESS',
    'database': 'B2C_DB',
    'trusted_connection': 'yes'
}

# Redis cache settings
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6378,
    'db': 0,
    'decode_responses': True
}
CACHE_TTL = 1800  # Cache expiry time in seconds (30 minutes)

# Model hyperparameters
MODEL_CONFIG = {
    'n_factors': 250,
    'n_epochs': 20,
    'lr_all': 0.005,
    'reg_all': 0.02,
    'random_state': 69
}

# Application settings
DEFAULT_RECOMMENDATIONS = 5