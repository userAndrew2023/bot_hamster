import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def init_conn():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = dict_factory

    return conn


def init_db():
    conn = init_conn()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, telegram_id TEXT, count INTEGER, 
    description TEXT, status TEXT, price FLOAT)''')
    conn.commit()
    conn.close()


def add_order(telegram_id, **kwargs):
    conn = init_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (telegram_id, count, description, status, price) VALUES (?, ?, ?, ?, ?)',
                   (telegram_id, kwargs.get('count'), kwargs.get('description'), 'Новый', kwargs.get('price')))
    last_id = cursor.lastrowid
    cursor.execute('SELECT * FROM orders WHERE id = ?', (last_id,))
    last = cursor.fetchone()
    conn.commit()
    conn.close()

    return last


def confirm_order(id):
    conn = init_conn()
    cursor = conn.cursor()
    cursor.execute(f'UPDATE orders SET status = "Оплачено" WHERE id = {id}')
    conn.commit()
    conn.close()


def get_orders(telegram_id):
    conn = init_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE telegram_id = ?', (telegram_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders
