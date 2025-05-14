import pandas as pd
import pyodbc
import sqlalchemy
from config import DB_CONFIG

def create_connection_string():
    return (f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"Trusted_Connection={DB_CONFIG['trusted_connection']};")

def fetch_transactions():
    conn_str = create_connection_string()
    connection_url = f"mssql+pyodbc:///?odbc_connect={conn_str}"
    engine = sqlalchemy.create_engine(connection_url)

    query = """
    SELECT 
        DV.[DocPiece] AS order_id,
        DVL.[LigneArtCode] AS item_id
    FROM 
        [B2C_DB].[dbo].[DocumentVentes] DV
    JOIN 
        [B2C_DB].[dbo].[DocumentVenteLignes] DVL 
        ON DV.[DocPiece] = DVL.[LigneDocPiece]
    """

    df = pd.read_sql(query, engine)
    df['order_id'] = df['order_id'].astype(str)
    df['item_id'] = df['item_id'].astype(str)
    return df
