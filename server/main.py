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
