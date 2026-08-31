# 🛒 ShopFlow-API: E-Commerce Marketplace Backend

A production-grade, multi-vendor e-commerce backend built with **Django**, **Django REST Framework (DRF)**, and **JWT Authentication**. Designed with a focus on database concurrency control, ACID compliance, and secure inventory management.

---

## 🚀 Core Engineering Highlights
* **ACID Transactions & Concurrency Safety:** Implements `transaction.atomic()` and row-level locking (`select_for_update()`) during the checkout pipeline to completely prevent race conditions and overselling when multiple users buy the last item simultaneously.
* **Role-Based Access Control (RBAC):** Custom user roles (`Admin`, `Vendor`, `Customer`) with fine-grained permission boundaries (e.g., only verified vendors can create or modify products).
* **Advanced Query Filtering:** Integrated dynamic product filtering by category, search queries, price ranges, and sorting using `django-filter`.
* **Automated API Documentation:** Fully documented with interactive Swagger UI and OpenAPI schemas via `drf-spectacular`.

---

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Framework:** Django & Django REST Framework
* **Authentication:** SimpleJWT (JSON Web Tokens)
* **Database:** SQLite (Development) / PostgreSQL-ready
* **Documentation:** drf-spectacular (Swagger / ReDoc)

---

## ⚙️ Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mohanrajtunes/shopflow-backend.git](https://github.com/mohanrajtunes/shopflow-backend.git)
   cd shopflow-backend