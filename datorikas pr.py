from flask import Flask, request, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField, StringField, DecimalField, FileField
from wtforms.validators import Email, DataRequired
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'any secret key'

# Database Setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employee.db"
db = SQLAlchemy(app)

# Employee Model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    salary = db.Column(db.Numeric, nullable=False)
    references = db.Column(db.String)

    def __repr__(self):
        return f"({self.name}, {self.email}, {self.salary})"

# FlaskForm
class EmployeeForm(FlaskForm):
    id = HiddenField()
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    salary = DecimalField('Salary', validators=[DataRequired()])
    submit = SubmitField("Save")
    file = FileField("Upload CSV")

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/employee", methods=["GET", "POST"])
def createEmployee():
    form = EmployeeForm(request.form)
    employees = Employee.query.all()

    if form.validate_on_submit():
        employee = Employee(name=form.name.data, email=form.email.data, salary=form.salary.data)
        db.session.add(employee)
        db.session.commit()
        db.session.refresh(employee)
        flash("Added Employee Successfully")
        return redirect(url_for("createEmployee"))
    
    return render_template("employee.html", title="Employee", form=form, employees=employees)

@app.route("/updateEmployee/<int:employee_id>", methods=["GET", "POST"])
def updateEmployee(employee_id):
    employee = Employee.query.get(employee_id)
    form = EmployeeForm(request.form, obj=employee)
    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        flash("Updated Employee Successfully")
        return redirect(url_for("createEmployee"))
    return render_template("employee.html", title="Employee", form=form, employees=Employee.query.all())

@app.route("/deleteEmployee/<int:employee_id>", methods=["POST"])
def deleteEmployee(employee_id):
    employee = Employee.query.get(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for("createEmployee"))

# CSV Upload Route
@app.route("/uploadCSV", methods=["POST"])
def uploadCSV():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        data = pd.read_csv(file)
        # Assuming CSV contains columns 'name', 'email', 'salary'
        for _, row in data.iterrows():
            employee = Employee(name=row['name'], email=row['email'], salary=row['salary'])
            db.session.add(employee)
        db.session.commit()
        flash(f"Successfully added {len(data)} employees from the CSV!")
        return redirect(url_for("createEmployee"))
    flash("Invalid file format, please upload a CSV.")
    return redirect(request.url)

# Helper function to check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['csv']

# Data Visualization Route
@app.route("/visualize")
def visualizeData():
    # Get all employee data
    employees = Employee.query.all()
    names = [emp.name for emp in employees]
    salaries = [emp.salary for emp in employees]

    # Create a bar chart of salaries
    fig, ax = plt.subplots()
    ax.bar(names, salaries)
    ax.set_xlabel('Employee')
    ax.set_ylabel('Salary')
    ax.set_title('Employee Salaries')

    # Convert plot to PNG image for web display
    img = BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template("visualize.html", img_data=img_data)

@app.route("/filter", methods=["GET", "POST"])
def filterData():
    name_filter = request.args.get('name')
    salary_filter = request.args.get('salary')
    
    query = Employee.query
    if name_filter:
        query = query.filter(Employee.name.contains(name_filter))
    if salary_filter:
        query = query.filter(Employee.salary >= float(salary_filter))
    
    filtered_employees = query.all()
    return render_template("employee.html", employees=filtered_employees)

# Create database tables
with app.app_context():
    db.create_all()

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5001)