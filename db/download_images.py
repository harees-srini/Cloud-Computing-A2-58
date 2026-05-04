import json
import requests
import boto3
import os

s3 = boto3.client("s3", region_name="us-east-1")

bucket_name = "cloudmusic-images-piyush"  # change to your real bucket name

with open("2026a2_songs.json", "r") as f:
    data = json.load(f)

songs = data["songs"]

for i, song in enumerate(songs):
    try:
        image_url = song["img_url"]  # FIXED
        artist = song["artist"].replace(" ", "_").replace("&", "and").replace("/", "_")
        filename = f"{artist}_{i}.jpg"

        response = requests.get(image_url, timeout=15)
        response.raise_for_status()

        with open(filename, "wb") as f:
            f.write(response.content)

        s3.upload_file(filename, bucket_name, filename)
        print(f"Uploaded: {filename}")

        os.remove(filename)

    except Exception as e:
        print(f"Error at item {i}: {e}")

print("Done!")