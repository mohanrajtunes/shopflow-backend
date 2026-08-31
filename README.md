# ShopFlow-API

A multi-vendor e-commerce backend built with **Django** and **Django REST Framework**.

Focused on real backend engineering problems: inventory race conditions, transactional safety, role-based access control, and clean API design.

---

## Engineering Highlights

- **ACID Transactions & Concurrency Safety**  
  Checkout uses `transaction.atomic()` and `select_for_update()` to prevent overselling when multiple users try to buy the last item at the same time.

- **Role-Based Access Control**  
  Supports `Admin`, `Vendor`, and `Customer` roles with proper permission boundaries. Vendors can only manage their own products.

- **Dynamic Filtering & Search**  
  Products can be filtered by category, vendor, price range (`min_price`, `max_price`), and searched by title/description.

- **JWT Authentication**  
  Secure token-based auth using SimpleJWT (access + refresh tokens).

- **API Documentation**  
  Interactive Swagger UI available via `drf-spectacular`.

---

## Tech Stack

- Python 3.10+
- Django + Django REST Framework
- SimpleJWT
- django-filter
- drf-spectacular
- python-dotenv
- SQLite (development) / PostgreSQL-ready

---

## Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/mohanrajtunes/shopflow-backend.git
cd shopflow-backend

2. **Create and activate virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

3.  **Install dependencies**
```bash
pip install -r requirements.txt

4. **Environment variables**
```bash
cp .env.example .env
Open .env and set a strong SECRET_KEY.

5. **Run migrations**
```bash
python manage.py migrate

6. **Create superuser (optional)**
```bash
python manage.py createsuperuser

7.  **Migrate and start the server**
```bash
python manage.py migrate
python manage.py runserver

8. **Explore the API Docs:**
Open your browser at http://127.0.0.1:8000/api/docs/


🔄 API Request Flow Example
Register User: POST /api/register/ (Register as customer or vendor)

Obtain Token: POST /api/token/ to receive your JWT Access Token.

Authorize: Click "Authorize" in Swagger and paste Bearer <your_token>.

Create Product (Vendor only): POST /api/products/

Filter Products: GET /api/products/?min_price=100&max_price=500&search=shoes

Add to Cart (Customer): POST /api/cart/

Checkout: POST /api/orders/checkout/ (Triggers atomic transaction, row locking, and stock deduction).

🧪 Running Tests
To run the automated test suite covering race conditions and stock safety:
```bash
python manage.py test store
 