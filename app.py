# @redears-lambda TODO: create dummy items, transactions, and likes
from datetime import datetime
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap5
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from PIL import Image
from flask_msearch import Search
from werkzeug.utils import secure_filename
from wtforms import (
    BooleanField,
    EmailField,
    FileField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, ValidationError


######## APP INIT ########

app = Flask(__name__)
Bootstrap5(app)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WHOOSH_BASE"] = "whoosh"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
search = Search(app, db)


######## LOGIN MANAGER ########


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("render_login"))


######## MODELS ########


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("Item", backref="author", lazy=True)
    bought = db.relationship(
        "Transaction", foreign_keys="Transaction.user_id", backref="buyer", lazy=True
    )
    sold = db.relationship(
        "Transaction", foreign_keys="Transaction.vendor_id", backref="seller", lazy=True
    )
    reviews = db.relationship(
        "Review", foreign_keys="Review.user_id", backref="author", lazy=True
    )
    reviewed = db.relationship(
        "Review", foreign_keys="Review.recipient_id", backref="getter", lazy=True
    )
    liked = db.relationship(
        "ItemLike", foreign_keys="ItemLike.user_id", backref="user", lazy=True
    )

    @property
    def ratings(self):
        return len(self.reviewed)

    @property
    def rating(self):
        total = 0
        reviews = self.reviewed
        if reviews:
            for review in reviews:
                total += review.rating
            average = total / len(self.reviewed)
            return "{:.1f}".format(average)
        return "No reviews yet"

    def __repr__(self):
        return f"User(username='{self.username}',email='{self.email}',image_file='{self.image_file}')"

    def like_item(self, item):
        if not self.has_liked_item(item):
            like = ItemLike(user_id=self.id, item_id=item.id)
            db.session.add(like)

    def unlike_item(self, item):
        if self.has_liked_item(item):
            ItemLike.query.filter_by(user_id=self.id, item_id=item.id).delete()

    def has_liked_item(self, item):
        return (
            ItemLike.query.filter(
                ItemLike.user_id == self.id, ItemLike.item_id == item.id
            ).count()
            > 0
        )


class Item(db.Model):
    __searchable__ = ["name", "description"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(20), nullable=True)
    base_price = db.Column(db.Float, nullable=False)
    image_file = db.Column(db.String(200), nullable=False, default="default.jpg")
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    likes = db.relationship("ItemLike", backref="item", lazy=True)
    status = db.Column(
        db.String(10), nullable=False, default="available"
    )  # "available" or "sold"

    @property
    def price(self):
        return "{:.2f}".format(self.base_price)

    def __repr__(self):
        return f"Item(name='{self.name}',date_posted='{self.date_posted}',image_file='{self.image_file}')"


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.Integer, db.ForeignKey("transaction.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Review(user_id={self.user_id},recipient_id={self.recipient_id},rating={self.rating},comment='{self.comment}')"


class ItemLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)

    def __repr__(self):
        return f"ItemLike(user_id={self.user_id},item_id={self.item_id})"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date_transacted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Transaction(user_id={self.user_id},vendor_id={self.vendor_id},item_id={self.item_id},value={self.value},date_transacted='{self.date_transacted}')"

######## INDEXING ######## 

######## FORMS ########


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and (user.password != self.password.data):
            raise ValidationError("Wrong Username or Password. Please check again.")

    def validate_password(self, password):
        user = User.query.filter_by(username=self.username.data).first()
        if user and (user.password != password.data):
            raise ValidationError("Wrong Username or Password. Please check again.")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(8, 150)])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class ForgetForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    search = StringField(
        validators=[DataRequired()], render_kw={"placeholder": "Enter Search"}
    )
    submit = SubmitField("Search")


class PaymentForm(FlaskForm):
    MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    YEARS = [str(i) for i in range(2023, 2031)]
    name = StringField(
        "Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your name"},
    )
    card_number = StringField(
        "Card",
        validators=[DataRequired(), Length(16)],
        render_kw={"placeholder": "0000 0000 0000 0000"},
    )
    month = SelectField("Expiry Month", validators=[DataRequired()], choices=MONTHS)
    year = SelectField("Expiry Year", validators=[DataRequired()], choices=YEARS)
    cvv = IntegerField("CVV", validators=[DataRequired(3)])
    submit = SubmitField("Enter")


