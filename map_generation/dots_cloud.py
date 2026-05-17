# dots_cloud.py
import folium
import pandas as pd
import os

# 1. Define the file paths
csv_file_path = "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/csv/photo_gps_data.csv"

# The output map will be saved in your 'main' folder
output_map_path = "dot_cloud_output.html"

def create_dot_cloud():
    print(f"Reading data from: {csv_file_path}")
    
    # 2. Read the CSV file using pandas
    try:
        df = pd.read_csv(csv_file_path)
        # Drop any rows that have missing data in the first two columns
        df = df.dropna(subset=[df.columns[0], df.columns[1]]) 
    except FileNotFoundError:
        print("Error: Could not find the CSV file. Please check the path.")
        return

    # 3. Calculate the center of the map so it opens in the right place
    avg_lat = df.iloc[:, 0].mean()
    avg_lon = df.iloc[:, 1].mean()

    # 4. Initialize the Folium Map
    print("Generating map...")
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles='CartoDB positron')

    # 5. Add a CircleMarker (dot) for every row in the dataset
    # You can tweak the radius, color, and fill_opacity to make your cloud look perfect
    for lat, lon in zip(df.iloc[:, 0], df.iloc[:, 1]):
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,             # Size of the dot
            color='#3186cc',      # Hex color or name (e.g., 'blue', 'red')
            weight=0,             # Set to 0 to remove the dot's outline
            fill=True,
            fill_color='#3186cc', # Fill color of the dot
            fill_opacity=0.6      # Transparency (0.0 to 1.0). Lower = more "cloud-like"
        ).add_to(m)

    # 6. Save the map to an HTML file
    m.save(output_map_path)
    print(f"✅ Success! Dot cloud map saved as '{output_map_path}'.")
    print(f"Double click '{output_map_path}' to open it in your web browser.")

if __name__ == "__main__":
    create_dot_cloud()

# cd "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/main"
# source venv/bin/activate
# python dots_cloud.py
# deactivate