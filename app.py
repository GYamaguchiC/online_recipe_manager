from datetime import datetime
from flask import Flask, render_template, url_for, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import os
from flask_migrate import Migrate

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True)
    password = db.Column(db.String(80), nullable = False)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255), nullable = False)
    ingredients = db.Column(db.String(1000), nullable = False)
    method = db.Column(db.String(5000), nullable = False)
    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='recipes')

class RegisterForm(FlaskForm):
    username = StringField(validators = [InputRequired(), Length(min = 4, max= 20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username = username.data).first()
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different one.")
        
    
class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    ingredients = TextAreaField('Ingredients', validators=[InputRequired()])
    method = TextAreaField('Method', validators=[InputRequired()])
    submit = SubmitField('Add Recipe')
        
class LoginForm(FlaskForm):
    username = StringField(validators = [InputRequired(), Length(min = 4, max= 20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")
        

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(title=form.title.data,
                        ingredients=form.ingredients.data,
                        method=form.method.data,
                        author=current_user)
        db.session.add(recipe)
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('add_recipe.html', form=form)


@app.route('/see_recipes')
def see_recipes():
    page = request.args.get('page', 1, type=int)
    per_page = 2
    recipes = Recipe.query.paginate(page=page, per_page=per_page)
    return render_template('see_recipes.html', recipes=recipes)


@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        abort(404)
    return render_template('recipe_detail.html', recipe=recipe)


if __name__ == "__main__":
    if not os.path.exists('database.db'):
        db.create_all()
    app.run(debug=True)