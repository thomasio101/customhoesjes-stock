import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="customhoesjes_stock"
    )

product_fields = [
"id",
"name",
"description"
]

class ProductMeta(type):
    @property
    def all(self):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT id FROM products;")

            for row in cursor.fetchall():
                yield Product(*row)
        finally:
            try:
                connection.close()
            except e:
                raise e

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
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                    "SELECT 1 FROM products WHERE id=%s;",
                    (self.id,)
                    )

                    if not cursor.fetchall():
                        raise ValueError("There is no product with the provided id!")
                finally:
                    try:
                        connection.close()
                    except e:
                        raise e
        elif arg_count == len(product_fields):
            try:
                self.id = int(args[0])
            except ValueError:
                raise TypeError("The provided id has to be an int!")
            else:
                try:
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
                        .format(",".join(product_fields), ",".join(['%s'] * len(product_fields))),
                        args
                        )

                        connection.commit()
                finally:
                    try:
                        connection.close()
                    except e:
                        raise e
        else:
            raise ValueError("expected 1 or {} arguments, got {}".format(len(product_fields), arg_count))

    def delete(self):
        try:
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
        finally:
            try:
                connection.close()
            except e:
                raise e

def get_field_getter(field):
    def field_getter(self):
        try:
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
        finally:
            try:
                connection.close()
            except e:
                raise e

    return field_getter

def get_field_setter(field):
    def field_setter(self, value):
        try:
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
        finally:
            try:
                connection.close()
            except e:
                raise e

    return field_setter

for field in product_fields:
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
            field: getattr(product, field) for field in product_fields
            }
        except ValueError:
            return None, 404

    def put(self, id):
        try:
            product = Product(id)
            for key in request.form:
                setattr(product, key, request.form[key])
            return {
            field: getattr(product, field) for field in product_fields
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
        field: getattr(product, field) for field in product_fields
        } for product in Product.all
        ]
    def post(self):
        try:
            product = Product(*request.form.values())
            return {
            field: getattr(product, field) for field in product_fields
            }, 201
        except ValueError as e:
            return None, 409

from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

api.add_resource(ProductResource, '/product/<int:id>')
api.add_resource(ProductsResource, '/product')

@app.route('/')
def host_index():
    with open('index.html') as index:
        return index.read()

@app.route('/main.js')
def host_main_js():
    with open('main.js') as main_js:
        return main_js.read()

from flask import render_template

@app.route('/add-product')
def host_add_product():
    return render_template('add-product.html', fields=product_fields)

if __name__ == '__main__':
    app.run(threaded=True, debug=True)
