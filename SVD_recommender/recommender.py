"""
Core recommendation system logic
"""
import numpy as np
from collections import defaultdict
import pandas as pd

from models.similarity import get_similar_users
from models.svd_model import get_svd_predictions

class RecommenderService:
    def __init__(self, df, svd_model):
        """Initialize the recommender service with data and model"""
        self.df = df
        self.svd_model = svd_model
        self.user_item_matrix = df.pivot_table(index='user_id', columns='item_id', values='quantity', fill_value=0)
    
    def get_popular_items(self, n=10):
        """Get the most popular items based on frequency and average purchase quantity"""
        # Calculate item popularity as a function of frequency and average quantity
        item_stats = self.df.groupby('item_id').agg(
            count=('quantity', 'count'),
            avg_quantity=('quantity', 'mean')
        ).reset_index()
        
        # Normalize the counts and quantities
        max_count = item_stats['count'].max()
        item_stats['norm_count'] = item_stats['count'] / max_count
        
        # Calculate popularity score (weighted combination of frequency and quantity)
        item_stats['popularity'] = (0.7 * item_stats['norm_count']) + (0.3 * item_stats['avg_quantity'] / 5.0)
        
        # Sort by popularity score and return top n
        popular_items = item_stats.sort_values('popularity', ascending=False).head(n)
        return list(zip(popular_items['item_id'], popular_items['popularity']))
    
    def get_diverse_recommendations(self, n=5):
        """Get a diverse set of recommendations using item categories/prefixes"""
        # Get popular items
        popular_items = self.get_popular_items(n=n*3)
        
        # Simple approach: Take items with different first digits (assuming item_ids have different prefixes)
        selected_items = []
        prefixes_seen = set()
        
        for item_id, score in popular_items:
            # Get prefix (first digit or character)
            prefix = item_id[0] if item_id else ''
            
            # If we haven't seen this prefix, add the item
            if prefix not in prefixes_seen:
                selected_items.append((item_id, score))
                prefixes_seen.add(prefix)
                
                # Break if we have enough items
                if len(selected_items) >= n:
                    break
        
        # If we don't have enough items with different prefixes, add remaining popular items
        if len(selected_items) < n:
            remaining_items = [item for item in popular_items if item[0] not in [i[0] for i in selected_items]]
            selected_items.extend(remaining_items[:n-len(selected_items)])
        
        return selected_items[:n]
    
    def get_cf_predictions(self, user_id, unpurchased_items, similar_users):
        """Get collaborative filtering predictions based on similar users"""
        cf_scores = defaultdict(float)
        cf_counts = defaultdict(int)
        
        for sim_user, sim_score in similar_users:
            # Get items purchased by similar user
            sim_user_items = self.df[self.df['user_id'] == sim_user]['item_id'].unique()
            
            # Find items the target user hasn't purchased
            new_items = [item for item in sim_user_items if item in unpurchased_items]
            
            # Calculate score based on similarity
            for item in new_items:
                # Get the quantity this similar user purchased of the item
                sim_user_quantity = self.df[(self.df['user_id'] == sim_user) & 
                                         (self.df['item_id'] == item)]['quantity'].values[0]
                
                # Weight the quantity by similarity score
                cf_scores[item] += sim_score * sim_user_quantity
                cf_counts[item] += 1
        
        # Calculate final collaborative filtering scores
        cf_predictions = []
        for item, score in cf_scores.items():
            if cf_counts[item] > 0:
                avg_score = score / cf_counts[item]
                cf_predictions.append((item, avg_score))
        
        # Sort CF predictions
        cf_predictions.sort(key=lambda x: x[1], reverse=True)
        return cf_predictions
    
    def get_recommendations(self, user_id, n=5):
        """Get top N recommendations for a user with emphasis on user similarity and fallback for new users"""
        # Check if user exists in the database
        user_exists = user_id in self.user_item_matrix.index
        
        # If user doesn't exist, return diverse popular recommendations
        if not user_exists:
            print(f"User {user_id} not found in database. Returning popular recommendations.")
            return self.get_diverse_recommendations(n=n)
        
        # Get all items
        all_items = self.df['item_id'].unique()
        
        # Get items the user has already purchased
        user_items = self.df[self.df['user_id'] == user_id]['item_id'].unique()
        
        # Get items the user hasn't purchased
        unpurchased_items = np.setdiff1d(all_items, user_items)
        
        # Find similar users
        similar_users = get_similar_users(user_id, self.user_item_matrix, n=10)
        
        # Get recommendations from SVD model
        svd_predictions = get_svd_predictions(self.svd_model, user_id, unpurchased_items)
        svd_top_items = [item for item, _ in svd_predictions[:n*3]]
        
        # Get recommendations from similar users (user-based collaborative filtering)
        cf_predictions = self.get_cf_predictions(user_id, unpurchased_items, similar_users)
        cf_top_items = [item for item, _ in cf_predictions[:n*2]] if cf_predictions else []
        
        # Hybrid approach: Combine SVD and collaborative filtering
        # Items in both lists get higher priority
        common_items = set(svd_top_items).intersection(set(cf_top_items))
        
        # Start with items recommended by both approaches
        final_recommendations = []
        for item in common_items:
            # Find scores from both approaches
            svd_score = next((score for i, score in svd_predictions if i == item), 0)
            cf_score = next((score for i, score in cf_predictions if i == item), 0)
            
            # Weighted average with higher weight on collaborative filtering
            combined_score = (0.4 * svd_score) + (0.6 * cf_score)
            final_recommendations.append((item, combined_score))
        
        # Add remaining top items from CF until we reach n recommendations
        remaining_cf = [item for item in cf_top_items if item not in common_items]
        for item in remaining_cf:
            if len(final_recommendations) >= n:
                break
            score = next((score for i, score in cf_predictions if i == item), 0)
            final_recommendations.append((item, score))
        
        # Add remaining top SVD items if needed
        remaining_svd = [item for item in svd_top_items if item not in common_items and item not in remaining_cf[:n]]
        for item in remaining_svd:
            if len(final_recommendations) >= n:
                break
            score = next((score for i, score in svd_predictions if i == item), 0)
            final_recommendations.append((item, score))
        
        # If we still don't have enough recommendations, add popular items
        if len(final_recommendations) < n:
            popular_items = self.get_popular_items(n=n)
            popular_items = [(item, score) for item, score in popular_items 
                             if item not in [i[0] for i in final_recommendations]]
            final_recommendations.extend(popular_items[:n-len(final_recommendations)])
        
        # Sort by combined score and return top n
        final_recommendations.sort(key=lambda x: x[1], reverse=True)
        return final_recommendations[:n]
    
    def get_top_products(self, user_id, n=5):
        """Return the top N products for a specific user, with fallback for new users"""
        try:
            # Check if user exists in the system
            user_exists = user_id in self.user_item_matrix.index
            
            # Generate recommendations
            recommendations = self.get_recommendations(user_id, n=n)
            
            # Format the results
            top_products = []
            for i, (item_id, score) in enumerate(recommendations, 1):
                product = {
                    'rank': i,
                    'item_id': item_id,
                    'score': round(score, 2)
                }
                
                # Add note for popular items
                if not user_exists:
                    product['note'] = 'popular item (fallback)'
                    
                top_products.append(product)
            
            return {
                'user_id': user_id,
                'user_exists': user_exists,
                'recommendation_type': 'personalized' if user_exists else 'popular',
                'recommendations': top_products
            }
            
        except Exception as e:
            # Log the error
            print(f"Error generating recommendations for user {user_id}: {str(e)}")
            
            # Fallback to popular items
            popular_items = self.get_popular_items(n=n)
            top_products = []
            for i, (item_id, score) in enumerate(popular_items, 1):
                top_products.append({
                    'rank': i,
                    'item_id': item_id,
                    'score': round(score, 2),
                    'note': 'popular item (fallback)'
                })
            
            return {
                'user_id': user_id,
                'user_exists': False,
                'recommendation_type': 'popular (error fallback)',
                'recommendations': top_products
            }