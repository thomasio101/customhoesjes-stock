import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="customhoesjes_stock"
    )

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
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT id FROM products;")

            row = cursor.fetchone()

            while row:
                yield Product(*row)
                row = cursor.fetchone()
        finally:
            try:
                connection.close()
            except Exception as e:
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
                    except Exception as e:
                        raise e
        elif arg_count == len(Product.fields):
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
                        .format(",".join(Product.fields), ",".join(['%s'] * len(Product.fields))),
                        args
                        )

                        connection.commit()
                finally:
                    try:
                        connection.close()
                    except Exception as e:
                        raise e
        else:
            raise ValueError("expected 1 or {} arguments, got {}".format(len(Product.fields), arg_count))

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
            except Exception as e:
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
            except Exception as e:
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
            except Exception as e:
                raise e

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
