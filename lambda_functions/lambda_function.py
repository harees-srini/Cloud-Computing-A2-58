import json
import boto3
import base64
from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')

def lambda_handler(event, context):
    """
    Main handler for all API requests
    """
    
    # Get the HTTP method and path
    http_method = event['httpMethod']
    path = event['path']
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    
    try:
        # LOGIN endpoint
        if path == '/login' and http_method == 'POST':
            return handle_login(body)
        
        # REGISTER endpoint
        elif path == '/register' and http_method == 'POST':
            return handle_register(body)
        
        # GET USER endpoint
        elif path == '/user' and http_method == 'GET':
            email = event['queryStringParameters']['email']
            return handle_get_user(email)
        
        # SEARCH endpoint
        elif path == '/search' and http_method == 'POST':
            return handle_search(body)
        
        # SUBSCRIBE endpoint
        elif path == '/subscribe' and http_method == 'POST':
            return handle_subscribe(body)
        
        # GET SUBSCRIPTIONS endpoint
        elif path == '/subscriptions' and http_method == 'GET':
            email = event['queryStringParameters']['email']
            return handle_get_subscriptions(email)
        
        # UNSUBSCRIBE endpoint
        elif path == '/unsubscribe' and http_method == 'DELETE':
            return handle_unsubscribe(body)
        
        else:
            return response(404, {'error': 'Not found'})
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_login(body):
    """Handle user login"""
    email = body.get('email')
    password = body.get('password')
    
    try:
        result = login_table.get_item(Key={'email': email})
        
        if 'Item' not in result:
            return response(401, {'success': False, 'message': 'Email or password is invalid'})
        
        user = result['Item']
        if user['password'] == password:
            return response(200, {'success': True, 'user_name': user['user_name']})
        else:
            return response(401, {'success': False, 'message': 'Email or password is invalid'})
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_register(body):
    """Handle user registration"""
    email = body.get('email')
    username = body.get('username')
    password = body.get('password')
    
    try:
        # Check if email exists
        result = login_table.get_item(Key={'email': email})
        if 'Item' in result:
            return response(400, {'success': False, 'message': 'The email already exists'})
        
        # Add new user
        login_table.put_item(Item={
            'email': email,
            'user_name': username,
            'password': password
        })
        
        return response(200, {'success': True, 'message': 'Registration successful'})
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_get_user(email):
    """Get user information"""
    try:
        result = login_table.get_item(Key={'email': email})
        
        if 'Item' not in result:
            return response(404, {'error': 'User not found'})
        
        user = result['Item']
        return response(200, {
            'email': user['email'],
            'user_name': user['user_name']
        })
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_search(body):
    """Search for songs"""
    title = body.get('title', '')
    artist = body.get('artist', '')
    album = body.get('album', '')
    year = body.get('year')
    
    try:
        results = []
        
        # If artist is provided, use GSI
        if artist:
            response_data = music_table.query(
                KeyConditionExpression='artist = :artist',
                ExpressionAttributeValues={':artist': artist}
            )
            results = response_data['Items']
        else:
            # Scan all songs
            response_data = music_table.scan()
            results = response_data['Items']
        
        # Filter results
        filtered = []
        for song in results:
            match = True
            if title and title.lower() not in song['title'].lower():
                match = False
            if album and album.lower() != song['album'].lower():
                match = False
            if year and int(song['year']) != year:
                match = False
            
            if match:
                filtered.append({
                    'title': song['title'],
                    'artist': song['artist'],
                    'album': song['album'],
                    'year': int(song['year']),
                    'image_url': song.get('image_url', '')
                })
        
        return response(200, filtered)
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_subscribe(body):
    """Add song to user subscriptions"""
    email = body.get('email')
    title = body.get('title')
    artist = body.get('artist')
    
    try:
        # Create subscription table if needed or use a field in login table
        login_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscriptions = list_append(subscriptions, :val)',
            ExpressionAttributeValues={':val': [{'title': title, 'artist': artist}]},
            ReturnValues='ALL_NEW'
        )
        
        return response(200, {'success': True})
    
    except Exception as e:
        # If subscriptions list doesn't exist, create it
        try:
            login_table.update_item(
                Key={'email': email},
                UpdateExpression='SET subscriptions = :val',
                ExpressionAttributeValues={':val': [{'title': title, 'artist': artist}]},
                ReturnValues='ALL_NEW'
            )
            return response(200, {'success': True})
        except:
            return response(500, {'error': str(e)})


def handle_get_subscriptions(email):
    """Get user subscriptions"""
    try:
        result = login_table.get_item(Key={'email': email})
        
        if 'Item' not in result:
            return response(404, {'error': 'User not found'})
        
        user = result['Item']
        subscriptions = user.get('subscriptions', [])
        
        # Get details for each subscription
        detailed_subs = []
        for sub in subscriptions:
            song = music_table.get_item(
                Key={'artist': sub['artist'], 'title': sub['title']}
            )
            if 'Item' in song:
                detailed_subs.append({
                    'title': song['Item']['title'],
                    'artist': song['Item']['artist'],
                    'album': song['Item']['album'],
                    'year': int(song['Item']['year']),
                    'image_url': song['Item'].get('image_url', '')
                })
        
        return response(200, detailed_subs)
    
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_unsubscribe(body):
    """Remove song from subscriptions"""
    email = body.get('email')
    title = body.get('title')
    artist = body.get('artist')
    
    try:
        result = login_table.get_item(Key={'email': email})
        subscriptions = result['Item'].get('subscriptions', [])
        
        # Remove the song
        subscriptions = [s for s in subscriptions if not (s['title'] == title and s['artist'] == artist)]
        
        login_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscriptions = :val',
            ExpressionAttributeValues={':val': subscriptions}
        )
        
        return response(200, {'success': True})
    
    except Exception as e:
        return response(500, {'error': str(e)})


def response(status_code, body):
    """Create HTTP response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }