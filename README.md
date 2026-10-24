# ShopFlow API

Backend for [ShopFlow](https://shopflow-frontend-alpha.vercel.app), a multi-vendor e-commerce platform built with **Django** and **Django REST Framework**.

Focused on real backend problems: inventory race conditions, transactional safety, role-based access control and clean API design.

## Live
- **Frontend app:** https://shopflow-frontend-alpha.vercel.app
- **Frontend repo:** https://github.com/mohanrajtunes/Shopflow-frontend
- **API docs (Swagger):** https://shopflow-backend-5o0j.onrender.com/api/docs/

*Free hosting: the first request can take up to a minute while the server wakes up.*

## Engineering highlights
- **ACID transactions and concurrency safety:** checkout uses `transaction.atomic()` and `select_for_update()` to stop overselling when several users buy the last item at the same time.
- **Role-based access control:** Admin, Vendor and Customer roles. Vendors can only edit and delete their own products.
- **JWT authentication:** SimpleJWT access and refresh tokens, with the user's role included in the token.
- **Search, filtering and pagination:** by category, vendor, price range and title/description, with sorting.
- **API documentation:** interactive Swagger UI via `drf-spectacular`.
- **Automated tests** covering stock safety and checkout.

## Tech stack
Python, Django, Django REST Framework, SimpleJWT, django-filter, drf-spectacular, PostgreSQL (Neon), Gunicorn, WhiteNoise. Hosted on Render.

## Main endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Register as customer or vendor |
| POST | `/api/token/` | Log in and get JWT tokens |
| POST | `/api/token/refresh/` | Refresh the access token |
| GET | `/api/products/` | List products (search, filters, ordering) |
| POST | `/api/products/` | Create a product (vendor only) |
| GET/POST | `/api/cart/` | View or add to your cart |
| POST | `/api/orders/checkout/` | Atomic checkout |
| GET | `/api/orders/` | Your order history |

## Run locally
1. Clone the repository:

   ```bash
   git clone https://github.com/mohanrajtunes/shopflow-backend.git
   cd shopflow-backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create your environment file and set a strong `SECRET_KEY`:

   ```bash
   cp .env.example .env
   ```

5. Run migrations, create an admin user and start the server:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

6. Open the API docs at http://127.0.0.1:8000/api/docs/

## Example flow
1. `POST /api/register/` to create a user
2. `POST /api/token/` to get a token
3. Click **Authorize** in Swagger and paste `Bearer <your_access_token>`
4. As a vendor: `POST /api/products/`
5. As a customer: `POST /api/cart/`, then `POST /api/orders/checkout/`

## Tests
```bash
python manage.py test store
```

## Deployment settings
Environment variables used in production: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.