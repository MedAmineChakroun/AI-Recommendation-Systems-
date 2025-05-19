import os
import pickle
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from config import MODEL_CONFIG

MODEL_PATH = "svd_model.pkl"

def create_svd_model(df, save_to_disk=True):
    """Create and train an SVD model using the provided DataFrame"""
    reader = Reader(rating_scale=(0, df['quantity'].max()))
    data = Dataset.load_from_df(df[['user_id', 'item_id', 'quantity']], reader)
    
    trainset, _ = train_test_split(
        data,
        test_size=0.2,
        random_state=MODEL_CONFIG['random_state']
    )

    svd = SVD(
        n_factors=MODEL_CONFIG['n_factors'],
        n_epochs=MODEL_CONFIG['n_epochs'],
        lr_all=MODEL_CONFIG['lr_all'],
        reg_all=MODEL_CONFIG['reg_all'],
        random_state=MODEL_CONFIG['random_state']
    )
    svd.fit(trainset)

    if save_to_disk:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(svd, f)

    return svd

def load_svd_model():
    """Load SVD model from disk if it exists"""
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    return None

def get_svd_predictions(model, user_id, unrated_items):
    """Get predictions from SVD model for unrated items"""
    predictions = []
    for item_id in unrated_items:
        try:
            pred = model.predict(user_id, item_id)
            predictions.append((item_id, pred.est))
        except Exception as e:
            print(f"Error predicting for user {user_id}, item {item_id}: {str(e)}")
            continue

    predictions.sort(key=lambda x: x[1], reverse=True)
    return predictions