class AddItemForm(FlaskForm):
    CATEGORIES = ["Fish", "Food", "Tank", "Decoration", "Utilties"]
    image_file = FileField(
        "Item Image",
        validators=[FileRequired(), FileAllowed(["jpg", "png"], "Images Only")],
    )
    name = StringField("Item Name", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()], choices=CATEGORIES)
    description = TextAreaField("Description", validators=[DataRequired()])
    base_price = FloatField("Price", validators=[DataRequired()])
    add = SubmitField("Add")


class ProfilePictureForm(FlaskForm):
    image_file = FileField(
        "New Profile Picture",
        validators=[FileRequired(), FileAllowed(["jpg", "png"], "Images Only")],
    )
    apply = SubmitField("Apply")


class UsernameForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    apply = SubmitField("Apply")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )


class DescriptionForm(FlaskForm):
    description = StringField(
        "Description", validators=[DataRequired(), Length(max=500)]
    )
    apply = SubmitField("Apply")


class ReviewForm(FlaskForm):
    choices = [1, 2, 3, 4, 5]
    rating = SelectField("Rating", validators=[DataRequired()], choices=choices)
    comment = TextAreaField(
        "Comment",
        validators=[DataRequired(), Length(5, 500)],
        render_kw={"placeholder": "Enter your comment here"},
    )
    submit = SubmitField("Submit")


######## ROUTES ########


