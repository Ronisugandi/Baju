from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# =========================
# Model Admin
# =========================
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password_input):
        return check_password_hash(self.password_hash, password_input)


# =========================
# Model User (pembeli)
# =========================
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# =========================
# Model Produk
# =========================
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    # relasi ke ukuran produk
    sizes = db.relationship('ProductSize', backref='product', lazy=True, cascade="all, delete-orphan")

# =========================
# Model Ukuran Produk
# =========================
class ProductSize(db.Model):
    __tablename__ = 'product_size'
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(10), nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    # foreign key ke produk
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
