from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample player data with YOUR custom metrics
SAMPLE_DATA = {
    '592450': {  # Aaron Judge
        'basicStats': {'avg': '.287', 'pa': 550, 'hits': 158, 'hr': 58, 'obp': '.410', 'slg': '.701'},
        'customMetrics': {
            'barrelPercent': 19.8,
            'hardHitPercent': 52.1,
            'groundBallPercent': 35.2,
            'pulledFlyBallPercent': 18.4,
            'maxExitVelocity': 121.1,
            'chasePercent': 23.1,
            'batSpeed': 76.8,
            'zoneContactPercent': 82.4
        },
        'statcastData': [
            {'metric': 'Barrel %', 'value': 19.8, 'percentile': 99, 'league_avg': 8.2},
            {'metric': 'Hard Hit %', 'value': 52.1, 'percentile': 96, 'league_avg': 38.5},
            {'metric': 'Ground Ball %', 'value': 35.2, 'percentile': 78, 'league_avg': 43.8},
            {'metric': 'Pulled FB %', 'value': 18.4, 'percentile': 85, 'league_avg': 12.3},
            {'metric': 'Max EV', 'value': 121.1, 'percentile': 99, 'league_avg': 112.4},
            {'metric': 'Chase %', 'value': 23.1, 'percentile': 72, 'league_avg': 28.9},
            {'metric': 'Bat Speed', 'value': 76.8, 'percentile': 94, 'league_avg': 71.2},
            {'metric': 'Zone Contact %', 'value': 82.4, 'percentile': 81, 'league_avg': 79.8}
        ]
    },
    '660271': {  # Shohei Ohtani
        'basicStats': {'avg': '.310', 'pa': 599, 'hits': 185, 'hr': 54, 'obp': '.390', 'slg': '.646'},
        'customMetrics': {
            'barrelPercent': 16.2,
            'hardHitPercent': 49.8,
            'groundBallPercent': 38.1,
            'pulledFlyBallPercent': 16.8,
            'maxExitVelocity': 119.0,
            'chasePercent': 21.4,
            'batSpeed': 75.9,
            'zoneContactPercent': 85.2
        },
        'statcastData': [
            {'metric': 'Barrel %', 'value': 16.2, 'percentile': 95, 'league_avg': 8.2},
            {'metric': 'Hard Hit %', 'value': 49.8, 'percentile': 92, 'league_avg': 38.5},
            {'metric': 'Ground Ball %', 'value': 38.1, 'percentile': 68, 'league_avg': 43.8},
            {'metric': 'Pulled FB %', 'value': 16.8, 'percentile': 82, 'league_avg': 12.3},
            {'metric': 'Max EV', 'value': 119.0, 'percentile': 97, 'league_avg': 112.4},
            {'metric': 'Chase %', 'value': 21.4, 'percentile': 82, 'league_avg': 28.9},
            {'metric': 'Bat Speed', 'value': 75.9, 'percentile': 91, 'league_avg': 71.2},
            {'metric': 'Zone Contact %', 'value': 85.2, 'percentile': 88, 'league_avg': 79.8}
        ]
    },
    '605141': {  # Mookie Betts
        'basicStats': {'avg': '.289', 'pa': 645, 'hits': 186, 'hr': 38, 'obp': '.372', 'slg': '.579'},
        'customMetrics': {
            'barrelPercent': 13.5,
            'hardHitPercent': 46.2,
            'groundBallPercent': 40.3,
            'pulledFlyBallPercent': 14.2,
            'maxExitVelocity': 115.8,
            'chasePercent': 19.8,
            'batSpeed': 73.4,
            'zoneContactPercent': 87.6
        },
        'statcastData': [
            {'metric': 'Barrel %', 'value': 13.5, 'percentile': 89, 'league_avg': 8.2},
            {'metric': 'Hard Hit %', 'value': 46.2, 'percentile': 85, 'league_avg': 38.5},
            {'metric': 'Ground Ball %', 'value': 40.3, 'percentile': 58, 'league_avg': 43.8},
            {'metric': 'Pulled FB %', 'value': 14.2, 'percentile': 76, 'league_avg': 12.3},
            {'metric': 'Max EV', 'value': 115.8, 'percentile': 88, 'league_avg': 112.4},
            {'metric': 'Chase %', 'value': 19.8, 'percentile': 90, 'league_avg': 28.9},
            {'metric': 'Bat Speed', 'value': 73.4, 'percentile': 78, 'league_avg': 71.2},
            {'metric': 'Zone Contact %', 'value': 87.6, 'percentile': 92, 'league_avg': 79.8}
        ]
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
    return jsonify({'status': 'healthy', 'version': '2.0'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Baseball Analytics API - Custom Metrics',
        'version': '2.0',
        'metrics': [
            'Barrel %', 'Hard Hit %', 'Ground Ball %', 
            'Pulled Fly Ball %', 'Max Exit Velocity', 
            'Chase %', 'Bat Speed', 'Zone Contact %'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