@app.route("/")
def render_landing():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def render_login():
    if current_user.is_authenticated:
        return redirect("home")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and (user.password == form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect("home")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def render_register():
    if current_user.is_authenticated:
        return redirect("home")
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        user = User(username=username, email=email, password=password)
        db.session().add(user)
        db.session().commit()
        return redirect("login")

    return render_template("register.html", form=form)


@app.route("/forget", methods=["GET", "POST"])
def render_forget():
    if request.method == "GET":
        return render_template("forget.html", form=ForgetForm())
    elif request.method == "POST":
        data = request.form
        return jsonify(data)


@app.route("/home")
def render_home():
    search_form = SearchForm()
    items = Item.query.filter_by(status="available").limit(4).all()
    # NOTE : pretend r_items is a long list of reccomended items
    r_items = items + items
    f_items = items
    l_items = []

    if current_user.is_authenticated:
        for like in current_user.liked:
            item = Item.query.filter_by(id=like.item_id).first()
            l_items.append(item)
    return render_template(
        "home.html",
        f_items=f_items,
        r_items=r_items,
        l_items=l_items,
        search_form=search_form,
    )


@app.route("/item/<int:item_id>")
def render_item(item_id):
    r_items = Item.query.filter_by(status="available").limit(4).all()
    form = SearchForm()
    item = Item.query.filter_by(id=item_id).first()
    vendor = User.query.filter_by(id=item.user_id).first()
    v_sold_count = len(vendor.sold)
    reviews = vendor.reviewed[:4]
    review_authors = [
        User.query.filter_by(id=review.user_id).first() for review in reviews
    ]
    reviews = list(zip(review_authors, reviews))
    if item:
        return render_template(
            "item.html",
            form=form,
            item=item,
            vendor=vendor,
            r_items=r_items,
            v_sold_count=v_sold_count,
            reviews=reviews,
        )


@app.route("/buy/<int:item_id>", methods=["GET", "POST"])
@login_required
def render_buy(item_id):
    search_form = SearchForm()
    form = PaymentForm()
    if form.validate_on_submit():
        item = Item.query.filter_by(id=item_id).first()
        vendor = User.query.filter_by(id=item.user_id).first()
        name = form.name.data
        card_number = form.card_number.data
        month = form.month.data
        year = form.year.data
        cvv = form.cvv.data

        ### --------------------------- ###
        ### --------------------------- ###
        ### INSERT CARD VALIDATION HERE ###
        ### --------------------------- ###
        ### --------------------------- ###

        item.status = "bought"
        transaction = Transaction(
            user_id=current_user.id,
            item_id=item.id,
            vendor_id=vendor.id,
            value=item.base_price,
        )
        db.session.add(transaction)
        db.session.commit()
        transaction = Transaction.query.filter_by(item_id=item.id).first()
        return redirect(url_for("render_review", transaction_id=transaction.id))

    return render_template("buy.html", search_form=search_form, form=form)


@app.route("/likes")
@login_required
def render_likes():
    search_form = SearchForm()
    l_items = []
    r_items = Item.query.filter_by(status="available").limit(4).all()
    if current_user.is_authenticated:
        for like in current_user.liked:
            item = Item.query.filter_by(id=like.item_id).first()
            l_items.append(item)

    return render_template(
        "likes.html", search_form=search_form, l_items=l_items, r_items=r_items
    )


@app.route("/myitems")
@login_required
def render_my_items():
    search_form = SearchForm()
    b_transactions = current_user.bought
    b_items = [
        Item.query.filter_by(id=transaction.item_id).first()
        for transaction in b_transactions
    ]
    s_transactions = current_user.sold
    s_items = [
        Item.query.filter_by(id=transaction.item_id).first()
        for transaction in s_transactions
    ]
    L_items = Item.query.filter_by(user_id=current_user.id, status="available").all()
    return render_template(
        "my_item.html",
        search_form=search_form,
        b_items=b_items,
        s_items=s_items,
        L_items=L_items,
    )


@app.route("/item/add", methods=["GET", "POST"])
@login_required
def render_add_item():
    search_form = SearchForm()
    form = AddItemForm()
    if form.validate_on_submit():
        image_file_name = form.image_file.data.filename
        file_extentsion = image_file_name[-3:]
        name = form.name.data
        category = form.category.data
        description = form.description.data
        base_price = form.base_price.data

        unique_file_name = uuid4()
        filename = secure_filename(f"{unique_file_name}.{file_extentsion}")
        form.image_file.data.save(f"./static/img/fish/{filename}")
        item = Item(
            user_id=current_user.id,
            name=name,
            description=description,
            category=category,
            base_price=base_price,
            image_file=filename,
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("render_my_items"))
    return render_template("add_item.html", search_form=search_form, form=form)


@app.route("/profile/<int:user_id>", methods=["GET", "POST"])
def render_profile(user_id):
    user = User.query.filter_by(id=user_id).first()
    search_form = SearchForm()
    pfp_form = ProfilePictureForm()
    username_form = UsernameForm()
    description_form = DescriptionForm()
    L_items = Item.query.filter_by(id=user.id, status="available").all()
    len_of_L_items = len(L_items)
    reviews = user.reviewed
    review_authors = [
        User.query.filter_by(id=review.user_id).first() for review in reviews
    ]
    reviews = list(zip(review_authors, reviews))

    if pfp_form.validate_on_submit():
        ### SAVE FILE ###
        image_file_name = pfp_form.image_file.data.filename
        file_extention = image_file_name[-3:]
        unique_file_name = uuid4()
        filename = secure_filename(f"{unique_file_name}.{file_extention}")
        pfp_form.image_file.data.save(f"./static/img/profile/{filename}")

        ### CROP IMAGE ###
        im = Image.open(f"./static/img/profile/{filename}")
        width, height = im.size
        new_width = 250
        new_height = 250
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2
        im = im.crop((left, top, right, bottom))
        im.save(f"./static/img/profile/{filename}")

        ### CHANGE USER IMAGE FILE NAME ###
        current_user.image_file = filename
        db.session.commit()
        return redirect(url_for("render_profile"))

    if username_form.validate_on_submit():
        current_user.username = username_form.username.data
        db.session.commit()
        return redirect(url_for("render_profile"))

    if description_form.validate_on_submit():
        current_user.description = description_form.description.data
        db.session.commit()
        return redirect(url_for("render_profile"))

    return render_template(
        "profile.html",
        search_form=search_form,
        L_items=L_items,
        pfp_form=pfp_form,
        username_form=username_form,
        description_form=description_form,
        len_of_L_items=len_of_L_items,
        reviews=reviews,
        user=user,
    )


@app.route("/review/<int:transaction_id>", methods=["GET", "POST"])
def render_review(transaction_id):
    search_form = SearchForm()
    form = ReviewForm()
    if form.validate_on_submit():
        transaction = Transaction.query.filter_by(id=transaction_id).first()
        user_id = transaction.user_id
        recipient_id = transaction.vendor_id
        rating = form.rating.data
        comment = form.comment.data
        review = Review(
            user_id=user_id,
            recipient_id=recipient_id,
            rating=rating,
            comment=comment,
            transaction_id=transaction_id,
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for("render_home"))

    return render_template("review.html", form=form, search_form=search_form)


@app.route("/search")
def render_search():
    search_form = SearchForm()
    search = request.args.get("search")
    items = Item.query.msearch(search,fields=['name','description'])
    count_of_items = len(list(items))
    return render_template("search.html", search_form=search_form, items=items, search=search, count_of_items=count_of_items)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("home")


@app.route("/like/<int:item_id>/<action>")
@login_required
def like_action(item_id, action):
    item = Item.query.filter(id=item_id).first()
    if action == "like":
        current_user.like_item(item)
        db.session.commit()
    if action == "unlike":
        current_user.unlike_item(item)
        db.session.commit()
    return redirect(request.referrer)


if __name__ == "__main__":
    app.run(debug=True)
