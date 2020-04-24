from flask import Flask, render_template, render_template_string, flash, redirect, url_for, request
app = Flask(__name__)

from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from wtforms import StringField, PasswordField, BooleanField, \
        SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Regexp
from wtforms.widgets import html_params

from flask_login import LoginManager, UserMixin, current_user, \
        login_user, logout_user, login_required
login_manager = LoginManager()
login_manager.init_app(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

import yaml

from pathlib import Path

import re

from markupsafe import Markup

from hashlib import md5

BASE_PATH = Path(__file__).parent

with (BASE_PATH / 'config.yaml').open() as f:
    config = yaml.safe_load(f)
    for key, value in config['flask'].items():
        app.config[key] = value

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

import secrets

from flask_mail import Mail, Message

mail = Mail(app)

from flaskext.markdown import Markdown

Markdown(app)

from html2text import HTML2Text

text_maker = HTML2Text()
text_maker.ignore_links = True

class MyUser(UserMixin):
    def __init__(self, id, data):
        self.data = data.copy()
        self.id = id
        self.data['username'] = id
    
    @property
    def is_active(self):
        return self.data['state'] == 'enabled'

    def get_id(self):
        return self.id

    def check_password(self, password):
        return bcrypt.check_password_hash(self.data['hashed_password'], password)

    def set_password(self, new_password):
        self.data['hashed_password'] = bcrypt.generate_password_hash(new_password)

    def send_activation_email(self):
        token = secrets.token_urlsafe(16)
        self.data['activation_hash'] = token
        msg = Message(config['activation_email']['subject'])
        msg.recipients = [(self.data['fullname'], self.data['email'])]
        msg.sender = config['activation_email']['from']
        link = url_for('activate_user', username=self.get_id(), hash=token, _external=True)
        msg_md = render_template('activation-email.md', link=link, user=self)
        msg.html = render_template_string('{{ md | markdown }}', md=msg_md)
        msg.body = text_maker.handle(msg.html)
        mail.send(msg)
    
    def send_reset_email(self):
        token = secrets.token_urlsafe(16)
        self.data['reset_hash'] = token
        msg = Message(config['reset_email']['subject'])
        msg.recipients = [(self.data['fullname'], self.data['email'])]
        msg.sender = config['reset_email']['from']
        link = url_for('reset_password', username=self.get_id(), hash=token, _external=True)
        msg_md = render_template('reset-email.md', link=link, user=self)
        msg.html = render_template_string('{{ md | markdown }}', md=msg_md)
        msg.body = text_maker.handle(msg.html)
        mail.send(msg)

    def activate(self, hash):
        if hash and self.data.get('activation_hash') == hash:
            self.data['state'] = 'enabled'
            self.data.pop('activation_hash')
            return True
        return False

    def allow_reset(self, hash):
        if hash and self.data.get('reset_hash') == hash:
            self.data['state'] = 'enabled'
            self.data.pop('reset_hash')
            return True
        return False

    def avatar(self, size):
        digest = md5(self.data['email'].lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=mp&s={}'.format(
            digest, size)

    general_fields = ['fullname', 'email', 'timezone', 'digest_allowed']


@login_manager.user_loader
def load_user(user_id):
    if not re.match(config['username_regexp'], user_id):
        return None
    try:
        with (BASE_PATH / ('data/accounts/%s.yaml' % (user_id,))).open() as f:
            data = yaml.safe_load(f)
            data['username'] = user_id
            user = MyUser(user_id, data)
            return user
    except FileNotFoundError:
        return None

def find_user_by_email(email):
    for path in (BASE_PATH / 'data/accounts').iterdir():
        if path.suffix=='.yaml':
            username = path.name[:-5]
            user = load_user(username)
            if user.data['email'] == email:
                return user
    return None

def flash_errors(form):
    for _, errors in form.errors.items():
        for error in errors:
            flash(error, 'error')

def save_user(user):
    with (BASE_PATH / ('data/accounts/%s.yaml' % (user.get_id(),))).open('w') as f:
        data = user.data.copy()
        data.pop('username')
        yaml.dump(data, f)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Confirm')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already signed in', 'default')
        return redirect(url_for('index'))
    page = { 'menu_item': 'login' }
    form = LoginForm()
    if form.validate_on_submit():
        user = load_user(form.username.data)
        if user and user.check_password(form.password.data):
            if user.is_active:
                login_user(user, remember = form.remember_me.data)
                flash('You have successfully signed in.', 'success')
                return redirect(url_for('profile'))
            else:
                flash('You cannot sign in because your account has not been activated. Please \
                    check your mailbox %s for the activation email. If it is \
                    not there, please check your spam folder.' % (user.data['email']), 'error')
        else:
            flash('The username or password is incorrect.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html', config=config, page=page, form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have signed out.', 'success')
    return redirect(url_for('index'))

with (BASE_PATH / 'timezones.yaml').open() as f:
    timezones = yaml.safe_load(f)
    timezone_choices = []
    for optgroup0 in timezones:
        for optgroup, options in optgroup0.items():
            for key, value in options.items():
                timezone_choices.append((key, value))

def timezone_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    res = render_template('timezones.html', \
            args=html_params(name=field.name, **kwargs), \
            placeholder=kwargs.get('placeholder', None),
            timezones=timezones, field=field)
    return Markup(res)

class ProfileForm(FlaskForm):
    username = StringField('Username')
    fullname = StringField('Full name', validators=[DataRequired()])
    email = StringField('Click here to change the email (needs re-activation)', validators=[DataRequired(), Email()])
    timezone = SelectField('Timezone', validators=[DataRequired()], \
            widget=timezone_widget, choices=timezone_choices)
    digest_allowed = BooleanField('Subscribe to the weekly digest (talks next week and recent news every Sunday)', \
            default=True)
    password = PasswordField('Change password')
    submit = SubmitField('Save')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    page = { 'menu_item': 'profile' }
    if request.method=='GET':
        form = ProfileForm(data=current_user.data)
    else:
        form = ProfileForm()
        if form.validate_on_submit():
            data = form.data
            email_changed = (form.email.data != current_user.data['email'])
            if email_changed and find_user_by_email(form.email.data):
                flash('Email %s already exists, please pick another email address' % (form.email.data,), \
                        'error')
            else:
                if data['password']:
                    current_user.set_password(form.password.data)
                for key in MyUser.general_fields:
                    current_user.data[key] = data[key]
                if email_changed:
                    current_user.data['state'] = 'disabled'
                    current_user.send_activation_email()
                save_user(current_user)
                if email_changed:
                    flash('You changed your email address. Your account needs to be re-activated. \
                    An activation email with instructions \
                    has been send to the address %s. Please follow the instructions to activate \
                    your account. If you didn\'t receive the activation email, please check your \
                    spam folder.' % (form.email.data,), 'warning')
                else:
                    flash('Your changes have been saved.', 'success')
                return redirect(url_for('profile'))
    form.username.data = current_user.get_id()
    flash_errors(form)
    return render_template('profile.html', config=config, page=page, form=form)
    

class RegisterForm(ProfileForm):
    username = StringField('Username', validators=[DataRequired(), 
        Regexp(config['username_regexp'], 0, 'Username can only contain lowercase letters, \
                numbers and symbols ._-. Username must be at least 3 characters long.')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Enter a password', validators=[DataRequired(),
        Regexp(config['password_regexp'], 0, 'Password must contain at least one lowercase \
                letter, one uppercase letter, and one number. Password must be \
                at least 8 characters long')])
    agree_terms = BooleanField(config['agree_terms_label'], validators=[DataRequired()])
    recaptcha = RecaptchaField(validators=[Recaptcha('Please confirm you are human')])
    submit = SubmitField('Register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already signed in', 'default')
        return redirect(url_for('index'))
    page = { 'menu_item': 'profile' }
    form = RegisterForm()
    if form.validate_on_submit():
        if load_user(form.username.data):
            flash('Username %s has been already taken. Please choose a different username.'\
                    % (form.username.data,), 'error')
        elif find_user_by_email(form.email.data):
            flash('Email %s already exists, please pick another email address' % (form.email.data,), \
                        'error')
        else:
            user_data = {}
            data = form.data
            for key in MyUser.general_fields:
                user_data[key] = data[key]

            user = MyUser(form.username.data, user_data)
            user.set_password(form.password.data)
            user.data['state'] = 'disabled'
            user.send_activation_email()
            save_user(user)
            flash('Your registration has been successful. An activation email with instructions \
                    has been send to the address %s. Please follow the instructions to activate \
                    your account. If you didn\'t receive the activation email, please check your \
                    spam folder.' % (user.data['email'],), 'success')
            return redirect(url_for('index'))
    flash_errors(form)
    return render_template('register.html', config=config, page=page, form=form)

class ActivateUserForm(FlaskForm):
    title = 'Account activation'
    username = StringField('Username', validators=[DataRequired()])
    hash = StringField('Activation token', validators=[DataRequired()])
    submit = SubmitField('Activate your account')

@app.route('/activate', methods=['GET', 'POST'])
def activate_user(username=None, hash=None):
    page = { 'menu_item': 'login' }
    form = ActivateUserForm()
    if form.validate_on_submit():
        user = load_user(form.username.data)
        hash = form.hash.data
        if user and hash and user.activate(hash):
            save_user(user)
            if current_user.is_authenticated:
                flash('Your account has been activated successfully.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Your account has been activated successfully. You can sign in now.', 'success')
                return redirect(url_for('login'))
        flash('Something went wrong. Please contact support.', 'error')
    else:
        username = request.args.get('username')
        hash = request.args.get('hash')
        if username:
            form.username.data = username
        if hash:
            form.hash.data = hash
    flash_errors(form)
    return render_template('simple-form.html', config=config, page=page, form=form)


class ForgotPasswordForm(FlaskForm):
    title = 'Password recovery'
    email = StringField('Please enter your Email', validators=[DataRequired(), Email()])
    recaptcha = RecaptchaField(validators=[Recaptcha('Please confirm you are human')])
    submit = SubmitField('Send reset instructions')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        flash('You are already signed in', 'default')
        return redirect(url_for('index'))
    page = { 'menu_item': 'login' }
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = find_user_by_email(email)
        if user:
            user.send_reset_email()
            save_user(user)
            flash('Password reset instructions have been sent to %s' % (email,), 'success')
            return redirect(url_for('login'))
        else:
            flash('Email does not exist', 'error')
    flash_errors(form)
    return render_template('simple-form.html', config=config, page=page, form=form)

class PasswordResetForm(FlaskForm):
    title = 'Change your password'
    username = StringField('Username', validators=[DataRequired()])
    hash = StringField('Security token', validators=[DataRequired()])
    password = PasswordField('Enter a new password', validators=[DataRequired(),
        Regexp(config['password_regexp'], 0, 'Password must contain at least one lowercase \
                letter, one uppercase letter, and one number. Password must be \
                at least 8 characters long')])
    submit = SubmitField('Change password')

@app.route('/reset', methods=['GET', 'POST'])
def reset_password(username=None, hash=None):
    page = { 'menu_item': 'login' }
    if current_user.is_authenticated:
        flash('You are already signed in', 'default')
        return redirect(url_for('index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = load_user(form.username.data)
        hash = form.hash.data
        if user and user.allow_reset(hash):
            user.set_password(form.password.data)
            save_user(user)
            flash('Your password has been changed. You can sign in now.', 'success')
            return redirect(url_for('login'))
        flash('Your reset link is invalid. Try again.', 'error')
        return redirect(url_for('forgot_password'))
    else:
        username = request.args.get('username')
        hash = request.args.get('hash')
        if username:
            form.username.data = username
        if hash:
            form.hash.data = hash
    flash_errors(form)
    return render_template('simple-form.html', config=config, page=page, form=form)

@app.route('/news')
def news():
    page = { 'menu_item': 'news' }
    return render_template('body.html', config=config, page=page)

app.add_url_rule('/', 'index', news)

@app.route('/events')
def events():
    page = { 'menu_item': 'events' }
    return render_template('body.html', config=config, page=page)

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')

