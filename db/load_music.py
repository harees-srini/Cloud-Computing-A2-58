import json
import boto3
from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('music')

# Read the JSON file
with open('2026a2_songs.json', 'r') as f:
    songs = json.load(f)['songs']

# Add each song to the database
for song in songs:
    # Convert year to number (DynamoDB needs this)
    item = {
        'artist': song['artist'],
        'title_album': f"{song['title']}#{song['album']}",  # composite sort key
        'album': song['album'],
        'image_url': song['img_url'], #rename
        'title': song['title'],
        'year': song['year']       
    }
    
    table.put_item(Item=item)
    print(f"Added: {song['title']} by {song['artist']}")

print("All songs loaded")