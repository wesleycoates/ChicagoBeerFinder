from flask import Flask, request, jsonify
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_beer_client import LocalBeerClient
from flask_cors import CORS
from local_beer_client import LocalBeerClient

app = Flask(__name__)
# Enable CORS for all domains
CORS(app, resources={r"/api/*": {"origins": "*"}})

beer_client = LocalBeerClient()

# Helper function to get database connection
def get_db_connection():
    # Go up one level from the api folder to the backend folder
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'beers.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.route('/api/search', methods=['GET'])
def search_beers():
    query = request.args.get('q', '')
    beer_type = request.args.get('type', '')
    min_abv = request.args.get('min_abv', '')
    max_abv = request.args.get('max_abv', '')
    brewery = request.args.get('brewery', '')
    
    # Flag to determine whether to include beer data
    include_beer_data = request.args.get('include_beer_data', 'true').lower() == 'true'

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build the SQL query dynamically based on filters
        sql = """
            SELECT b.name, b.type, b.abv, b.description, br.name as brewery, 
                   br.address, br.city, br.state, br.website
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
            WHERE bl.is_available = 1
        """
        
        params = []
        
        # Add conditions based on filters
        if query:
            sql += " AND (b.name LIKE ? OR b.description LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%'])
        
        if beer_type:
            sql += " AND b.type LIKE ?"
            params.append(f'%{beer_type}%')
        
        if min_abv:
            sql += " AND b.abv >= ?"
            params.append(float(min_abv))
        
        if max_abv:
            sql += " AND b.abv <= ?"
            params.append(float(max_abv))
        
        if brewery:
            sql += " AND br.name LIKE ?"
            params.append(f'%{brewery}%')
        
        cursor.execute(sql, params)
        
        results = cursor.fetchall()
        
        # Convert results to dictionary
        result_list = []
        for row in results:
            result_list.append({
                'beer': row['name'],
                'type': row['type'],
                'abv': row['abv'],
                'description': row['description'],
                'brewery': row['brewery'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'website': row['website'],
                'source': 'local'
            })
        
        conn.close()
        
        # If we have brewery results but no beer data and we want to include beer data
        if include_beer_data and brewery:
            # Search for beers to associate with the brewery
            beer_results = beer_client.get_all_beers(per_page=5)
            
            # Add these beers to the results
            for beer in beer_results:
                result_list.append({
                    'beer': beer['name'],
                    'type': beer.get('style', beer.get('tagline', '')),
                    'abv': beer.get('abv', 0),
                    'description': beer.get('description', ''),
                    'brewery': brewery,  # Associate with the searched brewery
                    'image_url': beer.get('image_url'),
                    'food_pairing': beer.get('food_pairing', []),
                    'beer_id': beer.get('id'),
                    'source': 'beer_database'
                })
        
        # If we're searching for a beer name and we want to include beer data
        elif include_beer_data and query and not result_list:
            # Search for beers by name
            beer_results = beer_client.search_beers_by_name(query)
            
            # Add these beers to the results
            for beer in beer_results:
                result_list.append({
                    'beer': beer['name'],
                    'type': beer.get('style', beer.get('tagline', '')),
                    'abv': beer.get('abv', 0),
                    'description': beer.get('description', ''),
                    'brewery': 'BrewDog',  # Default brewery for our beer data
                    'image_url': beer.get('image_url'),
                    'food_pairing': beer.get('food_pairing', []),
                    'beer_id': beer.get('id'),
                    'source': 'beer_database'
                })

        return jsonify({
            'results': result_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'results': []}), 500

@app.route('/api/filters', methods=['GET'])
def get_filters():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get unique beer types
        cursor.execute("SELECT DISTINCT type FROM beers ORDER BY type")
        types = [row['type'] for row in cursor.fetchall()]
        
        # Get min and max ABV
        cursor.execute("SELECT MIN(abv) as min_abv, MAX(abv) as max_abv FROM beers")
        abv_range = cursor.fetchone()
        
        # Get breweries
        cursor.execute("SELECT DISTINCT name FROM breweries ORDER BY name")
        breweries = [row['name'] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'types': types,
            'abv_range': {'min': abv_range['min_abv'], 'max': abv_range['max_abv']},
            'breweries': breweries
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to list all beers (for testing)
@app.route('/api/beers', methods=['GET'])
def list_beers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.name, b.type, b.abv, br.name as brewery
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
        """)
        
        results = cursor.fetchall()
        result_list = [dict(row) for row in results]
        
        conn.close()
        
        return jsonify({
            'beers': result_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'beers': []}), 500

# Add a simple root route for testing
@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Chicago Beer Finder API is running'})

@app.route('/api/beer/<beer_id>', methods=['GET'])
def get_beer_details(beer_id):
    """Get detailed information about a specific beer."""
    try:
        result = beer_client.get_beer(beer_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/beers/random', methods=['GET'])
def get_random_beer():
    """Get a random beer."""
    try:
        result = beer_client.get_random_beer()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/beers', methods=['GET'])
def list_all_beers():
    """Get a list of beers with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        result = beer_client.get_all_beers(page=page, per_page=per_page)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/beers/by_abv', methods=['GET'])
def get_beers_by_abv():
    """Get beers by ABV range."""
    try:
        min_abv = request.args.get('min_abv', type=float)
        max_abv = request.args.get('max_abv', type=float)
        page = request.args.get('page', 1, type=int)
        result = beer_client.search_beers_by_abv(min_abv=min_abv, max_abv=max_abv, page=page)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/beers/by_food', methods=['GET'])
def get_beers_by_food():
    """Get beers that pair with a specific food."""
    try:
        food = request.args.get('food', '')
        if not food:
            return jsonify({'error': 'Food parameter is required'}), 400
            
        result = beer_client.search_beers_by_food(food)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Make sure we can run this directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)