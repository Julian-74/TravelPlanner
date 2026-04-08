from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from models import TripPlanner
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Check config on startup
Config.check_config()

class TripForm(FlaskForm):
    origin = StringField('From', validators=[DataRequired()])
    destination = StringField('To', validators=[DataRequired()])
    dates = StringField('Dates (YYYY-MM-DD to YYYY-MM-DD)', validators=[DataRequired()])
    budget = FloatField('Budget ($)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Plan My Trip')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TripForm()
    if form.validate_on_submit():
        try:
            planner = TripPlanner(
                origin=form.origin.data,
                destination=form.destination.data,
                dates=form.dates.data,
                budget=form.budget.data
            )
            itinerary = planner.generate_itinerary()
            return render_template('itinerary.html', 
                                 itinerary=itinerary, 
                                 form=form)
        except Exception as e:
            flash(f'Planning failed: {str(e)}', 'error')
            return render_template('index.html', form=form)
    return render_template('index.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
