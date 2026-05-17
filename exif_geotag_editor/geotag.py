import os
import glob
import subprocess
import datetime
import gpxpy
from bisect import bisect_left

# ==========================================
#  SETTINGS 
# ==========================================
GPS_FOLDER = "/Volumes/alex_t7/📷_Lumix_s1r/Lumix_s1r_2026-05-02_海南/Lumix_s1r_2026-05-02_海南_GPS"
PHOTO_FOLDER = "/Volumes/alex_t7/📷_Lumix_s1r/Lumix_s1r_2026-05-02_海南/Lumix_s1r_2026-05-02_海南_PicFIX"

# Timezone difference: Camera is UTC+8, GPX is UTC.
CAMERA_TZ_OFFSET_HOURS = 8
# Maximum allowed time difference between photo and GPS point (in seconds)
MAX_TOLERANCE_SECONDS = 3600 

# ==========================================

def load_gpx_data(gps_folder):
    """Loops through all .gpx files and extracts a sorted list of (time, lat, lon)."""
    print("Parsing GPX files...")
    gpx_points = []
    gpx_files = glob.glob(os.path.join(gps_folder, "*.gpx"))
    
    for file in gpx_files:
        with open(file, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            # Strip timezone info to make it standard UTC naive datetime
                            utc_time = point.time.replace(tzinfo=None)
                            gpx_points.append((utc_time, point.latitude, point.longitude))
                            
    # Sort the list by time so we can do a fast nearest-match search
    gpx_points.sort(key=lambda x: x[0])
    print(f"✅ Found {len(gpx_points)} GPS points across {len(gpx_files)} files.\n")
    return gpx_points

def get_closest_gps(target_time, gpx_points):
    """Finds the closest GPS point to the given target time."""
    if not gpx_points:
        return None
        
    # Extract just the times for the bisect algorithm
    times = [p[0] for p in gpx_points]
    pos = bisect_left(times, target_time)
    
    # Determine the closest point (either before or after the target time)
    if pos == 0:
        return gpx_points[0]
    if pos == len(gpx_points):
        return gpx_points[-1]
        
    before = gpx_points[pos - 1]
    after = gpx_points[pos]
    
    if target_time - before[0] < after[0] - target_time:
        return before
    else:
        return after

def get_photo_time(file_path):
    """Uses ExifTool to safely extract the original date/time the photo was taken."""
    try:
        # Ask ExifTool for the CreateDate or DateTimeOriginal
        result = subprocess.run(
            ['exiftool', '-DateTimeOriginal', '-s3', file_path],
            capture_output=True, text=True, check=True
        )
        time_str = result.stdout.strip()
        if time_str:
            # ExifTool returns time as "YYYY:MM:DD HH:MM:SS"
            return datetime.datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"Could not read time for {os.path.basename(file_path)}")
    return None

def write_gps_to_photo(file_path, lat, lon):
    """Uses ExifTool to strictly write GPS tags without altering the AVIF image data."""
    # Determine references (North/South, East/West)
    lat_ref = 'N' if lat >= 0 else 'S'
    lon_ref = 'E' if lon >= 0 else 'W'
    
    # ExifTool command to write coordinates and overwrite the original file in place
    cmd = [
        'exiftool',
        f'-GPSLatitude={abs(lat)}',
        f'-GPSLatitudeRef={lat_ref}',
        f'-GPSLongitude={abs(lon)}',
        f'-GPSLongitudeRef={lon_ref}',
        '-overwrite_original',
        file_path
    ]
    
    subprocess.run(cmd, capture_output=True)

def main():
    # 1. Load all GPS points
    gpx_points = load_gpx_data(GPS_FOLDER)
    if not gpx_points:
        print("No GPS data found. Exiting.")
        return

    # 2. Find all AVIF photos
    avif_files = glob.glob(os.path.join(PHOTO_FOLDER, "*.avif"))
    print(f"Found {len(avif_files)} AVIF photos to process.")

    # 3. Loop through photos
    for photo_path in avif_files:
        filename = os.path.basename(photo_path)
        
        # Get Camera Time
        camera_time = get_photo_time(photo_path)
        if not camera_time:
            continue
            
        # Convert Camera Time (UTC+8) to UTC to match GPX
        utc_photo_time = camera_time - datetime.timedelta(hours=CAMERA_TZ_OFFSET_HOURS)
        
        # Find closest GPS point
        closest_point = get_closest_gps(utc_photo_time, gpx_points)
        
        if closest_point:
            gps_time, lat, lon = closest_point
            time_diff = abs((utc_photo_time - gps_time).total_seconds())
            
            if time_diff <= MAX_TOLERANCE_SECONDS:
                print(f"✔️ {filename} -> Matched! (Diff: {int(time_diff)}s) Writing Lat: {lat:.5f}, Lon: {lon:.5f}")
                write_gps_to_photo(photo_path, lat, lon)
            else:
                print(f"⏭️ {filename} -> Skipped. Closest GPS point is too far away in time ({int(time_diff)}s).")

    print("All done! Your photos are safely geotagged.")

if __name__ == "__main__":
    main()


#source /Users/alexdengmbp21/🧑‍💻_python_projets/cam_geotag/venv/bin/activate
#python /Users/alexdengmbp21/🧑‍💻_python_projets/cam_geotag/geotag.py
