import folium
from folium.plugins import HeatMap
import pandas as pd
import os

# 1. Define the file paths
# Using the absolute path you provided for the CSV
csv_file_path = "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/csv/heatmap_cor_pho.csv"

# The output map will be saved in your 'main' folder
output_map_path = "heatmap_output.html"

def create_heatmap():
    print(f"Reading data from: {csv_file_path}")
    
    # 2. Read the CSV file using pandas
    # Using iloc[:, [0, 1]] grabs the exact first (A) and second (B) columns, 
    # so it works even if your column headers are named differently or missing.
    try:
        df = pd.read_csv(csv_file_path)
        # Drop any rows that have missing data
        df = df.dropna(subset=[df.columns[0], df.columns[1]]) 
    except FileNotFoundError:
        print("Error: Could not find the CSV file. Please check the path.")
        return

    # Extract latitudes and longitudes as a list of lists: [[lat, lon], [lat, lon], ...]
    heat_data = df.iloc[:, [0, 1]].values.tolist()

    # 3. Calculate the center of the map so it opens in the right place
    avg_lat = df.iloc[:, 0].mean()
    avg_lon = df.iloc[:, 1].mean()

    # 4. Initialize the Folium Map
    # zoom_start determines how zoomed in the map is initially (1-20)
    print("Generating map...")
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles='CartoDB positron')

    # 5. Add the HeatMap layer to the map
    # You can tweak radius (size of point) and blur (smoothness) to make it look better
    HeatMap(heat_data, radius=1, blur=1).add_to(m)

    # 6. Save the map to an HTML file
    m.save(output_map_path)
    print(f"✅ Success! Heatmap saved as '{output_map_path}'.")
    print(f"Double click '{output_map_path}' to open it in your web browser.")

if __name__ == "__main__":
    create_heatmap()

# cd "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/main"
# source venv/bin/activate
# deactivate
# python heatmap.py