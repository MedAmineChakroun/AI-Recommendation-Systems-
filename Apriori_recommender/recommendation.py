import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from fetch_data import fetch_transactions
from config import MODEL_CONFIG
class RecommendationEngine:
    def __init__(self):
        self.rules = None
        self.initialize()

    def initialize(self):
        df = fetch_transactions()
        basket = df.groupby(['order_id', 'item_id']).size().unstack(fill_value=0)
        basket = basket.applymap(lambda x: 1 if x > 0 else 0)

        frequent_itemsets = apriori(basket, min_support=MODEL_CONFIG['min_support'],use_colnames=True)
        self.rules = association_rules(frequent_itemsets, metric="lift", min_threshold=MODEL_CONFIG['min_lift'])

    def get_recommendations(self, item_ids, count=5):
        if self.rules is None:
            return []

        matches = self.rules[self.rules['antecedents'].apply(lambda x: any(i in x for i in item_ids))]
        sorted_matches = matches.sort_values(by='lift', ascending=False)

        recommendations = []
        for _, row in sorted_matches.iterrows():
            consequents = row['consequents']
            for item in consequents:
                if item not in item_ids and item not in recommendations:
                    recommendations.append(item)
            if len(recommendations) >= count:
                break
        return recommendations[:count]

recommendation_engine = RecommendationEngine()
