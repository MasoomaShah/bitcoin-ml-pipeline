

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

def preprocess_data(df, popularity_threshold=100, mlb=None):
    """
    Preprocess dataframe for training or single-row prediction.

    If `mlb` (MultiLabelBinarizer) is provided, it will be used to transform genres
    without refitting so that one-hot columns stay consistent between training and
    inference. The function returns (df_processed, mlb_used).
    """
    # Convert genre_ids from string to list if needed
    if 'genre_ids' in df.columns and len(df) and isinstance(df.loc[0, 'genre_ids'], str):
        df['genre_ids'] = df['genre_ids'].apply(ast.literal_eval)

    # Map genre IDs to real names
    def map_genres(ids_list):
        return [GENRE_MAPPING[i] for i in ids_list if i in GENRE_MAPPING]

    if 'genre_ids' in df.columns:
        df['genres'] = df['genre_ids'].apply(map_genres)
    else:
        # ensure column exists
        df['genres'] = [[] for _ in range(len(df))]

    # One-hot encode genres. If mlb passed, use it (no refit). Otherwise fit new mlb.
    if mlb is None:
        mlb = MultiLabelBinarizer()
        genre_matrix = mlb.fit_transform(df['genres'])
    else:
        # mlb must have been fitted previously; transform will produce columns in same order
        genre_matrix = mlb.transform(df['genres'])

    genre_dummies = pd.DataFrame(
        genre_matrix,
        columns=mlb.classes_,
        index=df.index
    )
    df = pd.concat([df, genre_dummies], axis=1)

    # Drop original genre columns
    df.drop(columns=['genre_ids', 'genres'], errors='ignore', inplace=True)

    # Handle missing values
    df.fillna(0, inplace=True)

    # Create classification label if popularity present
    if 'popularity' in df.columns:
        df['popular'] = df['popularity'].apply(lambda x: 1 if x >= popularity_threshold else 0)

    # Drop columns that won't be used as features
    cols_to_drop = ['title', 'overview', 'poster_path', 'id', 'original_title', 'backdrop_path', 'release_date']
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True)

    # Convert boolean to int if present
    if 'adult' in df.columns:
        df['adult'] = df['adult'].astype(int)
    if 'video' in df.columns:
        df['video'] = df['video'].astype(int)

    # One-hot encode original_language if present
    if 'original_language' in df.columns:
        df = pd.get_dummies(df, columns=['original_language'], prefix='lang')

    print(df.dtypes)
    return df, mlb


# Test the preprocessing script
if __name__ == "__main__":
    from data_ingestion import load_data_from_postgres
    df_raw = load_data_from_postgres()
    df_processed = preprocess_data(df_raw)
    print("Processed DataFrame:")
    print(df_processed.head())
    print("\nColumns:", df_processed.columns.tolist())

