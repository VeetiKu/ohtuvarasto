import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def _safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


@app.teardown_appcontext
def close_connection(_exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                capacity REAL DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity REAL DEFAULT 0,
                description TEXT,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses (id)
            )
        ''')
        db.commit()


@app.route('/')
def index():
    db = get_db()
    warehouses = db.execute('SELECT * FROM warehouses').fetchall()
    return render_template('index.html', warehouses=warehouses)


@app.route('/warehouse/new', methods=['GET', 'POST'])
def new_warehouse():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location', '')
        capacity = request.form.get('capacity', 0)
        db = get_db()
        db.execute(
            'INSERT INTO warehouses (name, location, capacity) '
            'VALUES (?, ?, ?)',
            (name, location, _safe_float(capacity))
        )
        db.commit()
        return redirect(url_for('index'))
    return render_template('warehouse_form.html', warehouse=None)


@app.route('/warehouse/<int:warehouse_id>')
def view_warehouse(warehouse_id):
    db = get_db()
    warehouse = db.execute(
        'SELECT * FROM warehouses WHERE id = ?',
        (warehouse_id,)
    ).fetchone()
    if warehouse is None:
        return redirect(url_for('index'))
    items = db.execute(
        'SELECT * FROM items WHERE warehouse_id = ?',
        (warehouse_id,)
    ).fetchall()
    return render_template(
        'warehouse_view.html',
        warehouse=warehouse,
        items=items
    )


@app.route('/warehouse/<int:warehouse_id>/edit', methods=['GET', 'POST'])
def edit_warehouse(warehouse_id):
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location', '')
        capacity = request.form.get('capacity', 0)
        db.execute(
            'UPDATE warehouses SET name = ?, location = ?, capacity = ? '
            'WHERE id = ?',
            (name, location, _safe_float(capacity), warehouse_id)
        )
        db.commit()
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))
    warehouse = db.execute(
        'SELECT * FROM warehouses WHERE id = ?',
        (warehouse_id,)
    ).fetchone()
    if warehouse is None:
        return redirect(url_for('index'))
    return render_template('warehouse_form.html', warehouse=warehouse)


@app.route('/warehouse/<int:warehouse_id>/delete', methods=['POST'])
def delete_warehouse(warehouse_id):
    db = get_db()
    db.execute('DELETE FROM items WHERE warehouse_id = ?', (warehouse_id,))
    db.execute('DELETE FROM warehouses WHERE id = ?', (warehouse_id,))
    db.commit()
    return redirect(url_for('index'))


@app.route('/warehouse/<int:warehouse_id>/item/new', methods=['GET', 'POST'])
def new_item(warehouse_id):
    db = get_db()
    warehouse = db.execute(
        'SELECT * FROM warehouses WHERE id = ?',
        (warehouse_id,)
    ).fetchone()
    if warehouse is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form.get('quantity', 0)
        description = request.form.get('description', '')
        db.execute(
            'INSERT INTO items (warehouse_id, name, quantity, description) '
            'VALUES (?, ?, ?, ?)',
            (warehouse_id, name, _safe_float(quantity), description)
        )
        db.commit()
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))
    return render_template(
        'item_form.html',
        warehouse=warehouse,
        item=None
    )


def _get_warehouse(db, warehouse_id):
    return db.execute(
        'SELECT * FROM warehouses WHERE id = ?',
        (warehouse_id,)
    ).fetchone()


def _handle_item_update(db, warehouse_id, item_id):
    name = request.form['name']
    quantity = request.form.get('quantity', 0)
    description = request.form.get('description', '')
    db.execute(
        'UPDATE items SET name = ?, quantity = ?, description = ? '
        'WHERE id = ? AND warehouse_id = ?',
        (name, _safe_float(quantity), description, item_id, warehouse_id)
    )
    db.commit()


@app.route('/warehouse/<int:warehouse_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def edit_item(warehouse_id, item_id):
    db = get_db()
    warehouse = _get_warehouse(db, warehouse_id)
    if warehouse is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        _handle_item_update(db, warehouse_id, item_id)
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))
    item = db.execute(
        'SELECT * FROM items WHERE id = ? AND warehouse_id = ?',
        (item_id, warehouse_id)
    ).fetchone()
    if item is None:
        return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))
    return render_template('item_form.html', warehouse=warehouse, item=item)


@app.route('/warehouse/<int:warehouse_id>/item/<int:item_id>/delete',
           methods=['POST'])
def delete_item(warehouse_id, item_id):
    db = get_db()
    db.execute(
        'DELETE FROM items WHERE id = ? AND warehouse_id = ?',
        (item_id, warehouse_id)
    )
    db.commit()
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


if __name__ == '__main__':
    init_db()
    app.run(debug=False)
