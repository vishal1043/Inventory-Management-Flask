from flask import Flask, render_template, request, redirect, url_for
import pymysql
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
from utils import generate_id
from flask import jsonify

app = Flask(__name__)

db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DB)
cursor = db.cursor()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/product', methods=['GET', 'POST'])
def product():
    if request.method == 'POST':
        product_id = generate_id('pd')
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        location_id = request.form['location_id'] 
        # 1) Insert product (same as before)
        cursor.execute("INSERT INTO product VALUES (%s, %s, %s, %s)", (product_id, name, quantity, price))
        # 2) Record initial stock at a specific location
        cursor.execute("""
            INSERT INTO productmovement (product_id, from_location, to_location, qty)
            VALUES (%s, %s, %s, %s)
        """, (product_id, None, location_id, quantity))
        db.commit()
    
    # All locations (for dropdown in form)
    cursor.execute("SELECT * FROM location")
    # products = cursor.fetchall()
    locations = cursor.fetchall()
    # return render_template('product.html', products=products)
    # Show product + location-wise quantity
    query = """
        SELECT
            p.product_id,
            p.name,
            p.price,
            l.name AS location_name,
            SUM(
                CASE
                    WHEN m.to_location = l.location_id THEN m.qty
                    WHEN m.from_location = l.location_id THEN -m.qty
                    ELSE 0
                END
            ) AS qty
        FROM product p
        LEFT JOIN productmovement m ON p.product_id = m.product_id
        LEFT JOIN location l ON l.location_id = m.to_location OR l.location_id = m.from_location
        GROUP BY p.product_id, p.name, p.price, l.location_id, l.name
        HAVING qty IS NOT NULL AND qty >= 0
        ORDER BY p.product_id, l.name
    """
    cursor.execute(query)
    product_rows = cursor.fetchall()
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()

    return render_template(
        'product.html',
        locations=locations,
        product_rows=product_rows,
        products=products
    )

@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        location_id = generate_id('lc')
        name = request.form['name']
        cursor.execute("INSERT INTO location VALUES (%s, %s)", (location_id, name))
        db.commit()
    cursor.execute("SELECT * FROM location")
    locations = cursor.fetchall()
    return render_template('location.html', locations=locations)

# @app.route('/movement', methods=['GET', 'POST'])
# def movement():
#     cursor.execute("SELECT * FROM product")
#     products = cursor.fetchall()
#     cursor.execute("SELECT * FROM location")
#     locations = cursor.fetchall()
#     message = None

#     if request.method == 'POST':
#         product_id = request.form['product_id']
#         from_location = request.form['from_location'] or None
#         to_location = request.form['to_location'] or None
#         qty = int(request.form['qty'])

#         cursor.execute("SELECT quantity FROM product WHERE product_id = %s", (product_id,))
#         result = cursor.fetchone()
#         available_qty = result[0] if result else 0
#         val = int(qty-available_qty)
        
#         if from_location and qty > available_qty:
#             message = f"Error: Only {available_qty} units. we want {val} more units."
#         else:
#             cursor.execute("""
#                 INSERT INTO productmovement (product_id, from_location, to_location, qty)
#                 VALUES (%s, %s, %s, %s)
#             """, (product_id, from_location, to_location, qty))

#             if from_location:
#                 cursor.execute("UPDATE product SET quantity = quantity - %s WHERE product_id = %s", (qty, product_id))
#             if to_location and not from_location:
#                 cursor.execute("UPDATE product SET quantity = quantity + %s WHERE product_id = %s", (qty, product_id))

#             db.commit()
#             message = "Movement recorded successfully."

#     cursor.execute("""
#         SELECT 
#             m.movement_id, 
#             m.timestamp, 
#             p.name, 
#             lf.name AS from_location, 
#             lt.name AS to_location, 
#             m.qty
#         FROM productmovement m
#         JOIN product p ON m.product_id = p.product_id
#         LEFT JOIN location lf ON m.from_location = lf.location_id
#         LEFT JOIN location lt ON m.to_location = lt.location_id
#         ORDER BY m.timestamp DESC
#     """)
#     movements = cursor.fetchall()
#     return render_template('movement.html', products=products, locations=locations, movements=movements, message=message)

