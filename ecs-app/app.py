from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)
CORS(app)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')

# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print("Login attempt:", data)
    try:
        result = login_table.get_item(Key={'email': data['email']})
        print("DynamoDB result:", result)
        if 'Item' in result and result['Item']['password'] == data['password']:
            return jsonify({'success': True, 'user_name': result['Item']['user_name']})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        result = login_table.get_item(Key={'email': data['email']})
        if 'Item' in result:
            return jsonify({'success': False, 'message': 'Email already exists'}), 400

        login_table.put_item(Item={
            'email': data['email'],
            'user_name': data['username'],
            'password': data['password'],
            'subscriptions': []
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# GET USER PROFILE
# ─────────────────────────────────────────
@app.route('/user', methods=['GET'])
def get_user():
    email = request.args.get('email')
    try:
        result = login_table.get_item(Key={'email': email})
        if 'Item' not in result:
            return jsonify({'error': 'User not found'}), 404
        item = result['Item']
        return jsonify({
            'email': item['email'],
            'user_name': item['user_name']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# SEARCH MUSIC
# ─────────────────────────────────────────
@app.route('/search', methods=['POST'])
def search():
    data = request.json
    title  = data.get('title', '').strip()
    artist = data.get('artist', '').strip()
    album  = data.get('album', '').strip()
    year   = data.get('year')

    try:
        filter_expr = None

        def add_filter(existing, new_condition):
            return new_condition if existing is None else existing & new_condition

        if title:
            filter_expr = add_filter(filter_expr, Attr('title').contains(title))
        if artist:
            filter_expr = add_filter(filter_expr, Attr('artist').contains(artist))
        if album:
            filter_expr = add_filter(filter_expr, Attr('album').contains(album))
        if year:
            filter_expr = add_filter(filter_expr, Attr('year').eq(int(year)))

        if filter_expr is not None:
            result = music_table.scan(FilterExpression=filter_expr)
        else:
            result = music_table.scan()

        songs = result.get('Items', [])

        # Build image URLs from S3
        s3_base = 'https://cloudmusic-images-piyush.s3.amazonaws.com/'
        for song in songs:
            if 'image_url' not in song or not song['image_url']:
                artist_clean = song.get('artist', '').replace(' ', '+')
                song['image_url'] = f"{s3_base}{artist_clean}.jpg"

        return jsonify(songs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# GET SUBSCRIPTIONS
# ─────────────────────────────────────────
@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    email = request.args.get('email')
    try:
        result = login_table.get_item(Key={'email': email})
        if 'Item' not in result:
            return jsonify([])

        subscriptions = result['Item'].get('subscriptions', [])
        songs = []

        for sub in subscriptions:
            try:
                song_result = music_table.get_item(Key={
                    'title': sub['title'],
                    'artist': sub['artist']
                })
                if 'Item' in song_result:
                    song = song_result['Item']
                    if 'image_url' not in song or not song['image_url']:
                        artist_clean = song.get('artist', '').replace(' ', '+')
                        song['image_url'] = f"https://cloudmusic-images-piyush.s3.amazonaws.com/{artist_clean}.jpg"
                    songs.append(song)
            except:
                pass

        return jsonify(songs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# SUBSCRIBE
# ─────────────────────────────────────────
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email  = data['email']
    title  = data['title']
    artist = data['artist']
    try:
        result = login_table.get_item(Key={'email': email})
        if 'Item' not in result:
            return jsonify({'error': 'User not found'}), 404

        subscriptions = result['Item'].get('subscriptions', [])

        # Check not already subscribed
        for sub in subscriptions:
            if sub['title'] == title and sub['artist'] == artist:
                return jsonify({'success': False, 'message': 'Already subscribed'}), 400

        subscriptions.append({'title': title, 'artist': artist})

        login_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscriptions = :s',
            ExpressionAttributeValues={':s': subscriptions}
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
# UNSUBSCRIBE
# ─────────────────────────────────────────
@app.route('/unsubscribe', methods=['DELETE'])
def unsubscribe():
    data = request.json
    email  = data['email']
    title  = data['title']
    artist = data['artist']
    try:
        result = login_table.get_item(Key={'email': email})
        if 'Item' not in result:
            return jsonify({'error': 'User not found'}), 404

        subscriptions = result['Item'].get('subscriptions', [])
        subscriptions = [s for s in subscriptions if not (s['title'] == title and s['artist'] == artist)]

        login_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscriptions = :s',
            ExpressionAttributeValues={':s': subscriptions}
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)