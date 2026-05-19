# Django eCommerce Project

A simple eCommerce web application built with Django.
It includes user authentication, vendor stores, products, REST API functionality, cart system, reviews, checkout with email confirmation, and X (Twitter) API integration.

## Features
### Authentication
* User registration (Buyer / Vendor)
* Login system using Django authentication
* Group-based vendor permissions
### Store System
* Vendors can create and manage stores
* Stores belong to authenticated vendors
* Store descriptions and logo uploads
* Store editing and deletion
* Vendor ownership protection
### Products
* Products linked to stores
* Product creation, editing, and deletion
* Product stock management
* Product detail pages
* Vendor-only product management
### Cart System
* Session-based shopping cart
* Add products to cart
* View cart contents
* Clear cart functionality
### Checkout
* Calculates order totals
* Sends invoice emails to users
* Clears cart after purchase
* Tracks purchased products for verified reviews
### Reviews
* Users can leave product reviews
* Verified purchase review system
* Product review retrieval
### REST API
* Built using Django REST Framework
* JSON serialisation of products, stores, and reviews
* Vendor authentication for protected endpoints
* Product CRUD API endpoints
* Store CRUD API endpoints
* Cart and checkout API endpoints
* Review submission API
### X (Twitter) API Integration
* Automatically tweets when:
  * a new store is created
  * a new product is added
* Store tweets include:
  * store name
  * description
* Product tweets include:
  * store name
  * product name
  * product description
* Integrated using Tweepy and X API v2
### API Authentication
The API endpoints are protected and require authentication before they can be accessed.
#### Step 1: Register a user
Create an account through the registration page:
```
http://127.0.0.1:8000/register/
```
Choose either:
* Buyer
* Vendor

After registering, log in with your account.
#### Step 2: Obtain authentication credentials
This project uses Django authentication. Users must log in before accessing protected API endpoints.

If using Session Authentication:
1. Start the server:
```
python manage.py runserver
```
2. Open
```
http://127.0.0.1:8000/login/
```
3. Log in with your credentials

The browser session will then be authenticated
### Testing the API with Postman
Some API endpoints are protected and require authentication. If authentication is not provided, requests may return:
```
403 Forbidden
```
This is expected behaviour and prevents unauthorised users from accessing protected functionality.
#### Step 1: Run the Django server
```
python manage.py runserver
```
The application should now be available at:
```
http://127.0.0.1:8000/
```
#### Step 2: (if no current account) Create an account
Open the registration page:
```
http://127.0.0.1:8000/register/
```
Create a new account and choose a role:
* Buyer
* Vendor
#### Step 3: Log in
Go to:
```
http://127.0.0.1:8000/login/
```
Log in using the account you created.

Once logged in, Django creates a session.
#### Step 4: Obtain session authentication values
Because the project uses Django Session Authentication, Postman needs your browser session information.

After logging in:

1. Press F12 in your browser / Inspect element
2. Open:
Application → Cookies

(or Storage → Cookies depending on browser)

Locate:
* sessionid
* csrftoken

Copy both values.

Example:
```
sessionid=abc123xyz456
csrftoken=gh789example
```
### Step 5: Open Postman
Create a new request.
Example:
```
GET
http://127.0.0.1:8000/ecommerce/my-products/
```
#### Step 6: Add authentication headers
Open the Headers tab and add:
| Key | Value |
|------|--------|
| Cookie | sessionid=abc123xyz456, csrftoken= gh789example|
| X-CSRFToken | gh789example |

Replace with your own values.
#### Step 7: Test GET requests
Example:
```
GET
http://127.0.0.1:8000/ecommerce/my-products/
```
#### Step 8: Test POST requests
Example:
```
POST
http://127.0.0.1:8000/ecommerce/create/
```
Body → form-data:
| Key | Value |
|------|--------|
| name | Gaming Mouse |
| description | Wireless mouse |
| price | 30 |
| stock | 15 |
| store | 1 |

Required authentication:
Headers:
```
Cookie: sessionid=your_session_id
X-CSRFToken: your_csrf_token
```
### API Endpoints
#### Products
| Method | Endpoint	| Description                              |
| ------ | -------- |------------------------------------------|
| GET	 | /api/products/ | Retrieve all products                    |
| POST	 | /api/products/ | Create a new product                     |
| GET	 | /api/products/mine/ | Retrieve authenticated vendor products   |
| GET	 | /api/products/<id>/ | Retrieve single product                  |
| PATCH	 | /api/products/<id>/ | Edit product                             |
| DELETE | /api/products/<id>/ | Delete product                           |
| POST	 | /api/products/<id>/reviews/ | Create product review                    |

#### Stores
| Method  | 	Endpoint          |	Description|
|---------|--------------------| ----------- |
| GET	    | /api/stores/       |	Retrieve vendor stores |
| POST	   | /api/stores/	      | Create store |
| GET	    | /api/stores/<id>/  |	Retrieve single store |
| PATCH	  | /api/stores/<id>/	 | Edit store |
| DELETE	 | /api/stores/<id>/  |	Delete store |

#### Cart & Checkout
| Method	 | Endpoint	| Description |
|---------| --------- | ----------- |
| GET	    | /api/cart/	| View cart |
| POST	   | /api/cart/	| Add item to cart |
| DELETE	| /api/cart/	| Clear cart |
| POST	| /api/checkout/	| Checkout cart |

### Tech Stack
* Python
* Django
* Django REST Framework
* MySQL
* Tweepy
* X (Twitter) API
* HTML (Django Templates)

### Media Uploads
Store logos are uploaded using Django media handling.

Uploaded images are stored inside:
```
media/store_logos/
```
Environment Variables

The project uses a .env file for X API credentials and Email Host Users.
Example:
```
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password

X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
```
This has been changed to .env.example

```
📁 Project Structure
eCommerce_app/
├── .env.example
├── manage.py
├── README.md
├── requirements.txt
│
├── eCommerce/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── authenticator/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   └── ...
│
├── store/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── api_urls.py
│   ├── twitter_utils.py
│   ├── templates/
│   └── ...
│
├── media/
│   └── store_logos/
│   └── product_images/
│
└── static/
```

### Setup Instructions
#### Clone Project
```
git clone https://github.com/samia-islam-01/eCommerce_app
cd eCommerce
```
#### Create Virtual Environment
```
python -m venv venv
```
#### Activate Virtual Environment
##### Windows
```
venv\Scripts\activate
```
##### Install Dependencies
```
pip install -r requirements.txt
```
##### Install and Create MySQL database
```
mysql -u root -p
```
##### Run Migrations
```
python manage.py migrate
python manage.py makemigrations
```
##### Start Development Server
```
python manage.py runserver
```

### Notes
* Currently, no credits in the X Developer Console, so when a tweet is meant to be made, it instead returns:
```
PRODUCT TWEET FAILED
<class 'tweepy.errors.HTTPException'>
402 Payment Required
Your enrolled account [2054295400161415168] does not have any credits to fulfill this request.
```
