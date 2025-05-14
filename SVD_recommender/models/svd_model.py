"""
SVD model for recommendation system
"""
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from config import MODEL_CONFIG

def create_svd_model(df):
    """Create and train an SVD model using the provided DataFrame"""
    # Create a Surprise reader and dataset
    reader = Reader(rating_scale=(0, df['rating'].max()))
    data = Dataset.load_from_df(df[['user_id', 'item_id', 'rating']], reader)
    
    # Split the dataset
    trainset, _ = train_test_split(
        data, 
        test_size=0.2, 
        random_state=MODEL_CONFIG['random_state']
    )
    
    # Define and train the SVD model
    svd = SVD(
        n_factors=MODEL_CONFIG['n_factors'],
        n_epochs=MODEL_CONFIG['n_epochs'],
        lr_all=MODEL_CONFIG['lr_all'],
        reg_all=MODEL_CONFIG['reg_all'],
        random_state=MODEL_CONFIG['random_state']
    )
    svd.fit(trainset)
    
    return svd

def get_svd_predictions(model, user_id, unrated_items):
    """Get predictions from SVD model for unrated items"""
    predictions = []
    
    for item_id in unrated_items:
        try:
            pred = model.predict(user_id, item_id)
            predictions.append((item_id, pred.est))
        except Exception as e:
            # Skip items that cause prediction errors
            print(f"Error predicting for user {user_id}, item {item_id}: {str(e)}")
            continue
    
    # Sort predictions by estimated rating
    predictions.sort(key=lambda x: x[1], reverse=True)
    return predictions