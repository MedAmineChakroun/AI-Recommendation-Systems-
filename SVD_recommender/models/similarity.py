"""
User similarity calculations for collaborative filtering
"""
import numpy as np

def get_similar_users(user_id, user_item_matrix, n=5):
    """Find users with similar purchase patterns with increased emphasis on similarity over quantity"""
    if user_id not in user_item_matrix.index:
        return []
    
    # Calculate cosine similarity between users
    user_similarities = {}
    user_vector = user_item_matrix.loc[user_id].values
    
    for other_user in user_item_matrix.index:
        if other_user != user_id:
            other_vector = user_item_matrix.loc[other_user].values
            
            # Calculate cosine similarity (with epsilon to avoid division by zero)
            epsilon = 1e-8
            similarity = np.dot(user_vector, other_vector) / (max(np.linalg.norm(user_vector), epsilon) * max(np.linalg.norm(other_vector), epsilon))
            
            # Count common non-zero elements (common purchased items)
            user_items = set(np.where(user_vector > 0)[0])
            other_items = set(np.where(other_vector > 0)[0])
            common_items = len(user_items.intersection(other_items))
            total_items = len(user_items.union(other_items))
            
            # Calculate Jaccard similarity (common items / total unique items)
            jaccard_sim = common_items / max(total_items, 1)
            
            # Pearson correlation for rating patterns
            user_mean = np.mean([user_vector[i] for i in user_items]) if user_items else 0
            other_mean = np.mean([other_vector[i] for i in other_items]) if other_items else 0
            
            numerator = 0
            user_variance = 0
            other_variance = 0
            
            # Calculate Pearson correlation
            for i in user_items.intersection(other_items):
                user_centered = user_vector[i] - user_mean
                other_centered = other_vector[i] - other_mean
                numerator += user_centered * other_centered
                user_variance += user_centered ** 2
                other_variance += other_centered ** 2
            
            # Calculate correlation with handling for zero division
            if user_variance > 0 and other_variance > 0:
                pearson = numerator / (np.sqrt(user_variance) * np.sqrt(other_variance))
            else:
                pearson = 0
            
            # Use a weighted combination with HIGHER weight on similarity measures and LOWER on quantity
            combined_sim = (0.4 * similarity) + (0.4 * pearson) + (0.2 * jaccard_sim)
            
            # Penalize users with very few ratings in common to avoid spurious matches
            min_common_threshold = 2
            if common_items < min_common_threshold:
                combined_sim *= (common_items / min_common_threshold)
            
            if not np.isnan(combined_sim):
                user_similarities[other_user] = combined_sim
    
    # Sort by similarity and return top n
    similar_users = sorted(user_similarities.items(), key=lambda x: x[1], reverse=True)
    return similar_users[:n]