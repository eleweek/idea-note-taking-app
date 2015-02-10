from flask import Flask
from flask import render_template, abort, flash, request
from flask_bootstrap import Bootstrap

from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import current_user, login_required
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin

import os
import wtf_helpers


class IdeaForm(Form):
    idea_name = StringField('Idea name', validators=[DataRequired()])
    is_private = BooleanField('private')
    submit_button = SubmitField('Add idea')

app = Flask(__name__)
# in a real app, these should be configured through Flask-Appconfig
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = False
app.config['SECURITY_FLASH_MESSAGES'] = True

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    ideas = db.relationship('Idea', backref='user', lazy='dynamic')

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idea_name = db.Column(db.String(140))
    is_private = db.Column(db.Boolean())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, idea, user):
        self.idea_name = idea
        self.user_id = user.id

    def __repr__(self):
        return '<Idea %r>' % self.id


db.create_all()

Bootstrap(app)
wtf_helpers.add_helpers(app)


@app.route("/")
def index():
    users = User.query
    return render_template("index.html", users=users)


@app.route("/edit_idea/<idea_id>", methods=["GET", "POST"])
@login_required
def edit_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    if idea.user_id != current_user.id:
        abort(403)

    form = IdeaForm()
    if request.method == "GET":
        form.is_private.data = idea.is_private
        form.idea_name.data = idea.idea_name

    if form.validate_on_submit():
        idea.is_private = form.is_private.data
        idea.name = form.idea_name.data
        db.session.commit()
        flash("Idea was changed successfully", "success")

    return render_template("edit_idea.html", form=form)


@app.route("/ideas/<user_email>/<privacy_filter>", methods=["GET", "POST"])
@app.route("/ideas/<user_email>", defaults={'privacy_filter': 'public'}, methods=["GET", "POST"])
def ideas(user_email, privacy_filter):
    user = User.query.filter_by(email=user_email).first_or_404()
    if privacy_filter == 'private' and user != current_user:
        abort(403)
    elif privacy_filter == 'private':
        is_private = True
    elif privacy_filter == 'public':
        is_private = False
    else:
        abort(404)

    if user == current_user:
        form = IdeaForm()
    else:
        form = None

    if form and form.validate_on_submit():
        # TODO: populate_obj?
        idea = Idea(form.idea_name.data, user)
        idea.is_private = form.is_private.data
        form.idea_name.data = ""
        db.session.add(idea)
        db.session.commit()
        flash("Idea was added successfully", "success")

    list_of_ideas = user.ideas.filter_by(is_private=is_private)
    return render_template("ideas.html", form=form, list_of_ideas=list_of_ideas, user_email=user_email, is_private=is_private)

if __name__ == "__main__":
    app.run(debug=True)
