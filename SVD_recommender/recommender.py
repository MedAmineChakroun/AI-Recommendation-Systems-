import numpy as np
import pandas as pd
from collections import defaultdict

from models.similarity import get_similar_users
from models.svd_model import get_svd_predictions
from models.similarity import get_neighborhood_scores

class RecommenderService:
    def __init__(self, df, svd_model):
        self.df = df
        self.svd_model = svd_model
        self.user_item_matrix = df.pivot_table(index='user_id', columns='item_id', values='quantity', fill_value=0)

    def get_popular_items(self, n=10):
        stats = self.df.groupby('item_id').agg(
            count=('quantity', 'count'),
            avg_quantity=('quantity', 'mean')
        ).reset_index()
        stats['norm_count'] = stats['count'] / stats['count'].max()
        stats['popularity'] = 0.7 * stats['norm_count'] + 0.3 * (stats['avg_quantity'] / 5.0)
        top_items = stats.sort_values('popularity', ascending=False).head(n)
        return list(zip(top_items['item_id'], top_items['popularity']))

    def get_diverse_recommendations(self, n=5):
        popular_items = self.get_popular_items(n * 3)
        selected, seen_prefixes = [], set()
        for item_id, score in popular_items:
            prefix = item_id[0] if item_id else ''
            if prefix not in seen_prefixes:
                selected.append((item_id, score))
                seen_prefixes.add(prefix)
            if len(selected) == n:
                break
        if len(selected) < n:
            remaining = [item for item in popular_items if item[0] not in [i[0] for i in selected]]
            selected += remaining[:n - len(selected)]
        return selected[:n]

    def get_cf_predictions(self, user_id, unpurchased_items, similar_users):
        """Get CF predictions using neighborhood scores utility"""
        item_quantities = defaultdict(dict)
        
        if not similar_users:  # If no similar users found
            return []
            
        for sim_user, sim_score in similar_users:
            sim_user_data = self.df[self.df['user_id'] == sim_user]
            for _, row in sim_user_data.iterrows():
                item = row['item_id']
                if item in unpurchased_items:
                    item_quantities[item][(sim_user, sim_score)] = row['quantity']

        scores = get_neighborhood_scores(item_quantities)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def get_recommendations(self, user_id, n=5):
        if user_id not in self.user_item_matrix.index:
            return self.get_diverse_recommendations(n)

        all_items = set(self.df['item_id'].unique())
        user_items = set(self.df[self.df['user_id'] == user_id]['item_id'].unique())
        unpurchased = list(all_items - user_items)

        try:
            similar_users = get_similar_users(user_id, self.user_item_matrix, n=10)
            svd_preds = get_svd_predictions(self.svd_model, user_id, unpurchased)
            cf_preds = self.get_cf_predictions(user_id, unpurchased, similar_users)

            if not cf_preds and not svd_preds:  # If both prediction methods fail
                return self.get_diverse_recommendations(n)

            svd_top = {item: score for item, score in svd_preds[:n * 3]}
            cf_top = {item: score for item, score in cf_preds[:n * 2]}

            combined = []
            common = set(svd_top) & set(cf_top)

            for item in common:
                score = 0.4 * svd_top[item] + 0.6 * cf_top[item]
                combined.append((item, score))

            for item in cf_top:
                if item not in common and len(combined) < n:
                    combined.append((item, cf_top[item]))

            for item in svd_top:
                if item not in cf_top and len(combined) < n:
                    combined.append((item, svd_top[item]))

            if len(combined) < n:
                fallback = self.get_popular_items(n)
                used = {i[0] for i in combined}
                combined += [item for item in fallback if item[0] not in used][:n - len(combined)]

            return sorted(combined, key=lambda x: x[1], reverse=True)[:n]
        except Exception as e:
            print(f"Recommendation error for user {user_id}: {e}")
            return self.get_diverse_recommendations(n)

    def get_top_products(self, user_id, n=5):
        try:
            user_exists = user_id in self.user_item_matrix.index
            recs = self.get_recommendations(user_id, n)
            products = []
            for i, (item, score) in enumerate(recs, 1):
                prod = {'rank': i, 'item_id': item, 'score': round(score, 2)}
                if not user_exists:
                    prod['note'] = 'popular item (fallback)'
                products.append(prod)
            return {
                'user_id': user_id,
                'user_exists': user_exists,
                'recommendation_type': 'personalized' if user_exists else 'popular',
                'recommendations': products
            }
        except Exception as e:
            print(f"Recommendation error for user {user_id}: {e}")
            fallback = self.get_popular_items(n)
            products = [{'rank': i+1, 'item_id': item, 'score': round(score, 2), 'note': 'popular item (fallback)'} 
                        for i, (item, score) in enumerate(fallback)]
            return {
                'user_id': user_id,
                'user_exists': False,
                'recommendation_type': 'popular (error fallback)',
                'recommendations': products
            }
