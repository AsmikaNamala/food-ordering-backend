# Food Ordering Backend

A backend application for managing food ordering operations, built using **Python, FastAPI, PostgreSQL, and Docker**.

## 🚀 Project Overview

The Food Ordering Backend provides APIs to manage vendors, clients, food items, orders, and inventory-related operations. It uses PostgreSQL for persistent data storage and FastAPI to build RESTful APIs.

## ✨ Features

- **Vendor Management** – Create, retrieve, and update vendor details.
- **Client Management** – Register and manage client information.
- **Item Management** – Manage food items, prices, and available stock.
- **Order Management** – Create and manage customer orders.
- **Inventory Management** – Track available quantities and minimum stock levels.
- **Replenishment** – Support inventory replenishment operations.
- **Database Integration** – Store application data in PostgreSQL.
- **Automated Testing** – Validate API functionality using Pytest.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API development |
| PostgreSQL | Relational database |
| SQLAlchemy | Database ORM |
| Docker | Database containerization |
| Pytest | Automated testing |
| Git & GitHub | Version control |

## 📁 Project Structure

```text
food-ordering-backend/
│
├── app/
│   ├── routers/
│   │   ├── clients.py
│   │   ├── items.py
│   │   ├── orders.py
│   │   ├── replenishment.py
│   │   └── vendors.py
│   │
│   ├── database.py
│   ├── db_check.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   ├── scheduler.py
│   └── schemas.py
│
├── tests/
│   ├── conftest.py
│   └── test_main.py
│
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/AsmikaNamala/food-ordering-backend.git
cd food-ordering-backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://fooduser:YOUR_PASSWORD@localhost:5432/food_ordering
DB_PASSWORD=YOUR_PASSWORD
```

Replace `YOUR_PASSWORD` with your own PostgreSQL password in both places.

**Important:** Never upload your `.env` file or database credentials to GitHub.

### 5. Start PostgreSQL using Docker

```bash
docker compose up -d
```

### 6. Run the FastAPI application

```bash
uvicorn app.main:app --reload
```

The application will be available at:

`http://127.0.0.1:8000`

## 📖 API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Open:

`http://127.0.0.1:8000/docs`

You can explore and test the available API endpoints directly from your browser.

## 🧪 Running Tests

Execute the test suite using:

```bash
python -m pytest -v
```

## 🔮 Future Improvements

- User authentication and authorization.
- Role-based access control.
- Payment integration.
- Enhanced order tracking.
- Improved inventory and replenishment workflows.
- Deployment to a cloud platform.

## 👩‍💻 Author

**Asmika Namala**

B.Tech – Computer Science and Engineering

GitHub: [AsmikaNamala](https://github.com/AsmikaNamala)

---

⭐ If you find this project interesting, feel free to explore the repository!