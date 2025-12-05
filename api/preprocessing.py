

import pandas as pd
import ast
from sklearn.preprocessing import MultiLabelBinarizer

# TMDB genre mapping
GENRE_MAPPING = {
    28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy', 80: 'Crime',
    99: 'Documentary', 18: 'Drama', 10751: 'Family', 14: 'Fantasy', 36: 'History',
    27: 'Horror', 10402: 'Music', 9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
    10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
}

def preprocess_data(df, popularity_threshold=100):
    
    # Convert genre_ids from string to list if needed
    if isinstance(df.loc[0, 'genre_ids'], str):
        df['genre_ids'] = df['genre_ids'].apply(ast.literal_eval)
    
    # Map genre IDs to real names
    def map_genres(ids_list):
        return [GENRE_MAPPING[i] for i in ids_list if i in GENRE_MAPPING]
    
    df['genres'] = df['genre_ids'].apply(map_genres)
    
    # One-hot encode genres
    mlb = MultiLabelBinarizer()
    genre_dummies = pd.DataFrame(
        mlb.fit_transform(df['genres']),
        columns=mlb.classes_,
        index=df.index
    )
    df = pd.concat([df, genre_dummies], axis=1)
    
    # Drop original genre columns
    df.drop(columns=['genre_ids', 'genres'], errors='ignore', inplace=True)
    
    # Handle missing values
    df.fillna(0, inplace=True)
    
    # Create classification label
    df['popular'] = df['popularity'].apply(lambda x: 1 if x >= popularity_threshold else 0)
    
    # Drop columns that won't be used as features
    # Keep 'popularity' for regression, 'popular' for classification
    # Remove textual columns like 'title', 'overview' (can add embeddings later if needed)
    cols_to_drop = ['title', 'overview', 'poster_path', 'id', 'original_title','backdrop_path', 'release_date']  # any non-numeric columns
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True)
    # Convert boolean to int
    df['adult'] = df['adult'].astype(int)
    df['video'] = df['video'].astype(int)

    # One-hot encode original_language
    df = pd.get_dummies(df, columns=['original_language'], prefix='lang')
    print(df.dtypes)
    return df


# Test the preprocessing script
if __name__ == "__main__":
    from data_ingestion import load_data_from_postgres
    df_raw = load_data_from_postgres()
    df_processed = preprocess_data(df_raw)
    print("Processed DataFrame:")
    print(df_processed.head())
    print("\nColumns:", df_processed.columns.tolist())

