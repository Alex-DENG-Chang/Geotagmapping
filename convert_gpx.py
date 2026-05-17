import xml.etree.ElementTree as ET
import csv

def convert_gpx_to_csv(input_gpx_file, output_csv_file):
    # 1. Parse the GPX (XML) file
    tree = ET.parse(input_gpx_file)
    root = tree.getroot()

    # 2. Open the CSV file for writing
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write the header row (added elevation as a bonus, as it's common in GPX)
        writer.writerow(['lat', 'lon', 'time', 'elevation'])
        
        point_count = 0
        
        # 3. Loop through all elements in the XML tree
        for elem in root.iter():
            # GPX tags often have namespaces like {http://www.topografix.com/GPX/1/1}trkpt
            # We split by '}' to ignore the namespace and just get the tag name
            tag_name = elem.tag.split('}')[-1]
            
            # Check if the element is a track point, waypoint, or route point
            if tag_name in ['trkpt', 'wpt', 'rtept']:
                # Latitude and Longitude are stored as attributes inside the tag
                lat = elem.attrib.get('lat')
                lon = elem.attrib.get('lon')
                
                time_val = ""
                ele_val = ""
                
                # Time and Elevation are stored as child tags inside the point tag
                for child in elem:
                    child_tag = child.tag.split('}')[-1]
                    if child_tag == 'time':
                        time_val = child.text
                    elif child_tag == 'ele':
                        ele_val = child.text
                
                # Write the extracted data to the CSV
                writer.writerow([lat, lon, time_val, ele_val])
                point_count += 1

    print(f"Successfully converted {point_count} locations to '{output_csv_file}'")



input_file = '6_May_2026_3_02_29_pm.gpx'
output_file = '6_May_2026_3_02_29_pm.csv'

convert_gpx_to_csv(input_file, output_file)

# cd "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/gps_to_csv"
# source venv/bin/activate
# python convert_gpx.py
# deactivate