from flask import Flask, request, jsonify
import sqlite3
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_beers():
    query = request.args.get('q', '')
    
    conn = sqlite3.connect('beers.db')
    cursor = conn.cursor()
    
    # Search by beer name or type
    cursor.execute("""
        SELECT b.name, b.type, b.abv, br.name as brewery, br.address
        FROM beers b
        JOIN beer_locations bl ON b.id = bl.beer_id
        JOIN breweries br ON bl.brewery_id = br.id
        WHERE b.name LIKE ? OR b.type LIKE ?
        AND bl.is_available = 1
        AND br.city = 'Chicago'
    """, (f'%{query}%', f'%{query}%'))
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'results': [
            {
                'beer': r[0],
                'type': r[1],
                'abv': r[2],
                'brewery': r[3],
                'address': r[4]
            } for r in results
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)