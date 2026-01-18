from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample player data (we'll add real Statcast data later)
SAMPLE_DATA = {
    '592450': {  # Aaron Judge
        'basicStats': {'avg': '.287', 'pa': 550, 'hits': 158, 'hr': 58},
        'customMetrics': {
            'qualityOfContact': 9.2,
            'plateApproach': 8.5,
            'powerEfficiency': 9.5,
            'consistencyScore': 8.1
        },
        'statcastData': [
            {'metric': 'Exit Velo', 'value': 95.2, 'percentile': 99},
            {'metric': 'Launch Angle', 'value': 13.8, 'percentile': 78},
            {'metric': 'Barrel %', 'value': 19.8, 'percentile': 99},
            {'metric': 'Hard Hit %', 'value': 52.1, 'percentile': 96},
        ],
        'sprayChart': []
    },
    '660271': {  # Shohei Ohtani
        'basicStats': {'avg': '.310', 'pa': 599, 'hits': 185, 'hr': 54},
        'customMetrics': {
            'qualityOfContact': 9.0,
            'plateApproach': 8.8,
            'powerEfficiency': 9.3,
            'consistencyScore': 8.9
        },
        'statcastData': [
            {'metric': 'Exit Velo', 'value': 93.1, 'percentile': 94},
            {'metric': 'Launch Angle', 'value': 12.4, 'percentile': 72},
            {'metric': 'Barrel %', 'value': 16.2, 'percentile': 95},
            {'metric': 'Hard Hit %', 'value': 49.8, 'percentile': 92},
        ],
        'sprayChart': []
    },
    '605141': {  # Mookie Betts
        'basicStats': {'avg': '.289', 'pa': 645, 'hits': 186, 'hr': 38},
        'customMetrics': {
            'qualityOfContact': 8.7,
            'plateApproach': 9.1,
            'powerEfficiency': 8.5,
            'consistencyScore': 8.8
        },
        'statcastData': [
            {'metric': 'Exit Velo', 'value': 91.8, 'percentile': 88},
            {'metric': 'Launch Angle', 'value': 14.2, 'percentile': 80},
            {'metric': 'Barrel %', 'value': 13.5, 'percentile': 89},
            {'metric': 'Hard Hit %', 'value': 46.2, 'percentile': 85},
        ],
        'sprayChart': []
    }
}

@app.route('/api/search', methods=['GET'])
def search_players():
    query = request.args.get('q', '').lower()
    players = [
        {'id': '592450', 'name': 'Aaron Judge', 'team': 'NYY', 'position': 'RF'},
        {'id': '660271', 'name': 'Shohei Ohtani', 'team': 'LAD', 'position': 'DH'},
        {'id': '605141', 'name': 'Mookie Betts', 'team': 'LAD', 'position': 'RF'},
        {'id': '660670', 'name': 'Ronald Acuña Jr.', 'team': 'ATL', 'position': 'OF'},
        {'id': '645277', 'name': 'Juan Soto', 'team': 'NYY', 'position': 'OF'},
    ]
    filtered = [p for p in players if query in p['name'].lower()]
    return jsonify(filtered)

@app.route('/api/player/<player_id>', methods=['GET'])
def get_player_stats(player_id):
    data = SAMPLE_DATA.get(player_id)
    if not data:
        return jsonify({'error': 'Player data not available yet'}), 404
    return jsonify(data)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Baseball Analytics API',
        'version': '1.0',
        'status': 'operational'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
