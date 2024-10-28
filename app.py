from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from password import my_password
from marshmallow import fields, ValidationError, validate
from sqlalchemy import select
import datetime, re

def validate_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        raise ValueError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.String(required=True, validate=validate.Length(min=1))
    phone = fields.String(required=True, validate=validate.Length(min=9))

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    stock = fields.Integer(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('name', 'price', 'stock', 'id')

class OrderSchema(ma.Schema):
    customer_id = fields.Integer(required=True, validate=validate.Range(min=1))

    class Meta:
        fields = ('order_date', 'customer_id', 'expected_delivery', 'shipping_status', 'id')

class OrderProductSchema(ma.Schema):
    customer_id = fields.Integer(required=True, validate=validate.Range(min=1))
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('customer_id', 'product_id', 'quantity', 'price')

class AccountSchema(ma.Schema):
    username = fields.String(required=True, validate=validate.Length(min=1))
    password = fields.String(required=True, validate=validate.Length(min=1))
    customer_id = fields.Integer(required=True, validate=validate.Range(min=1))

    class Meta:
        fields = ('username', 'password', 'customer_id', 'id')

# Instantiate schemas
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

order_product_schema = OrderProductSchema()
order_products_schema = OrderProductSchema(many=True)

account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    # here we create a relationship on the parent side with the child orders and ensure passive_deletion so the database can handle the deletion of orphan children
    orders = db.relationship('Order', passive_deletes=True, backref='customer')
    # and we do the same with account, a one-to-one relationship ensured by uselist=False
    account = db.relationship('CustomerAccount', passive_deletes=True, backref='customer', uselist=False)

class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id', ondelete='Cascade'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False)
    expected_delivery = db.Column(db.Date, nullable=False)
    shipping_status = db.Column(db.String(30), nullable=False)
    # this foreign key is many-to-one with its related customer
    # we set the foreign key customer_id to link with its customer but also ensure cascade deletion
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id', ondelete='Cascade'))
    # # and we'll do the same with order and order_product so that if order is deleted, so will all of the child records on the order_product table
    # many-to-many with products, with the order_product table joining the two
    products = db.relationship('OrderProduct', passive_deletes=True, backref=db.backref('orders'))

class CustomerAccount(db.Model):#one-to-one relationship
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # we set the foreign key customer_id to link with customers but also ensure cascade deletion
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id', ondelete='Cascade'))

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    orders = db.relationship('OrderProduct', backref=db.backref('products'))

# customer routes
@app.route('/customers', methods=['GET'])
def get_customer():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

@app.route('/customers/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer)

@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        # Validate and deserialize input
        customer_data = customer_schema.load(request.json)
        validate_email(customer_data['email']) == True
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as err:
        return jsonify({'message': 'Email is not formatted correctly.'}), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'New customer added successfully'}), 201

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
        validate_email(customer_data['email'])
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as err:
        return jsonify({'message': 'Email is not formatted correctly.'}), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({'message': 'Customer details updated successfully'}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer removed successfully'}), 200

# product routes
@app.route('/products', methods=['GET'])
def get_product():
    products = Product.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    products = Product.query.get_or_404(id)
    return product_schema.jsonify(products)

@app.route('/products', methods=['POST'])
def add_product():
    try:
        # Validate and deserialize input
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_product = Product(
        name=product_data['name'], 
        price=product_data['price'], 
        stock=product_data['stock'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'New product added successfully'}), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']
    product.stock = product_data['stock']
    db.session.commit()
    return jsonify({'message': 'Product details updated successfully'}), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product removed successfully'}), 200

# customer_account routes
@app.route('/accounts', methods=['GET'])
def get_account():
    accounts = CustomerAccount.query.all()
    return accounts_schema.jsonify(accounts)

@app.route('/accounts/<int:id>', methods=['GET'])
def get_account_by_id(id):
    accounts = CustomerAccount.query.get_or_404(id)
    return account_schema.jsonify(accounts)

@app.route('/accounts', methods=['POST'])
def add_account():
    try:
        # Validate and deserialize input
        account_data = account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_account = CustomerAccount(
        username=account_data['username'], 
        password=account_data['password'], 
        customer_id=account_data['customer_id'])
    db.session.add(new_account)
    db.session.commit()
    return jsonify({'message': 'New account added successfully'}), 201

@app.route('/accounts/<int:id>', methods=['PUT'])
def update_account(id):
    account = CustomerAccount.query.get_or_404(id)
    try:
        account_data = account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    account.username = account_data['username']
    account.password = account_data['password']
    account.customer_id = account_data['customer_id']
    db.session.commit()
    return jsonify({'message': 'Account details updated successfully'}), 200

@app.route('/accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Account removed successfully'}), 200

