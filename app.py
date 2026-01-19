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
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            csv_data = response.read().decode('utf-8-sig')  # Handle BOM
            return csv_data
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

def calculate_metrics_from_csv(csv_data):
    """Calculate custom metrics from CSV data"""
    if not csv_data:
        return None
    
    try:
        reader = csv.DictReader(StringIO(csv_data))
        rows = list(reader)
        
        if not rows:
            return None
        
        # Filter for batted balls (type = 'X' means ball in play)
        batted_balls = [r for r in rows if r.get('type') == 'X' and r.get('launch_speed') and r.get('launch_speed').strip()]
        
        total_bb = len(batted_balls)
        
        if total_bb == 0:
            return None
        
        # Barrel %
        barrels = sum(1 for r in batted_balls if r.get('barrel') == '1')
        barrel_pct = (barrels / total_bb * 100)
        
        # Hard Hit % (95+ mph)
        hard_hits = sum(1 for r in batted_balls if float(r.get('launch_speed', 0) or 0) >= 95)
        hard_hit_pct = (hard_hits / total_bb * 100)
        
        # Ground Ball %
        ground_balls = sum(1 for r in batted_balls if r.get('bb_type') == 'ground_ball')
        gb_pct = (ground_balls / total_bb * 100)
        
        # Pulled Fly Ball %
        fly_balls = [r for r in batted_balls if r.get('bb_type') == 'fly_ball']
        # Hit locations 7,8,9 are pulled for righties; 1,2,3 for lefties
        # For simplicity, count all pulled fly balls
        pulled_fb = sum(1 for r in fly_balls if r.get('hit_location') in ['7', '8', '9'])
        pulled_fb_pct = (pulled_fb / total_bb * 100)
        
        # Max Exit Velocity
        exit_velos = [float(r.get('launch_speed', 0) or 0) for r in batted_balls if r.get('launch_speed')]
        max_ev = max(exit_velos) if exit_velos else 0
        avg_ev = sum(exit_velos) / len(exit_velos) if exit_velos else 0
        
        # Chase % (swings at pitches outside zone)
        all_pitches = [r for r in rows if r.get('zone') and r.get('zone').strip()]
        chase_pitches = [r for r in all_pitches if r.get('zone') and r.get('zone').strip() and int(float(r['zone'])) > 9]
        chase_swings = sum(1 for r in chase_pitches if r.get('description') and 'swing' in r.get('description', '').lower())
        chase_pct = (chase_swings / len(chase_pitches) * 100) if chase_pitches else 0
        
        # Zone Contact %
        zone_pitches = [r for r in all_pitches if r.get('zone') and r.get('zone').strip() and int(float(r['zone'])) <= 9]
        zone_swings = [r for r in zone_pitches if r.get('description') and 'swing' in r.get('description', '').lower()]
        zone_contact = sum(1 for r in zone_swings if r.get('description') in ['foul', 'hit_into_play', 'foul_tip'])
        zone_contact_pct = (zone_contact / len(zone_swings) * 100) if zone_swings else 0
        
        # Bat Speed (average from available data)
        bat_speeds = [float(r.get('bat_speed', 0) or 0) for r in batted_balls if r.get('bat_speed') and r.get('bat_speed').strip() and float(r.get('bat_speed', 0)) > 0]
        avg_bat_speed = (sum(bat_speeds) / len(bat_speeds)) if bat_speeds else 0
        
        # Basic stats
        hits = sum(1 for r in rows if r.get('events') in ['single', 'double', 'triple', 'home_run'])
        hrs = sum(1 for r in rows if r.get('events') == 'home_run')
        doubles = sum(1 for r in rows if r.get('events') == 'double')
        triples = sum(1 for r in rows if r.get('events') == 'triple')
        abs_count = len([r for r in rows if r.get('events') and r.get('events').strip()])
        avg = (hits / abs_count) if abs_count > 0 else 0
        
        # Calculate percentiles (approximate)
        barrel_percentile = min(int(barrel_pct * 8), 99)
        hard_hit_percentile = min(int(hard_hit_pct * 2), 99)
        gb_percentile = max(100 - int(gb_pct * 2), 1)  # Lower GB% is better
        pulled_fb_percentile = min(int(pulled_fb_pct * 6), 99)
        max_ev_percentile = min(int((max_ev - 100) * 8), 99)
        chase_percentile = max(100 - int(chase_pct * 3), 1)  # Lower chase is better
        bat_speed_percentile = min(int((avg_bat_speed - 65) * 8), 99) if avg_bat_speed > 0 else 50
        zone_contact_percentile = min(int(zone_contact_pct * 1.2), 99)
        
        return {
            'basicStats': {
                'avg': f"{avg:.3f}",
                'pa': len(rows),
                'hits': hits,
                'hr': hrs,
                '2b': doubles,
                '3b': triples
            },
            'customMetrics': {
                'barrelPercent': round(barrel_pct, 1),
                'hardHitPercent': round(hard_hit_pct, 1),
                'groundBallPercent': round(gb_pct, 1),
                'pulledFlyBallPercent': round(pulled_fb_pct, 1),
                'maxExitVelocity': round(max_ev, 1),
                'chasePercent': round(chase_pct, 1),
                'batSpeed': round(avg_bat_speed, 1) if avg_bat_speed > 0 else 73.5,
                'zoneContactPercent': round(zone_contact_pct, 1)
            },
            'statcastData': [
                {'metric': 'Barrel %', 'value': round(barrel_pct, 1), 'percentile': barrel_percentile, 'league_avg': 8.2},
                {'metric': 'Hard Hit %', 'value': round(hard_hit_pct, 1), 'percentile': hard_hit_percentile, 'league_avg': 38.5},
                {'metric': 'Ground Ball %', 'value': round(gb_pct, 1), 'percentile': gb_percentile, 'league_avg': 43.8},
                {'metric': 'Pulled FB %', 'value': round(pulled_fb_pct, 1), 'percentile': pulled_fb_percentile, 'league_avg': 12.3},
                {'metric': 'Max EV', 'value': round(max_ev, 1), 'percentile': max_ev_percentile, 'league_avg': 112.4},
                {'metric': 'Chase %', 'value': round(chase_pct, 1), 'percentile': chase_percentile, 'league_avg': 28.9},
                {'metric': 'Bat Speed', 'value': round(avg_bat_speed, 1) if avg_bat_speed > 0 else 73.5, 'percentile': bat_speed_percentile, 'league_avg': 71.2},
                {'metric': 'Zone Contact %', 'value': round(zone_contact_pct, 1), 'percentile': zone_contact_percentile, 'league_avg': 79.8}
            ],
            'sprayChart': []
        }
    except Exception as e:
        print(f"Error calculating metrics: {str(e)}")
        return None

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
    season = request.args.get('season', '2024')
    
    csv_data = fetch_statcast_csv(player_id, season)
    
    if csv_data:
        metrics = calculate_metrics_from_csv(csv_data)
        if metrics:
            return jsonify(metrics)
    
    return jsonify({'error': 'Unable to fetch player data'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '3.0 - Real Statcast'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Baseball Analytics API - Real Statcast Data',
        'version': '3.0',
        'data_source': 'Baseball Savant'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
