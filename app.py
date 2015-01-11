from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap

from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class IdeaForm(Form):
    idea = StringField('idea', validators=[DataRequired()])
    submit_button = SubmitField('Add idea')

app = Flask(__name__)
# in a real app, these should be configured through Flask-Appconfig
app.config['SECRET_KEY'] = 'devkey'

Bootstrap(app)


@app.route("/")
def hello():
    form = IdeaForm()
    return render_template("index.html", form=form)

if __name__ == "__main__":
    app.run(debug=True)