@app.route('/movement', methods=['GET', 'POST'])
def movement():
    # Get all products and locations for dropdowns
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM location")
    locations = cursor.fetchall()

    message = None

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        qty = int(request.form['qty'])

        # If moving OUT from a location -> check stock at that location
        if from_location:
            cursor.execute("""
                SELECT COALESCE(SUM(
                    CASE
                        WHEN m.to_location = %s THEN m.qty
                        WHEN m.from_location = %s THEN -m.qty
                        ELSE 0
                    END
                ), 0) AS qty
                FROM productmovement m
                WHERE m.product_id = %s
            """, (from_location, from_location, product_id))
            result = cursor.fetchone()
            available_qty = result[0] if result else 0

            if qty > available_qty:
                diff = qty - available_qty
                message = f"Error: Only {available_qty} units available at this location. Need {diff} more units."
            else:
                # Record movement
                cursor.execute("""
                    INSERT INTO productmovement (product_id, from_location, to_location, qty)
                    VALUES (%s, %s, %s, %s)
                """, (product_id, from_location, to_location, qty))

                # Total quantity update only when stock leaves/enters system
                if from_location and not to_location:
                    # Going out of inventory
                    cursor.execute(
                        "UPDATE product SET quantity = quantity - %s WHERE product_id = %s",
                        (qty, product_id)
                    )
                elif to_location and not from_location:
                    # Coming into inventory
                    cursor.execute(
                        "UPDATE product SET quantity = quantity + %s WHERE product_id = %s",
                        (qty, product_id)
                    )
                # Internal transfer (from & to set) -> no total change

                db.commit()
                message = "Movement recorded successfully."
        else:
            # No from_location: this is "Initial Stock" or new stock coming IN
            cursor.execute("""
                INSERT INTO productmovement (product_id, from_location, to_location, qty)
                VALUES (%s, %s, %s, %s)
            """, (product_id, None, to_location, qty))

            # Increase total stock
            if to_location:
                cursor.execute(
                    "UPDATE product SET quantity = quantity + %s WHERE product_id = %s",
                    (qty, product_id)
                )

            db.commit()
            message = "Movement recorded successfully."

    # Movement history (same as your old one)
    cursor.execute("""
        SELECT 
            m.movement_id, 
            m.timestamp, 
            p.name, 
            lf.name AS from_location, 
            lt.name AS to_location, 
            m.qty
        FROM productmovement m
        JOIN product p ON m.product_id = p.product_id
        LEFT JOIN location lf ON m.from_location = lf.location_id
        LEFT JOIN location lt ON m.to_location = lt.location_id
        ORDER BY m.timestamp DESC
    """)
    movements = cursor.fetchall()

    return render_template(
        'movement.html',
        products=products,
        locations=locations,
        movements=movements,
        message=message
    )



@app.route('/report')
def report():
    query = """
        SELECT
            p.product_id,
            p.name AS product_name,
            l.name AS location_name,
            SUM(
                CASE
                    WHEN m.to_location = l.location_id THEN m.qty
                    WHEN m.from_location = l.location_id THEN -m.qty
                    ELSE 0
                END
            ) AS qty
        FROM product p
        JOIN productmovement m ON p.product_id = m.product_id
        JOIN location l ON l.location_id = m.to_location OR l.location_id = m.from_location
        GROUP BY p.product_id, p.name, l.location_id, l.name
        HAVING qty >= 0
        ORDER BY p.product_id, l.name
    """
    cursor.execute(query)
    report_data = cursor.fetchall()
    return render_template('report.html', report_data=report_data)

@app.route('/product/<product_id>/available-locations')
def available_locations(product_id):
    query = """
        SELECT
            l.location_id,
            l.name,
            COALESCE(SUM(
                CASE
                    WHEN m.to_location = l.location_id THEN m.qty
                    WHEN m.from_location = l.location_id THEN -m.qty
                    ELSE 0
                END
            ), 0) AS qty
        FROM location l
        JOIN productmovement m
          ON l.location_id = m.to_location OR l.location_id = m.from_location
        WHERE m.product_id = %s
        GROUP BY l.location_id, l.name
        HAVING qty > 0
        ORDER BY l.name
    """
    cursor.execute(query, (product_id,))
    rows = cursor.fetchall()

    locations = [
        {"id": row[0], "name": row[1], "qty": row[2]}
        for row in rows
    ]
    return jsonify(locations)

# ===================== DELETE PRODUCT (AJAX) =====================
@app.route('/product/delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # delete related product movements first (to avoid FK issues)
        cursor.execute("DELETE FROM productmovement WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM product WHERE product_id = %s", (product_id,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ===================== DELETE LOCATION (AJAX) =====================
@app.route('/location/delete/<location_id>', methods=['DELETE'])
def delete_location(location_id):
    try:
        # Optional: also delete movements related to this location
        cursor.execute("""
            DELETE FROM productmovement
            WHERE from_location = %s OR to_location = %s
        """, (location_id, location_id))

        cursor.execute("DELETE FROM location WHERE location_id = %s", (location_id,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
