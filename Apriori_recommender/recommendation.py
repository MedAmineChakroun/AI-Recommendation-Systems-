import pandas as pd
import pickle
import os
import time

from mlxtend.frequent_patterns import apriori, association_rules
from fetch_data import fetch_transactions
from config import MODEL_CONFIG, DEFAULT_RECOMMENDATIONS

class RecommendationEngine:
    def __init__(self):
        self.rules = None
        self.rules_index = {}  # For faster lookups
        self.model_path = "saves/recommendation_rules.pkl"
        
        # Try to load existing model first
        if os.path.exists(self.model_path):
            try:
                print("Loading existing recommendation rules...")
                start_time = time.time()
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.rules = model_data['rules']
                    self.rules_index = model_data['index']
                
                load_time = time.time() - start_time
                print(f"Model loaded in {load_time:.2f} seconds.")
                print(f"Loaded {len(self.rules)} association rules.")
            except Exception as e:
                print(f"Failed to load model: {e}")
                self.initialize()
        else:
            print("No existing model found. Initializing new one...")
            self.initialize()

    def initialize(self):
        """Train the recommendation engine from scratch"""
        print("Building new recommendation rules...")
        start_time = time.time()
        
        # Step 1: Fetch transaction data from database
        df = fetch_transactions()
        
        # Step 2: Transform data into basket format
        basket = df.groupby(['order_id', 'item_id']).size().unstack(fill_value=0)
        basket = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        # Step 3: Generate frequent itemsets using Apriori algorithm
        frequent_itemsets = apriori(
            basket, 
            min_support=MODEL_CONFIG['min_support'], 
            use_colnames=True
        )
        
        # Step 4: Create association rules from frequent itemsets
        self.rules = association_rules(
            frequent_itemsets, 
            metric="lift", 
            min_threshold=MODEL_CONFIG['min_lift']
        )
        
        # Step 5: Build index for faster lookups
        self._build_index()
        
        build_time = time.time() - start_time
        print(f"Rules generated in {build_time:.2f} seconds.")
        print(f"Created {len(self.rules)} association rules.")
        
        # Step 6: Save model to disk
        self._save_model()
    
    def _build_index(self):
        """Build an index of rules for faster lookup"""
        self.rules_index = {}
        for idx, rule in self.rules.iterrows():
            antecedents = list(rule['antecedents'])
            for item in antecedents:
                if item not in self.rules_index:
                    self.rules_index[item] = []
                self.rules_index[item].append(idx)
    
    def _save_model(self):
        """Save the model to disk using pickle"""
        try:
            # Package the rules and index together
            model_data = {
                'rules': self.rules,
                'index': self.rules_index
            }
            
            # Save to a pickle file
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"Model saved successfully to {self.model_path}")
        except Exception as e:
            print(f"Failed to save model: {e}")

    def get_recommendations(self, item_ids, count=5):
        """Get recommendations based on items in cart"""
        # Return empty list if no rules or no items
        if self.rules is None or not item_ids:
            return []
        
        # Clean and standardize item_ids
        item_ids = [str(i).strip() for i in item_ids if i]
        if not item_ids:  # If after cleaning we have no items
            return []
        
        # Use the index for faster lookup
        candidate_indices = set()
        for item_id in item_ids:
            if item_id in self.rules_index:
                candidate_indices.update(self.rules_index[item_id])
        
        # If no matching rules found
        if not candidate_indices:
            return []
        
        # Get the candidate rules using the indices
        candidate_rules = self.rules.loc[list(candidate_indices)]
        
        # Sort by lift (higher lift = stronger association)
        sorted_rules = candidate_rules.sort_values(by='lift', ascending=False)
        
        # Extract recommendations
        recommendations = []
        for _, rule in sorted_rules.iterrows():
            consequents = list(rule['consequents'])
            for item in consequents:
                # Only add items not already in cart or recommendation list
                if item not in item_ids and item not in recommendations:
                    recommendations.append(item)
            # Stop once we have enough recommendations
            if len(recommendations) >= count:
                break
        
        return recommendations[:count]

# Global instance
recommendation_engine = RecommendationEngine()