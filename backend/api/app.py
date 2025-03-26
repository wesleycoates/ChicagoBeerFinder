from flask import Flask, request, jsonify
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all domains
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
    
    if not query:
        return jsonify({'error': 'No search query provided', 'results': []}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search by beer name or type
        cursor.execute("""
            SELECT b.name, b.type, b.abv, b.description, br.name as brewery, 
                   br.address, br.city, br.state, br.website
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
            WHERE (b.name LIKE ? OR b.type LIKE ?)
            AND bl.is_available = 1
        """, (f'%{query}%', f'%{query}%'))
        
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
                'website': row['website']
            })
        
        conn.close()
        
        return jsonify({
            'results': result_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'results': []}), 500

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

# Make sure we can run this directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)