from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import quote
from functools import wraps
import os
from flask_login import current_user

from models import db, Admin, Product, ProductSize, User

app = Flask(__name__)
app.secret_key = 'Ronisugandi20'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Middleware login user
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Middleware login admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash("Silakan login sebagai admin.", "warning")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Login Admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login admin gagal', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

# Tambah Produk
@app.route('/admin/add-product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = int(request.form['price'])

        image_file = request.files.get('image')  # Gunakan .get agar aman
        sizes = request.form.getlist('size[]')
        stocks = request.form.getlist('stock[]')

        if not image_file or image_file.filename == '':
            flash('Gambar produk wajib diunggah!', 'danger')
            return redirect(request.url)

        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        new_product = Product(name=name, price=price, image='uploads/' + filename)
        db.session.add(new_product)
        db.session.commit()

        for size, stock in zip(sizes, stocks):
            size_entry = ProductSize(size=size.strip(), stock=int(stock.strip()), product_id=new_product.id)
            db.session.add(size_entry)
            print(f"Menambahkan size: {size} | stok: {stock}") 
        db.session.commit()

        flash('Produk berhasil ditambahkan', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_product.html')


@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']

        # Jika upload gambar baru
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                image_path = os.path.join('static/uploads', image.filename)
                image.save(image_path)
                product.image = f'uploads/{image.filename}'

        # Hapus ukuran lama
        ProductSize.query.filter_by(product_id=product.id).delete()

        # Tambah ukuran baru
        sizes = request.form.getlist('size[]')
        stocks = request.form.getlist('stock[]')

        for size, stock in zip(sizes, stocks):
            new_size = ProductSize(size=size, stock=int(stock), product=product)
            db.session.add(new_size)

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', product=product)


@app.route('/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Produk berhasil dihapus.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/ganti_password', methods=['GET', 'POST'])
@admin_required
def ganti_password():
    admin = Admin.query.first()
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not admin.check_password(current_password):
            flash('Password lama salah!', 'danger')
        elif new_password != confirm_password:
            flash('Password baru tidak cocok!', 'danger')
        else:
            admin.set_password(new_password)
            db.session.commit()
            flash('Password berhasil diganti.', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('ganti_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Registrasi berhasil, silakan login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login berhasil!", "success")
            return redirect(url_for('index'))
        flash("Username atau password salah", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Berhasil logout", "info")
    return redirect(url_for('index'))

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/produk')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/checkout/<int:id>', methods=['GET', 'POST'])
@login_required
def checkout(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        size = request.form['size']
        quantity = int(request.form['quantity'])

        selected_size = ProductSize.query.filter_by(product_id=id, size=size).first()
        if not selected_size or selected_size.stock < quantity:
            flash('Stok tidak mencukupi untuk ukuran tersebut.', 'danger')
        else:
            selected_size.stock -= quantity
            db.session.commit()
            total = quantity * product.price

            phone = '6289671561543'
            message = f"Halo, saya ingin membeli:\n\n\ud83d\udce6 *{product.name}*\n\ud83d\udc55 Ukuran: *{size}*\n\ud83d\udccf Jumlah: *{quantity}*\n\ud83d\udcb5 Total: *Rp {total:,}*"
            wa_url = f"https://wa.me/{phone}?text={quote(message)}"
            return redirect(wa_url)

    return render_template('checkout.html', product=product)

def create_tables():
    db.create_all()
    if not Product.query.first():
        p1 = Product(name='Kaos Polos', image='uploads/kaos_polos.jpg', price=50000)
        p1.sizes = [ProductSize(size='S', stock=5), ProductSize(size='M', stock=3), ProductSize(size='L', stock=0)]
        db.session.add(p1)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)