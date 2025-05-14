"""
Database connection and data fetching utilities
"""
import pandas as pd
import pyodbc
from config import DB_CONFIG

def create_connection_string():
    """Create the connection string from configuration"""
    return (f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"Trusted_Connection={DB_CONFIG['trusted_connection']};")

def fetch_data_from_db():
    """Fetches user-item interaction data from the database"""
    conn_str = create_connection_string()
    
    try:
        conn = pyodbc.connect(conn_str)
        
        # SQL query to get user-item interactions
        query = """
        SELECT 
            DV.[DocTiersCode] AS user_id, 
            DVL.[LigneArtCode] AS item_id, 
            SUM(DVL.[LigneQte]) AS quantity
        FROM 
            [B2C_DB].[dbo].[DocumentVentes] DV
        JOIN 
            [B2C_DB].[dbo].[DocumentVenteLignes] DVL 
            ON DV.[DocPiece] = DVL.[LigneDocPiece]
        GROUP BY 
            DV.[DocTiersCode], 
            DVL.[LigneArtCode]
        ORDER BY 
            quantity DESC
        """
      
        # Load data into DataFrame
        df = pd.read_sql(query, conn)
      
        # Close connection
        conn.close()
        
        # Convert to string for consistency
        df['user_id'] = df['user_id'].astype(str)
        df['item_id'] = df['item_id'].astype(str)
        
        return df
    except Exception as e:
        print(f"Database error: {e}")
        return None
  