# InventoryFlow — Multi Location Inventory Management System

InventoryFlow is a **Flask-based Inventory Management System** that allows you to manage products, store them in different locations, move stock across locations, track quantity history, and generate product-wise reports.  
The system even supports **product & location deletion without page reload (AJAX Delete)**.

---

## 🚀 Features

✔ Add new products with quantity & price  
✔ Add multiple storage locations  
✔ Move stock between locations  
✔ Internal & external stock movement tracking  
✔ View product quantity per location  
✔ Delete product & location without page reload  
✔ Auto-generated IDs (`pdXXXX`, `lcXXXX`)  
✔ Movement logs with history  
✔ JSON API to fetch product available locations  
✔ Clean and scalable project structure  

---

## 🛠 Tech Stack

| Component | Technology |
|----------|------------|
| Backend | **Python Flask** |
| Database | **MySQL** |
| ORM/Driver | **PyMySQL** |
| Frontend | **HTML + Jinja2 + JavaScript** |



---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

      git clone https://github.com/your-username/InventoryFlow.git
      cd InventoryFlow

### 2️⃣ Install dependencies
      pip install -r requirements.txt

### 3️⃣ Configure Database
Create a MySQL database:
      CREATE DATABASE inventory_db;

Update credentials in config.py:

    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "your_password"
    MYSQL_DB = "inventory_db"

### 4️⃣ Required Tables
      CREATE TABLE product (
          product_id VARCHAR(50) PRIMARY KEY,
          name VARCHAR(100),
          quantity INT,
          price DECIMAL(10,2)
      );
      
      CREATE TABLE location (
          location_id VARCHAR(50) PRIMARY KEY,
          name VARCHAR(100)
      );
      
      CREATE TABLE productmovement (
          movement_id INT AUTO_INCREMENT PRIMARY KEY,
          product_id VARCHAR(50),
          from_location VARCHAR(50),
          to_location VARCHAR(50),
          qty INT,
          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

### ▶️ Run Project
      python app.py


Open in browser:
 http://127.0.0.1:5000/

### 📌 Usage Flow
#### Add Location

Location → Add → Appears in table → Can be deleted instantly

#### Add Product

Product → Enter details + Select location → Saves stock & displays in table

#### Transfer Stock

Movement Page → Select product & from-to location → Moves quantity

#### Delete (No Page Reload)

- Product & all stock records removed in one click

- Location deletion also removes related movements


### 📥 Git Commands to Push
    git init
    git add .
    git commit -m "Initial commit - InventoryFlow"
    git branch -M main
    git remote add origin  https://github.com/your-username/InventoryFlow.git
    git push -u origin main


## ✨ Author

##### Vishal Umath
###### Full-Stack | AI | Python Developer

If you like this project ⭐ Star the repo on GitHub!



