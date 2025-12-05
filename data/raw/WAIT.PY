import pandas as pd

input_file = r"C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT\data\raw\tmdb_popular.csv"
output_file = r"C:\Users\smaso\OneDrive\Desktop\5th semester\ML PROJECT\data\raw\tmdb_popular_utf8.csv"

# Open with cp1252 and replace invalid characters
with open(input_file, 'r', encoding='cp1252', errors='replace') as f_in:
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            f_out.write(line)

print("CSV converted to UTF-8 successfully")
