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
    beer_type = request.args.get('type', '')
    min_abv = request.args.get('min_abv', '')
    max_abv = request.args.get('max_abv', '')
    brewery = request.args.get('brewery', '')
    category_id = request.args.get('category_id', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build the SQL query dynamically based on filters
        sql = """
            SELECT b.name, b.type, b.abv, b.description, br.name as brewery, 
                   br.address, br.city, br.state, br.website,
                   bc.id as category_id, bc.name as category,
                   pc.id as parent_category_id, pc.name as parent_category
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
            LEFT JOIN beer_categories bc ON b.category_id = bc.id
            LEFT JOIN beer_categories pc ON bc.parent_id = pc.id
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
        
        if category_id:
            # Include direct matches and all beers in subcategories
            sql += """ 
                AND (b.category_id = ? OR bc.parent_id = ? OR 
                     EXISTS (
                         SELECT 1 FROM beer_categories subcat
                         WHERE subcat.id = b.category_id AND subcat.parent_id = ?
                     ))
            """
            params.extend([category_id, category_id, category_id])
        
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
                'category_id': row['category_id'],
                'category': row['category'],
                'parent_category_id': row['parent_category_id'],
                'parent_category': row['parent_category']
            })
        
        conn.close()
        
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
        
        # Get categories in hierarchical structure
        cursor.execute("""
            SELECT c.id, c.name, c.parent_id, p.name as parent_name
            FROM beer_categories c
            LEFT JOIN beer_categories p ON c.parent_id = p.id
            ORDER BY 
                CASE WHEN c.parent_id IS NULL THEN 0 ELSE 1 END,
                p.name,
                c.name
        """)
        categories_raw = cursor.fetchall()
        
        # Process categories into a hierarchical structure
        categories = []
        category_map = {}
        
        # First identify and create top-level categories
        for cat in categories_raw:
            if cat['parent_id'] is None:
                category = {
                    'id': cat['id'],
                    'name': cat['name'],
                    'subcategories': []
                }
                categories.append(category)
                category_map[cat['id']] = category
        
        # Then add subcategories to their parents
        for cat in categories_raw:
            if cat['parent_id'] is not None and cat['parent_id'] in category_map:
                subcategory = {
                    'id': cat['id'],
                    'name': cat['name']
                }
                category_map[cat['parent_id']]['subcategories'].append(subcategory)
        
        conn.close()
        
        return jsonify({
            'types': types,
            'abv_range': {'min': abv_range['min_abv'], 'max': abv_range['max_abv']},
            'breweries': breweries,
            'categories': categories
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add a route to get all categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.name, c.parent_id, p.name as parent_name
            FROM beer_categories c
            LEFT JOIN beer_categories p ON c.parent_id = p.id
            ORDER BY 
                CASE WHEN c.parent_id IS NULL THEN 0 ELSE 1 END,
                p.name,
                c.name
        """)
        
        categories = cursor.fetchall()
        
        # Process into hierarchical structure
        hierarchy = []
        category_map = {}
        
        # First pass: add all top-level categories
        for cat in categories:
            if cat['parent_id'] is None:
                category = {
                    'id': cat['id'],
                    'name': cat['name'],
                    'subcategories': []
                }
                hierarchy.append(category)
                category_map[cat['id']] = category
        
        # Second pass: add subcategories
        for cat in categories:
            if cat['parent_id'] is not None and cat['parent_id'] in category_map:
                subcategory = {
                    'id': cat['id'],
                    'name': cat['name']
                }
                category_map[cat['parent_id']]['subcategories'].append(subcategory)
        
        conn.close()
        
        return jsonify({
            'categories': hierarchy
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
            SELECT b.name, b.type, b.abv, br.name as brewery,
                   bc.name as category, pc.name as parent_category
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
            LEFT JOIN beer_categories bc ON b.category_id = bc.id
            LEFT JOIN beer_categories pc ON bc.parent_id = pc.id
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