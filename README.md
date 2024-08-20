My 5th mini project! This is a flask application that uses SQLalchemy to streamline and simplify interaction with an e-commerce database which it creates. It has endpoints that allow for full CRUD and automatically creates the tables it needs provided the database exists. As a note for it's functionality, it does utilize cascade deletion to prevent data integrity errors with orphaned entries in the tables. So, deleting a customer will delete their account, orders, and entries on the order_product table. It will not, however, delete references to deleted products in orders when a product is deleted.  

I recommend you create a customer, then an account, then the three test products provided, then an order. Everything should run smoothly out of the box. After, try to query or update whatever you wish. Lastly, try deleting products to see the safeguard assertion error, then delete either an order or a customer to see the changes reflected in the database.  

BONUSES: 
1. View and manage product stock levels (it also automatically checks stock before ordering and removes it once it does). The bonus functionality is baked into the product update endpoint.  
2. Manage order history is the 'orders_by_customer' endpoint accessed via the query in postman of the same name.  
3. Calcuate order total price is baked into the order endpoint. It stores the price each item is purchased at and saves along with the rest of the record on the order_products table. The total is never stored, but is calculated on demand from the originally bought prices. Everything is then bundled together into custom json and returned to the user. 

Dependencies:  
1. Flask  
2. Flask-Marshmallow  
3. Flask-SQLalchemy  
4. MySQL-connector-python
5. SQLalchemy  

The project will also need both a database named 'e_commerce_database' (unless you change it in the program) with no tables, and a password.py with the database password in the root directory.

Endpoints for customers:  
1. GET: localhost:5000/customers  
2. GET: localhost:5000/customers/id  
3. POST: localhost:5000/customers  
4. PUT: localhost:5000/customers/id  
5. DELETE: localhost:5000/customers/id  

JSON structure:  
POST/UPDATE:  
{
	"name": "Timmy",
    "email": "timmy@timmy.com",
    "phone": "1234567890"
}

---------------------------------------------------------

Endpoints for accounts:  
1. GET: localhost:5000/accounts  
2. GET: localhost:5000/accounts/id 
3. POST: localhost:5000/accounts  
4. PUT: localhost:5000/accounts/id  
5. DELETE: localhost:5000/accounts/id  

JSON structure:  
POST/UPDATE:  
{
	"username": "TimmyTom",
    "password": "test",
    "customer_id": 1
}

---------------------------------------------------------

Endpoints for products:  
1. GET: localhost:5000/products  
2. GET: localhost:5000/products/id 
3. POST: localhost:5000/products  
4. PUT: localhost:5000/products/id  
<!-- it will not allow you to delete a product that is on an order by design -->
5. DELETE: localhost:5000/products/id  

JSON structure:  
POST/UPDATE:  
{
	"name": "Pokeball",
    "price": 200,
    "stock": 10
}
{
	"name": "Greatball",
    "price": 500,
    "stock": 10
}
{
	"name": "Ultraball",
    "price": 1000,
    "stock": 10
}

---------------------------------------------------------

Endpoints for orders:  
1. GET: localhost:5000/orders  
2. GET: localhost:5000/orders/id  
3. GET: localhost:5000/orders_by_customer/id  
<!-- the below will order each product with an id appearing in the query -->
4. POST: localhost:5000/orders?product=1,2,4,4,2,1,4  
5. PUT: localhost:5000/orders/id  
6. DELETE: localhost:5000/orders/id  

JSON structure:  
POST:  
{
    "customer_id": 1
}  
<!-- the update and post structures are different as it automatically selects the right date in the first place and defaults everything else -->
<!-- the default shipping time for this application is set to 7 days for testing purposes -->
UPDATE:  
{
    "customer_id": 1,
    "expected_delivery": "2024/08/20",
    "order_date": "2024/08/27",
    "shipping_status": "shipped"
}