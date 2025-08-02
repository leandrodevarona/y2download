from app.database.database import get_db_connection
from app.database.schemas import MetaData

def get_metadata() -> MetaData:
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, likes, dislikes FROM metadata WHERE id = 1")
    metadata_row = cursor.fetchone()
    meta = MetaData(**metadata_row)
    return meta

def like():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE metadata SET likes = likes + 1 WHERE id = 1")
    db.commit()

    meta = get_metadata()
    return meta.likes

def dislike():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE metadata SET dislikes = dislikes + 1 WHERE id = 1")
    db.commit()
    
    meta = get_metadata()
    return meta.dislikes