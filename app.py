from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import urllib.request
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)

def fetch_statcast_csv(player_id, season='2024'):
    """Fetch Statcast data directly from Baseball Savant CSV export"""
    url = f"https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea={season}%7C&hfSit=&player_type=batter&hfOuts=&opponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfInfield=&team=&position=&hfOutfield=&hfRO=&home_road=&batters_lookup%5B%5D={player_id}&hfFlag=&hfBBT=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&min_pas=0&type=details"
    
    print(f"Fetching data for player {player_id} from Baseball Savant...")
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            csv_data = response.read().decode('utf-8')
            print(f"Received {len(csv_data)} characters of CSV data")
            
            # Check if we got actual data
            lines = csv_data.split('\n')
            print(f"CSV has {len(lines)} lines")
            
            if len(lines) < 2:
                print("CSV is empty or has no data rows")
                return None
            
            return csv_data
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

@app.route('/api/player/<player_id>', methods=['GET'])
def get_player_stats(player_id):
    season = request.args.get('season', '2024')
    
    print(f"API request for player {player_id}, season {season}")
    
    # For now, let's just test if we can fetch the CSV
    csv_data = fetch_statcast_csv(player_id, season)
    
    if csv_data:
        return jsonify({
            'status': 'success',
            'data_length': len(csv_data),
            'preview': csv_data[:500]  # First 500 chars to see what we got
        })
    
    return jsonify({'error': 'Unable to fetch player data', 'player_id': player_id}), 404

@app.route('/api/search', methods=['GET'])
def search_players():
    query = request.args.get('q', '').lower()
    players = [
        {'id': '592450', 'name': 'Aaron Judge', 'team': 'NYY', 'position': 'RF'},
        {'id': '660271', 'name': 'Shohei Ohtani', 'team': 'LAD', 'position': 'DH'},
        {'id': '605141', 'name': 'Mookie Betts', 'team': 'LAD', 'position': 'RF'},
    ]
    filtered = [p for p in players if query in p['name'].lower()]
    return jsonify(filtered)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '3.0-debug'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Baseball Analytics API - Debug Mode'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
