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