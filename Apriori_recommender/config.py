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

# Model hyperparameters
MODEL_CONFIG = {
    'min_support': 0.05,
    'min_lift': 1.0,
    'random_state': 42
} 

# Application settings
DEFAULT_RECOMMENDATIONS = 5

#a9al men 0.05 
# Performance monitoring settings
Minimum_CTR = 0.05