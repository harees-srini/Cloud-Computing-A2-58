from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)
CORS(app)

# Artist to S3 image mapping
S3_BASE = 'https://cloudmusic-images-piyush.s3.amazonaws.com/'
ARTIST_IMAGE_MAP = {
    'Arcade Fire': 'Arcade_Fire_46.jpg',
    'Ben Harper': 'Ben_Harper_112.jpg',
    'Bill Withers': 'Bill_Withers_71.jpg',
    'Billy Bragg and Wilco': 'Billy_Bragg_and_Wilco_127.jpg',
    'Blitzen Trapper': 'Blitzen_Trapper_43.jpg',
    'Bob Dylan': 'Bob_Dylan_100.jpg',
    'Bob Marley': 'Bob_Marley_92.jpg',
    'Bryan Adams': 'Bryan_Adams_109.jpg',
    'Cat Stevens': 'Cat_Stevens_37.jpg',
    'Chvrches': 'Chvrches_116.jpg',
    'Coldplay': 'Coldplay_125.jpg',
    'Conor Oberst': 'Conor_Oberst_16.jpg',
    'Dave Matthews': 'Dave_Matthews_1.jpg',
    'David Bowie': 'David_Bowie_103.jpg',
    'DeVotchKa': 'DeVotchKa_136.jpg',
    'Dispatch': 'Dispatch_113.jpg',
    'Don McLean': 'Don_McLean_6.jpg',
    'Donovan': 'Donovan_18.jpg',
    'Edward Sharpe and The Magnetic Zeros': 'Edward_Sharpe_and_The_Magnetic_Zeros_56.jpg',
    'Elton John': 'Elton_John_96.jpg',
    'Elvis Perkins': 'Elvis_Perkins_32.jpg',
    'Emmylou Harris': 'Emmylou_Harris_45.jpg',
    'Father John Misty': 'Father_John_Misty_55.jpg',
    'First Aid Kit': 'First_Aid_Kit_35.jpg',
    'Gin Blossoms': 'Gin_Blossoms_51.jpg',
    "Guns N' Roses": "Guns_N'_Roses_91.jpg",
    'Harry Chapin': 'Harry_Chapin_19.jpg',
    'Jack Johnson': 'Jack_Johnson_12.jpg',
    'Jason Mraz': 'Jason_Mraz_65.jpg',
    'Jimmy Buffett': 'Jimmy_Buffett_13.jpg',
    'John Lennon': 'John_Lennon_126.jpg',
    'John Mellencamp': 'John_Mellencamp_67.jpg',
    'Johnny Cash': 'Johnny_Cash_23.jpg',
    'Journey': 'Journey_31.jpg',
    'Keane': 'Keane_102.jpg',
    'Kendrick Lamar': 'Kendrick_Lamar_11.jpg',
    'Lynyrd Skynyrd': 'Lynyrd_Skynyrd_110.jpg',
    'Mason Jennings': 'Mason_Jennings_24.jpg',
    'Metallica': 'Metallica_87.jpg',
    'Miley Cyrus': 'Miley_Cyrus_90.jpg',
    'Neil Young': 'Neil_Young_48.jpg',
    'OAR': 'OAR_61.jpg',
    'Oasis': 'Oasis_30.jpg',
    'Of Monsters and Men': 'Of_Monsters_and_Men_72.jpg',
    'Paul Simon': 'Paul_Simon_79.jpg',
    'Radiohead': 'Radiohead_22.jpg',
    'Regina Spektor': 'Regina_Spektor_29.jpg',
    'Ricky Nelson': 'Ricky_Nelson_75.jpg',
    'She and Him': 'She_and_Him_99.jpg',
    'Stealers Wheel': 'Stealers_Wheel_106.jpg',
    'Sublime': 'Sublime_2.jpg',
    'Taylor Swift': 'Taylor_Swift_10.jpg',
    'The Avett Brothers': 'The_Avett_Brothers_73.jpg',
    'The Band': 'The_Band_120.jpg',
    'The Beatles': 'The_Beatles_133.jpg',
    'The Church': 'The_Church_124.jpg',
    'The Eagles': 'The_Eagles_59.jpg',
    'The Kinks': 'The_Kinks_74.jpg',
    'The Lumineers': 'The_Lumineers_14.jpg',
    'The Melodians': 'The_Melodians_94.jpg',
    'The Pretenders': 'The_Pretenders_118.jpg',
    'The Tallest Man on Earth': 'The_Tallest_Man_on_Earth_0.jpg',
    'The White Stripes': 'The_White_Stripes_60.jpg',
    'Tom Petty': 'Tom_Petty_4.jpg',
    'Train': 'Train_52.jpg',
    'Vampire Weekend': 'Vampire_Weekend_134.jpg',
    'Van Morrison': 'Van_Morrison_15.jpg',
    'Violent Femmes': 'Violent_Femmes_5.jpg',
    'Weezer': 'Weezer_64.jpg',
    'Whitesnake': 'Whitesnake_50.jpg',
    'fun.': 'fun._17.jpg',
}

def get_image_url(artist):
    filename = ARTIST_IMAGE_MAP.get(artist, '')
    return S3_BASE + filename if filename else ''

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
            filter_expr = add_filter(filter_expr, Attr('year').eq(int(year)) | Attr('year').eq(str(year)))

        if filter_expr is not None:
            result = music_table.scan(FilterExpression=filter_expr)
        else:
            result = music_table.scan()

        songs = result.get('Items', [])

        # Build image URLs from S3
        for song in songs:
            song['image_url'] = get_image_url(song.get('artist', ''))
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
                    song['image_url'] = get_image_url(song.get('artist', ''))
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