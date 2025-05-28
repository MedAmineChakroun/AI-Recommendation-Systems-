"""
User similarity calculations for collaborative filtering
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def calculate_user_similarity_matrix(user_item_matrix):
    """Calculate cosine similarity between user vectors"""
    return cosine_similarity(user_item_matrix)

def get_similar_users(user_id, user_item_matrix, n=10):
    """Find n most similar users to the target user"""
    try:
        user_idx = list(user_item_matrix.index).index(user_id)
    except ValueError:
        return []

    # Calculate similarity matrix
    similarity_matrix = calculate_user_similarity_matrix(user_item_matrix)
    
    # Get similarities for target user
    user_similarities = similarity_matrix[user_idx]
    
    # Get indices of most similar users (excluding self)
    similar_user_indices = np.argsort(user_similarities)[::-1][1:n+1]
    
    # Convert to list of (user_id, similarity_score) tuples
    similar_users = [
        (user_item_matrix.index[idx], user_similarities[idx])
        for idx in similar_user_indices
    ]
    
    return similar_users

def get_neighborhood_scores(item_quantities):
    """Calculate scores for items based on user neighborhood"""
    scores = {}
    for item_id, user_data in item_quantities.items():
        weighted_sum = 0
        similarity_sum = 0
        
        for (_, sim_score), rating in user_data.items():
            weighted_sum += sim_score * rating
            similarity_sum += sim_score
            
        if similarity_sum > 0:
            scores[item_id] = weighted_sum / similarity_sum
    
    return scores