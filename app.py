from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
from pybaseball import statcast_batter
import os

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('baseball_analytics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS statcast_cache
                 (player_id TEXT, date_fetched TEXT, data TEXT, 
                  PRIMARY KEY (player_id, date_fetched))''')
    conn.commit()
    conn.close()

init_db()

def calculate_quality_of_contact(df):
    if df.empty:
        return 0
    avg_exit_velo = df['launch_speed'].mean()
    exit_velo_score = min((avg_exit_velo - 80) / 3, 10)
    optimal_angles = df[(df['launch_angle'] >= 10) & (df['launch_angle'] <= 30)]
    optimal_angle_pct = len(optimal_angles) / len(df) * 100 if len(df) > 0 else 0
    angle_score = min(optimal_angle_pct / 5, 10)
    barrel_pct = (df['barrel'] == 1).sum() / len(df) * 100 if len(df) > 0 else 0
    barrel_score = min(barrel_pct * 0.8, 10)
    return round((exit_velo_score * 0.4 + angle_score * 0.3 + barrel_score * 0.3), 1)

def fetch_statcast_data(player_id, start_date, end_date):
    try:
        df = statcast_batter(start_date, end_date, player_id)
        return df
    except:
        return pd.DataFrame()

def process_player_data(df):
    if df.empty:
        return None
    
    batted_balls = df[df['type'] == 'X']
    hits = df[df['events'].isin(['single', 'double', 'triple', 'home_run'])]
    at_bats = df[df['events'].notna()].shape[0]
    avg = len(hits) / at_bats if at_bats > 0 else 0
    
    statcast_metrics = []
    if not batted_balls.empty:
        avg_exit_velo = batted_balls['launch_speed'].mean()
        barrel_pct = (batted_balls['barrel'] == 1).sum() / len(batted_balls) * 100
        hard_hit_pct = (batted_balls['launch_speed'] >= 95).sum() / len(batted_balls) * 100
        
        statcast_metrics = [
            {'metric': 'Exit Velo', 'value': round(avg_exit_velo, 1), 'percentile': min(int((avg_exit_velo - 85) * 5), 99)},
            {'metric': 'Barrel %', 'value': round(barrel_pct, 1), 'percentile': min(int(barrel_pct * 8), 99)},
            {'metric': 'Hard Hit %', 'value': round(hard_hit_pct, 1), 'percentile': min(int(hard_hit_pct * 2), 99)},
        ]
    
    return {
        'basicStats': {'avg': f"{avg:.3f}", 'pa': at_bats, 'hits': len(hits), 'hr': len(df[df['events'] == 'home_run'])},
        'customMetrics': {'qualityOfContact': calculate_quality_of_contact(df), 'plateApproach': 7.5, 'powerEfficiency': 8.2, 'consistencyScore': 7.8},
        'statcastData': statcast_metrics,
        'sprayChart': []
    }

@app.route('/api/search', methods=['GET'])
def search_players():
    query = request.args.get('q', '')
    players = [
        {'id': '592450', 'name': 'Aaron Judge', 'team': 'NYY', 'position': 'RF'},
        {'id': '660271', 'name': 'Shohei Ohtani', 'team': 'LAD', 'position': 'DH'},
        {'id': '605141', 'name': 'Mookie Betts', 'team': 'LAD', 'position': 'RF'},
    ]
    filtered = [p for p in players if query.lower() in p['name'].lower()]
    return jsonify(filtered)

@app.route('/api/player/<player_id>', methods=['GET'])
def get_player_stats(player_id):
    season = request.args.get('season', '2024')
    df = fetch_statcast_data(player_id, f"{season}-04-01", f"{season}-10-01")
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    return jsonify(process_player_data(df))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Baseball Analytics API', 'version': '1.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
