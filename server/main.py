import mysql.connector
import threading
import time
from timeit import default_timer as timer

connections = {}

class ConnectionGarbageCollector(threading.Thread):
    lock = threading.Lock()

    def __init__(self, cycle_length):
        super().__init__(daemon=True)
        self.cycle_length = cycle_length
        self.start()

    def run(self):
        while True:
            time.sleep(self.cycle_length)
            with ConnectionGarbageCollector.lock:
                dead_thread_ids = []
                for thread_id in connections:
                    for thread in threading.enumerate():
                        alive = thread.ident == thread_id
                        if alive:
                            break
                    if not alive:
                        dead_thread_ids.append(thread_id)

                for thread_id in dead_thread_ids:
                    connections[thread_id].close()
                    del connections[thread_id]
                if dead_thread_ids:
                    print("Cleaned up {} connection{}!".format(len(dead_thread_ids), 's' * (len(dead_thread_ids) != 1)))

ConnectionGarbageCollector(10)

def get_db_connection():
    global connections
    thread_id = threading.get_ident()

    with ConnectionGarbageCollector.lock:
        if thread_id in connections and not connections[thread_id].is_connected():
            connections[thread_id].reconnect()
        elif thread_id not in connections:
            connections[thread_id] = mysql.connector.connect(
            buffered=True,
            host="localhost",
            user="root",
            passwd="",
            database="customhoesjes_stock"
            )

        return connections[thread_id]

class ProductMeta(type):
    @property
    def fields(self):
        return [
        "id",
        "name",
        "description",
        "stock",
        "wholesaler",
        "internal_id"
        ]

    @property
    def all(self):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM products;")

        row = cursor.fetchone()

        while row:
            yield Product(*row)
            row = cursor.fetchone()

class Product(metaclass=ProductMeta):
    def __init__(self, *args):
        arg_count = len(args)

        if arg_count == 1:
            try:
                self.id = int(args[0])
            except ValueError:
                raise TypeError("The provided id has to be an int!")
            else:
                ## Check if a product exists with the provided id
                connection = get_db_connection()
                cursor = connection.cursor()

                cursor.execute(
                "SELECT 1 FROM products WHERE id=%s;",
                (self.id,)
                )

                if not cursor.fetchall():
                    raise ValueError("There is no product with the provided id!")
        elif arg_count == len(Product.fields):
            try:
                self.id = int(args[0])
            except ValueError:
                raise TypeError("The provided id has to be an int!")
            else:
                connection = get_db_connection()
                cursor = connection.cursor()

                cursor.execute(
                "SELECT 1 FROM products WHERE id=%s;",
                (self.id,)
                )

                if cursor.fetchall():
                    raise ValueError("There is already a product with the provided id!")
                else:
                    cursor.execute(
                    "INSERT INTO products({}) VALUES ({});"
                    .format(",".join(Product.fields), ",".join(['%s'] * len(Product.fields))),
                    args
                    )

                    connection.commit()
        else:
            raise ValueError("expected 1 or {} arguments, got {}".format(len(Product.fields), arg_count))

    def delete(self):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
        "SELECT 1 FROM products WHERE id=%s;",
        (self.id,)
        )

        if not cursor.fetchall():
            raise ValueError("There is no product with the provided id!\rAre you trying to access a deleted product?")
        else:
            cursor.execute(
            "DELETE FROM products WHERE id = %s;",
            (self.id,)
            )

            connection.commit()

def get_field_getter(field):
    def field_getter(self):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
        "SELECT {} FROM products WHERE id=%s;"
        .format(field),
        (self.id,)
        )

        results = cursor.fetchall()

        if results:
            return results[0][0]
        else:
            raise ValueError("There is no product with the provided id!\rAre you trying to access a deleted product?")

    return field_getter

def get_field_setter(field):
    def field_setter(self, value):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
        "SELECT 1 FROM products WHERE id=%s;",
        (self.id,)
        )

        if not cursor.fetchall():
            raise ValueError("There is no product with the provided id!\rAre you trying to access a deleted product?")
        else:
            cursor.execute(
            "UPDATE products SET {} = %s WHERE id=%s;"
            .format(field),
            (value, self.id)
            )

            connection.commit()

    return field_setter

for field in Product.fields:
    if field != 'id':
        setattr(Product, field, property(
        get_field_getter(field),
        get_field_setter(field)
        ))

from flask import request
from flask_restful import Resource

class ProductResource(Resource):
    def get(self, id):
        try:
            product = Product(id)
            return {
            field: getattr(product, field) for field in Product.fields
            }
        except ValueError:
            return None, 404

    def put(self, id):
        try:
            product = Product(id)
            for key in request.form:
                setattr(product, key, request.form[key])
            return {
            field: getattr(product, field) for field in Product.fields
            }, 202
        except ValueError as e:
            return None, 404

    def delete(self, id):
        try:
            Product(id).delete()
            return None, 204
        except ValueError as e:
            return None, 404

class ProductsResource(Resource):
    def get(self):
        return [
        {
        field: getattr(product, field) for field in Product.fields
        } for product in Product.all
        ]
    def post(self):
        try:
            product = Product(*request.form.values())
            return {
            field: getattr(product, field) for field in Product.fields
            }, 201
        except ValueError as e:
            return None, 409

from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

api.add_resource(ProductResource, '/product/<int:id>')
api.add_resource(ProductsResource, '/product')

from flask import render_template

@app.route('/')
def host_index():
    page = int(request.args['page'])
    products_per_page = int(request.args['products-per-page'])

    products_on_page = []

    for i, product in enumerate(Product.all):
        if i >= (page - 1) * products_per_page and i < page * products_per_page:
            products_on_page.append(product)
        elif i >= page * products_per_page:
            break

    return render_template('index.html', page=page, products_per_page=products_per_page, getattr=getattr, products=products_on_page, fields=Product.fields)

@app.route('/add-product')
def host_add_product():
    return render_template('input.html', fields=Product.fields, method='post')

@app.route('/product/<int:id>/update')
def host_update_product(id):
    try:
        return render_template('input.html', fields=Product.fields, method='put', getattr=getattr, product=Product(id))
    except ValueError as e:
        return str(e), 404

if __name__ == '__main__':
    app.run(threaded=True, debug=True)
