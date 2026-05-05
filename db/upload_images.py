import json
import requests
import boto3
import os

# Connect to S3
s3 = boto3.client('s3', region_name='us-east-1')
bucket_name = 'music-images-piyush'

# Read songs
with open('2026a2_songs.json', 'r') as f:
    songs = json.load(f)['songs']

# Download each image
for i, song in enumerate(songs):
    try:
        image_url = song['img_url']
        artist = song['artist'].replace(' ', '_')  # Replace spaces
        filename = f"{artist}_{i}.jpg"
        
        # Download image
        response = requests.get(image_url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        # Upload to S3
        s3.upload_file(filename, bucket_name, filename)
        print(f"Uploaded: {filename}")
        
        # Delete local file
        os.remove(filename)
        
    except Exception as e:
        print(f"Error: {e}")

print("Uploaded images to S3 bucket")