# order routes
@app.route('/orders', methods=['GET'])
def get_order():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

@app.route('/orders/<int:id>', methods=['GET'])
def get_order_by_id(id):
    orders = Order.query.get_or_404(id)
    products_in_order = {
        f'item{i+1}':{
            'name':x.products.name, 
            'price':x.price, 
            'quantity':x.quantity
            } for i, x in enumerate(orders.products)}
    total = 0
    for x in products_in_order.items():
        total = total + x[1].get('price')
    # accounts = CustomerAccount.query.all()
    new_json = {
        'order_id':orders.id,
        'customer_id':id, 
        'order_date':orders.order_date, 
        'expected_delivery':orders.expected_delivery, 
        'shipping_status':orders.shipping_status, 
        'total':total, 
        'products_in_order': products_in_order}
    return new_json

@app.route('/orders_by_customer/<int:id>', methods=['GET'])
def get_order_by_customer_id(id):
    customer = Customer.query.get_or_404(id)
    orders = customer.orders
    # create the json we will return to client later
    new_json = {
        'customer_id':id, 
        'orders':{}
        }
    for i, order in enumerate(orders):
        # create the order json we will update the orders dictionary with
        order_json = {
            'order_id':order.id,
            'order_date':order.order_date, 
            'expected_delivery':order.expected_delivery, 
            'shipping_status':order.shipping_status, 
            'total':0, 
            'products_in_order': {}
        }
        # create each product's json and update the order with them
        for x, product in enumerate(order.products):
            order_json['total'] = order_json['total'] + product.price
            order_json['products_in_order'].update({f'item{x}':{
                'name':product.products.name,
                'price':product.price,
                'quantity':product.quantity
            }})
        # update the json we will send with the orders
        new_json['orders'].update({f'order{i+1}':order_json})
    return new_json

@app.route('/orders', methods=['POST'])
def add_order():
    query = request.args.getlist('product')
    query = [x for x in query[0].split(',')]
    try:
        # Validate and deserialize input
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    # get current date
    date_time = datetime.datetime.now()
    current_date = date_time.strftime("%Y/%m/%d")
    delta = datetime.timedelta(days=7)
    # create new order and add it
    new_order = Order(
        order_date=current_date,
        customer_id=order_data['customer_id'],
        expected_delivery=(date_time+delta).strftime("%Y/%m/%d"),
        shipping_status='not shipped'
        )
    db.session.add(new_order)
    # create dictionary of products with convenient quantity information
    products = {x:{"data":Product.query.get_or_404(x), "quantity":query.count(x)} for x in query}
    # utilize product dictionary to create OrderProducts
    products_to_order = [OrderProduct(order_id=new_order.id, product_id=x[0], quantity=x[1].get('quantity'), price=x[1].get('data').price) for x in products.items()]
    try:
        # check stock of each item
        for x in products.items():
            stock = x[1].get('data').stock
            quantity = x[1].get('quantity')
            stock >= quantity
    except ValueError:
        return jsonify({'message': 'Unable to purchase items as one or more items does not have enough stock left'}), 400
    else:
        # reduce stocks by quantities bought
        for x in products.items():
            x[1]['data'].stock = stock - quantity
    # add OrderProducts to database
    for x in products_to_order:
        db.session.add(x)
    db.session.commit()
    return jsonify({'message': 'New order added successfully'}), 201

@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Order.query.get_or_404(id)
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    order.order_date = order_data['order_date']
    order.expected_delivery = order_data['expected_delivery']
    order.shipping_status = order_data['shipping_status']
    db.session.commit()
    return jsonify({'message': 'Order details updated successfully'}), 200

@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order removed successfully'}), 300

# Initialize the database and create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)