from flask import Flask, request, jsonify
import boto3
import json

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        result = login_table.get_item(Key={'email': data['email']})
        if 'Item' in result and result['Item']['password'] == data['password']:
            return jsonify({'success': True, 'user_name': result['Item']['user_name']})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            'password': data['password']
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)