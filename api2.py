import os
import sqlite3
from flask import Flask, jsonify, request, g
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return jsonify({"message": "Chicago Beer Finder API", "status": "running"})


# Database path - adjust as needed
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'beers.db')

def get_db():
    """Get database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row  # Return rows as dictionaries
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection when app context ends."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def dict_factory(cursor, row):
    """Convert SQL rows to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

# Main search endpoint used by the frontend
@app.route('/api/search', methods=['GET'])
def search_beers():
    """Search beers with optional filters."""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Get query parameters
    query = request.args.get('q', '')
    beer_type = request.args.get('type', '')
    min_abv = request.args.get('min_abv', '')
    max_abv = request.args.get('max_abv', '')
    brewery = request.args.get('brewery', '')
    category_id = request.args.get('category_id', '')
    
    # Base query
    sql_query = """
        SELECT 
            b.id as beer_id,
            b.name as beer,
            b.type as type,
            b.abv as abv,
            b.description as description,
            br.name as brewery,
            br.location as address,
            COALESCE(SUBSTR(br.location, INSTR(br.location, ', ') + 2), 'IL') as state,
            COALESCE(SUBSTR(br.location, 1, INSTR(br.location, ', ') - 1), 'Chicago') as city,
            br.website as website,
            c.name as category,
            pc.name as parent_category
        FROM beers b
        JOIN breweries br ON b.brewery_id = br.id
        LEFT JOIN beer_categories c ON b.category_id = c.id
        LEFT JOIN beer_categories pc ON c.parent_id = pc.id
        WHERE 1=1
    """
    
    params = []
    
    # Add search filter
    if query:
        sql_query += " AND (b.name LIKE ? OR b.description LIKE ? OR b.type LIKE ?)"
        search_pattern = f"%{query}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    # Add type filter
    if beer_type:
        sql_query += " AND b.type LIKE ?"
        params.append(f"%{beer_type}%")
    
    # Add ABV filters
    if min_abv:
        sql_query += " AND b.abv >= ?"
        params.append(float(min_abv))
    
    if max_abv:
        sql_query += " AND b.abv <= ?"
        params.append(float(max_abv))
    
    # Add brewery filter
    if brewery:
        sql_query += " AND br.name LIKE ?"
        params.append(f"%{brewery}%")
    
    # Add category filter with subcategories support
    if category_id:
        # Get all subcategories of the selected category
        cursor.execute("""
            WITH RECURSIVE subcategories AS (
                SELECT id FROM beer_categories WHERE id = ?
                UNION
                SELECT bc.id FROM beer_categories bc
                JOIN subcategories sc ON bc.parent_id = sc.id
            )
            SELECT id FROM subcategories
        """, (category_id,))
        
        category_ids = [row['id'] for row in cursor.fetchall()]
        if category_ids:
            placeholders = ','.join('?' for _ in category_ids)
            sql_query += f" AND b.category_id IN ({placeholders})"
            params.extend(category_ids)
    
    # Add ordering
    sql_query += " ORDER BY b.name"
    
    # Execute query
    cursor.execute(sql_query, params)
    results = cursor.fetchall()
    
    return jsonify({
        "results": results
    })

# Get filter options for the frontend
@app.route('/api/filters', methods=['GET'])
def get_filter_options():
    """Get all possible filter options."""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Get unique beer types
    cursor.execute("SELECT DISTINCT type FROM beers WHERE type IS NOT NULL AND type != '' ORDER BY type")
    types = [row['type'] for row in cursor.fetchall()]
    
    # Get ABV range
    cursor.execute("SELECT MIN(abv) as min, MAX(abv) as max FROM beers WHERE abv IS NOT NULL")
    abv_range = cursor.fetchone()
    
    if not abv_range['min']:
        abv_range['min'] = 0
    if not abv_range['max']:
        abv_range['max'] = 15
    
    # Get brewery names
    cursor.execute("SELECT name FROM breweries ORDER BY name")
    breweries = [row['name'] for row in cursor.fetchall()]
    
    # Get categories with hierarchical structure
    cursor.execute("""
        SELECT id, name, parent_id 
        FROM beer_categories 
        WHERE parent_id IS NULL
        ORDER BY name
    """)
    parent_categories = cursor.fetchall()
    
    categories = []
    for parent in parent_categories:
        # Get subcategories
        cursor.execute("""
            SELECT id, name 
            FROM beer_categories 
            WHERE parent_id = ? 
            ORDER BY name
        """, (parent['id'],))
        
        subcategories = cursor.fetchall()
        
        category = {
            'id': parent['id'],
            'name': parent['name'],
            'subcategories': subcategories
        }
        
        categories.append(category)
    
    return jsonify({
        'types': types,
        'abv_range': abv_range,
        'breweries': breweries,
        'categories': categories
    })

# Get all breweries for the map view
@app.route('/api/breweries', methods=['GET'])
def get_breweries():
    """Get all breweries."""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            br.id,
            br.name,
            br.location as address,
            COALESCE(SUBSTR(br.location, INSTR(br.location, ', ') + 2), 'IL') as state,
            COALESCE(SUBSTR(br.location, 1, INSTR(br.location, ', ') - 1), 'Chicago') as city,
            br.website,
            br.description,
            41.8781 as lat,  -- Default to Chicago's coordinates for demo
            -87.6298 as lng,
            (SELECT COUNT(*) FROM beers WHERE brewery_id = br.id) as beer_count
        FROM breweries br
    """)
    
    breweries = cursor.fetchall()
    
    # For each brewery, get their beers
    for brewery in breweries:
        cursor.execute("""
            SELECT 
                b.name,
                b.type,
                b.abv,
                b.description,
                c.name as category
            FROM beers b
            LEFT JOIN beer_categories c ON b.category_id = c.id
            WHERE b.brewery_id = ?
            ORDER BY b.name
        """, (brewery['id'],))
        
        brewery['beers'] = cursor.fetchall()
    
    return jsonify({
        "breweries": breweries
    })

# Get details for a specific beer
@app.route('/api/beer/<int:beer_id>', methods=['GET'])
def get_beer_detail(beer_id):
    """Get detailed information about a specific beer."""
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            b.id as beer_id,
            b.name as beer,
            b.type as type,
            b.abv as abv,
            b.description as description,
            br.name as brewery,
            br.location as address,
            COALESCE(SUBSTR(br.location, INSTR(br.location, ', ') + 2), 'IL') as state,
            COALESCE(SUBSTR(br.location, 1, INSTR(br.location, ', ') - 1), 'Chicago') as city,
            br.website as website,
            c.name as category,
            pc.name as parent_category
        FROM beers b
        JOIN breweries br ON b.brewery_id = br.id
        LEFT JOIN beer_categories c ON b.category_id = c.id
        LEFT JOIN beer_categories pc ON c.parent_id = pc.id
        WHERE b.id = ?
    """, (beer_id,))
    
    beer = cursor.fetchone()
    
    if not beer:
        return jsonify({"error": "Beer not found"}), 404
    
    return jsonify([beer])  # Return as array for compatibility with existing frontend

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
