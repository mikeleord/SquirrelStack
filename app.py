"""
This file is part of Family Budget Web App AKA SquirrelStack.
Family Budget Web App AKA SquirrelStack is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Family Budget Web App AKA SquirrelStack is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Family Budget Web App AKA SquirrelStack.  If not, see <https://www.gnu.org/licenses/>.        
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from models.models import FinancialCalendar, SavingsProjectDeadline, SavingsProject, FutureExpense, db, Expense, Tag, Income, Savings, expense_tag, income_tag, savings_tag
from datetime import datetime, date, timedelta
from dateutil.parser import parse
from sqlalchemy import extract
from sqlalchemy.sql import func
import csv
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
from flask_htpasswd import HtPasswdAuth
import os

db_path = os.path.join(os.path.dirname(__file__), 'db', 'budget.db')

app = Flask(__name__)
app.secret_key = 'il_tuo_segreto_chiave_qui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['FLASK_SECRET'] = 'MySuperMegaSECRET'
app.config['FLASK_HTPASSWD_PATH'] = './.htpasswd'
htpasswd = HtPasswdAuth(app)
financial_calendar = FinancialCalendar()
db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_current_month():
    current_month = datetime.now().strftime('%B %Y')
    return dict(current_month=current_month)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/')
@htpasswd.required
def home(user):
    current_date = date.today()
    start_of_month = current_date.replace(day=1)
    end_of_month = start_of_month + relativedelta(months=1) - timedelta(days=1)

    expenses = Expense.query.filter(Expense.date.between(start_of_month, end_of_month)).all()
    incomes = Income.query.filter(Income.date.between(start_of_month, end_of_month)).all()
    tags = Tag.query.all()
    balance_ron = sum(expense.amount_ron for expense in expenses)
    total_incomes_ron = sum(income.amount_ron for income in incomes)
    current_month = current_date.strftime('%B %Y')
    return render_template(
        'index.html', 
        expenses=expenses,
        balance_ron=balance_ron,
        tags=tags,
        current_month=current_month,
        incomes=incomes,
        total_incomes_ron=total_incomes_ron
    )

@app.route('/all')
@htpasswd.required
def show_all_entries(user):
    page_expenses = request.args.get('page_expenses', 1, type=int)
    page_incomes = request.args.get('page_incomes', 1, type=int)
    page_savings = request.args.get('page_savings', 1, type=int)

    expenses = Expense.query.paginate(page=page_expenses, per_page=10, error_out=False)
    incomes = Income.query.paginate(page=page_incomes, per_page=5, error_out=False)
    savings = Savings.query.paginate(page=page_savings, per_page=5, error_out=False)

    return render_template('all_entries.html', expenses=expenses, incomes=incomes, savings=savings)

@app.route('/delete_entry/<entry_type>/<entry_id>', methods=['POST'])
@htpasswd.required
def delete_entry(user, entry_type, entry_id):
    entry_models = {'expense': Expense, 'income': Income, 'savings': Savings}

    if entry_type not in entry_models:
        abort(400, description="Tipo di voce non valido")

    entry = entry_models[entry_type].query.get(entry_id)

    if entry:
        db.session.delete(entry)
        db.session.commit()

    return redirect(url_for('show_all_entries'))

@app.route('/add_expense', methods=['POST'])
@htpasswd.required
def add_expense(user):
    title = request.form.get('title')
    amount_ron = request.form.get('amount_ron')
    date_str = request.form.get('date')
    tags_str = request.form.get('tags')
    if not title or not amount_ron or not date_str or not tags_str:
        return redirect(url_for('home'))
    try:
        amount_ron = float(amount_ron)
    except ValueError:
        return redirect(url_for('home'))
    try:
        date = parse(date_str)
    except ValueError:
        date = datetime.utcnow()
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    tag_objects = [Tag.query.filter_by(name=tag).first() for tag in tags]
    new_expense = Expense(title=title, amount_ron=amount_ron, date=date, tags=tag_objects)
    try:
        db.session.add(new_expense)
        db.session.commit()
    except Exception as e:
        return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route('/tags')
@htpasswd.required
def manage_tags(user):
    page = request.args.get('page', 1, type=int)
    tags = Tag.query.paginate(page=page, per_page=10)
    return render_template('tags.html', tags=tags)

@app.route('/create_tag', methods=['POST'])
@htpasswd.required
def create_tag(user):
    tag_name = request.form['tag_name']
    
    existing_tag = Tag.query.filter_by(name=tag_name).first()
    if existing_tag:
        flash('Il tag esiste già', 'error')
    else:
        new_tag = Tag(name=tag_name)
        db.session.add(new_tag)
        db.session.commit()
        flash('Nuovo tag creato con successo', 'success')

    return redirect(url_for('manage_tags'))

@app.route('/delete_tag/<int:tag_id>', methods=['POST'])
@htpasswd.required
def delete_tag(user, tag_id):
    tag = Tag.query.get(tag_id)
    if tag:
        db.session.delete(tag)
        db.session.commit()
        flash('Il tag è stato eliminato con successo', 'success')
    else:
        flash('Il tag non esiste', 'error')
    return redirect(url_for('manage_tags'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@htpasswd.required
def delete_expense(user, expense_id):
    expense = Expense.query.get_or_404(expense_id)
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Spesa cancellata con successo', 'success')
    except Exception as e:
        flash(f"Errore nella cancellazione della spesa: {str(e)}", 'error')
    return redirect(url_for('home'))

@app.route('/add_income', methods=['POST'])
@htpasswd.required
def add_income(user):
    try:
        income_title = request.form['income_title']
        income_amount_ron = float(request.form['income_amount_ron'])
        income_date_str = request.form['income_date']
        income_tags_str = request.form['income_tags']
        income_date = parse(income_date_str)
        income_tags = [tag.strip() for tag in income_tags_str.split(',') if tag.strip()]
        tag_objects = [Tag.query.filter_by(name=tag).first() for tag in income_tags]
        new_income = Income(title=income_title, amount_ron=income_amount_ron, date=income_date, tags=tag_objects)
        db.session.add(new_income)
        db.session.commit()
    except ValueError:
        flash("Formato di data o importo non valido", 'error')
    except Exception as e:
        flash(f"Errore nell'aggiunta dell'introito: {str(e)}", 'error')
    return redirect(url_for('home'))

@app.route('/delete_income/<int:income_id>', methods=['POST'])
@htpasswd.required
def delete_income(user, income_id):
    income = Income.query.get_or_404(income_id)
    try:
        db.session.delete(income)
        db.session.commit()
        flash('Introito eliminato con successo', 'success')
    except Exception as e:
        flash(f"Errore nell'eliminazione dell'introito: {str(e)}", 'error')
    return redirect(url_for('home'))

@app.route('/savings')
@htpasswd.required
def manage_savings(user):
    current_date = date.today()
    start_of_month = current_date.replace(day=1)
    end_of_month = (current_date.replace(day=1, month=current_date.month % 12 + 1) - timedelta(days=1)) if current_date.month != 12 else current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    savings = Savings.query.filter(Savings.date.between(start_of_month, end_of_month)).all()
    total_savings_ron = sum(saving.amount_ron for saving in savings)
    tags = Tag.query.all()
    return render_template('savings.html', savings=savings, tags=tags, total_savings_ron=total_savings_ron)

@app.route('/add_saving', methods=['POST'])
@htpasswd.required
def add_saving(user):
    try:
        amount_ron = float(request.form['amount_ron'])
        date = parse(request.form['date'])
        tags = [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        tag_objects = [Tag.query.filter_by(name=tag).first() for tag in tags]
        new_saving = Savings(amount_ron=amount_ron, date=date, tags=tag_objects, project_id=10000)
        db.session.add(new_saving)
        db.session.commit()
    except ValueError:
        flash('Errore di formato nei dati inseriti. Assicurati di aver inserito una data e un importo validi.', 'error')
    except Exception as e:
        flash(f'Errore durante l\'aggiunta del risparmio: {str(e)}', 'error')
    return redirect(url_for('manage_savings'))

@app.route('/delete_saving/<int:saving_id>', methods=['POST'])
@htpasswd.required
def delete_saving(user, saving_id):
    saving = Savings.query.get_or_404(saving_id)
    try:
        db.session.delete(saving)
        db.session.commit()
        flash('Risparmio eliminato con successo', 'success')
    except Exception as e:
        flash(f'Errore durante l\'eliminazione del risparmio: {str(e)}', 'error')
    return redirect(url_for('manage_savings'))

@app.route('/summary_month')
@htpasswd.required
def summary_month(user):
    current_date = date.today()
    start_of_month = current_date.replace(day=1)
    end_of_month = (current_date.replace(day=1, month=current_date.month % 12 + 1) - timedelta(days=1)) if current_date.month != 12 else current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    data = {
        "expenses": {"query": Expense, "total": 0},
        "incomes": {"query": Income, "total": 0},
        "savings": {"query": Savings, "total": 0}
    }
    for key, value in data.items():
        value["items"] = value["query"].query.filter(value["query"].date.between(start_of_month, end_of_month)).all()
        value["total"] = sum(item.amount_ron for item in value["items"])
    return render_template(
        'summary_month.html',
        expenses=data["expenses"]["items"],
        incomes=data["incomes"]["items"],
        savings=data["savings"]["items"],
        total_expenses_ron=data["expenses"]["total"],
        total_incomes_ron=data["incomes"]["total"],
        total_savings_ron=data["savings"]["total"]
    )

@app.route('/summary_year')
@htpasswd.required
def summary_year(user):
    current_year = datetime.now().year
    current_year_data = []
    last_year_data = []
    for month in range(1, 13):
        expenses_current = Expense.query.filter(
            extract('year', Expense.date) == current_year,
            extract('month', Expense.date) == month
        ).all()
        incomes_current = Income.query.filter(
            extract('year', Income.date) == current_year,
            extract('month', Income.date) == month
        ).all()
        savings_current = Savings.query.filter(
            extract('year', Savings.date) == current_year,
            extract('month', Savings.date) == month
        ).all()
        total_expenses_current = sum(expense.amount_ron for expense in expenses_current)
        total_incomes_current = sum(income.amount_ron for income in incomes_current)
        total_savings_current = sum(saving.amount_ron for saving in savings_current)
        budget = total_incomes_current - (total_expenses_current + total_savings_current)
        current_year_data.append({
            "month": month,
            "total_expenses": total_expenses_current,
            "total_incomes": total_incomes_current,
            "total_savings": total_savings_current,
            "budget": budget
        })
    last_year = current_year - 1
    for month in range(1, 13):
        expenses_last = Expense.query.filter(
            extract('year', Expense.date) == last_year,
            extract('month', Expense.date) == month
        ).all()
        incomes_last = Income.query.filter(
            extract('year', Income.date) == last_year,
            extract('month', Income.date) == month
        ).all()
        savings_last = Savings.query.filter(
            extract('year', Savings.date) == last_year,
            extract('month', Savings.date) == month
        ).all()
        total_expenses_last = sum(expense.amount_ron for expense in expenses_last)
        total_incomes_last = sum(income.amount_ron for income in incomes_last)
        total_savings_last = sum(saving.amount_ron for saving in savings_last)
        budget = total_incomes_last - (total_expenses_last + total_savings_last)
        last_year_data.append({
            "month": month,
            "total_expenses": total_expenses_last,
            "total_incomes": total_incomes_last,
            "total_savings": total_savings_last,
            "budget": budget
        })

    total_expenses_year_current = sum(data["total_expenses"] for data in current_year_data)
    total_incomes_year_current = sum(data["total_incomes"] for data in current_year_data)
    total_savings_year_current = sum(data["total_savings"] for data in current_year_data)
    total_budget_year_current = sum(data["budget"] for data in current_year_data)

    total_expenses_year_last = sum(data["total_expenses"] for data in last_year_data)
    total_incomes_year_last = sum(data["total_incomes"] for data in last_year_data)
    total_savings_year_last = sum(data["total_savings"] for data in last_year_data)
    total_budget_year_last = sum(data["budget"] for data in last_year_data)

    all_time_expenses = Expense.query.all()
    all_time_incomes = Income.query.all()
    all_time_savings = Savings.query.all()

    total_expenses_all_time = sum(expense.amount_ron for expense in all_time_expenses)
    total_incomes_all_time = sum(income.amount_ron for income in all_time_incomes)
    total_savings_all_time = sum(saving.amount_ron for saving in all_time_savings)

    return render_template('summary_year.html', current_year=current_year,
                       current_year_data=current_year_data,
                       total_expenses_year_current=total_expenses_year_current,
                       total_incomes_year_current=total_incomes_year_current,
                       total_savings_year_current=total_savings_year_current,
                       total_budget_year_current=total_budget_year_current,
                       last_year_data=last_year_data,
                       total_expenses_year_last=total_expenses_year_last,
                       total_incomes_year_last=total_incomes_year_last,
                       total_savings_year_last=total_savings_year_last,
                       total_budget_year_last=total_budget_year_last,
                       total_expenses_all_time=total_expenses_all_time,
                       total_incomes_all_time=total_incomes_all_time,
                       total_savings_all_time=total_savings_all_time)

@app.route('/data_mining')
@htpasswd.required
def data_mining(user):
    total_incomes = db.session.query(func.sum(Income.amount_ron)).scalar() or 0.0
    total_expenses = db.session.query(func.sum(Expense.amount_ron)).scalar() or 0.0
    total_savings = db.session.query(func.sum(Savings.amount_ron)).scalar() or 0.0
    total_balance = total_incomes - (total_expenses + total_savings)
    current_year = datetime.now().year
    monthly_data = []
    for month in range(1, 13):
        total_expenses_month = Expense.query.filter(
            extract('year', Expense.date) == current_year,
            extract('month', Expense.date) == month
        ).with_entities(func.sum(Expense.amount_ron)).scalar() or 0.0

        total_incomes_month = Income.query.filter(
            extract('year', Income.date) == current_year,
            extract('month', Income.date) == month
        ).with_entities(func.sum(Income.amount_ron)).scalar() or 0.0

        total_savings_month = Savings.query.filter(
            extract('year', Savings.date) == current_year,
            extract('month', Savings.date) == month
        ).with_entities(func.sum(Savings.amount_ron)).scalar() or 0.0

        monthly_data.append({
            "month": month,
            "total_expenses": total_expenses_month,
            "total_incomes": total_incomes_month,
            "total_savings": total_savings_month
        })

    total_expenses_annual = sum(data["total_expenses"] for data in monthly_data)
    total_incomes_annual = sum(data["total_incomes"] for data in monthly_data)
    total_savings_annual = sum(data["total_savings"] for data in monthly_data)
    expense_tag_totals = db.session.query(Tag.name, func.sum(Expense.amount_ron)).join(
        expense_tag, (expense_tag.c.tag_id == Tag.id)
    ).join(
        Expense, (expense_tag.c.expense_id == Expense.id)
    ).filter(
        extract('year', Expense.date) == current_year
    ).group_by(Tag.name).all()
    income_tag_totals = db.session.query(Tag.name, func.sum(Income.amount_ron)).join(
        income_tag, (income_tag.c.tag_id == Tag.id)
    ).join(
        Income, (income_tag.c.income_id == Income.id)
    ).filter(
        extract('year', Income.date) == current_year
    ).group_by(Tag.name).all()
    saving_tag_totals = db.session.query(Tag.name, func.sum(Savings.amount_ron)).join(
        savings_tag, (savings_tag.c.tag_id == Tag.id)
    ).join(
        Savings, (savings_tag.c.savings_id == Savings.id)
    ).filter(
        extract('year', Savings.date) == current_year
    ).group_by(Tag.name).all()

    return render_template('data_mining.html',
                           total_balance=total_balance,
                           monthly_data=monthly_data,
                           total_expenses_annual=total_expenses_annual,
                           total_incomes_annual=total_incomes_annual,
                           total_savings_annual=total_savings_annual,
                           expense_tag_totals=expense_tag_totals,
                           income_tag_totals=income_tag_totals,
                           saving_tag_totals=saving_tag_totals)

@app.route('/get_financial_data')
@htpasswd.required
def get_financial_data(user):
    financial_data = financial_calendar.get_all_financial_data()
    return jsonify(financial_data)

def create_data_dict(data_type, title, amount, date):
    return {
        "type": data_type,
        "title": title,
        "amount_ron": amount,
        "date": date.strftime("%Y-%m-%d")
    }

def query_to_dict(query_result, data_type, title=""):
    return [create_data_dict(data_type, title or item.title, item.amount_ron, item.date) for item in query_result]

@app.route('/export_all_data_csv')
@htpasswd.required
def export_all_data_csv(user):
    try:
        all_expenses = Expense.query.all()
        all_incomes = Income.query.all()
        all_savings = Savings.query.all()
    except Exception as e:
        return str(e), 500
    all_data = (
        query_to_dict(all_expenses, "Expense") +
        query_to_dict(all_incomes, "Income") +
        query_to_dict(all_savings, "Saving", title="Risparmio")
    )
    output = StringIO()
    fieldnames = ["type", "title", "amount_ron", "date"]
    try:
        csv_writer = csv.DictWriter(output, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(all_data)
    except Exception as e:
        return str(e), 500
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=all_data.csv"
    return response

@app.route('/future_expenses', methods=['GET', 'POST'])
@htpasswd.required
def future_expenses(user):
    if request.method == 'POST':
        title = request.form['title']
        amount_ron = request.form['amount_ron']
        date_str = request.form['date']
        tag_id = int(request.form['tag'])
        category = request.form['category']
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            future_expense = FutureExpense(
                title=title,
                amount_ron=amount_ron,
                date=date,
                category=category
            )
            tag = Tag.query.get(tag_id)
            future_expense.tags.append(tag)
            db.session.add(future_expense)
            db.session.commit()
            return redirect(url_for('future_expenses'))
        except ValueError:
            return "Formato data non valido. Utilizzare il formato 'YYYY-MM-DD'."

    future_expenses = FutureExpense.query.all()
    all_tags = Tag.query.all()
    return render_template('future_expenses.html', future_expenses=future_expenses, all_tags=all_tags)

@app.route('/delete_future_expense/<int:expense_id>')
@htpasswd.required
def delete_future_expense(user, expense_id):
    future_expense = FutureExpense.query.get_or_404(expense_id)
    db.session.delete(future_expense)
    db.session.commit()
    return redirect(url_for('future_expenses'))

@app.route('/mark_as_unpaid/<int:expense_id>', methods=['POST'])
@htpasswd.required
def mark_as_unpaid(user, expense_id):
    future_expense = FutureExpense.query.get_or_404(expense_id)
    future_expense.paid = False
    db.session.commit()
    return redirect(url_for('future_expenses'))

@app.route('/mark_as_paid/<int:expense_id>', methods=['POST'])
@htpasswd.required
def mark_as_paid(user, expense_id):
    future_expense = FutureExpense.query.get_or_404(expense_id)
    tag_id = future_expense.tags[0].id
    try:
        category = future_expense.category
        amount_ron = future_expense.amount_ron
        if category == 'spesa':
            new_expense = Expense(
                title=future_expense.title,
                amount_ron=amount_ron, 
                date=future_expense.date,
            )
            for tag in future_expense.tags:
                new_expense.tags.append(tag)
            db.session.add(new_expense)
        elif category == 'introito':
            new_expense = Income(
                title=future_expense.title,
                amount_ron=amount_ron,
                date=future_expense.date,
            )
            for tag in future_expense.tags:
                new_expense.tags.append(tag)
            db.session.add(new_expense)
        elif category == 'risparmio':
            new_expense = Savings(
                amount_ron=amount_ron,
                date=future_expense.date,
                project_id=10000
            )
            for tag in future_expense.tags:
                new_expense.tags.append(tag)
            db.session.add(new_expense)
        db.session.delete(future_expense)
        db.session.commit()
    except ValueError as e:
        return str(e)

    return redirect(url_for('future_expenses'))

def create_savings_project_deadlines(project, months_to_save, start_date, budget_ron):
    monthly_saving = budget_ron / months_to_save
    for i in range(months_to_save):
        deadline_date = start_date + timedelta(days=30 * i)
        deadline_amount = monthly_saving
        deadline = SavingsProjectDeadline(
            date=deadline_date,
            amount_ron=deadline_amount,
            saved=False,
            project=project
        )
        db.session.add(deadline)
        db.session.commit()

@app.route('/savings_projects', methods=['GET', 'POST'])
@htpasswd.required
def savings_projects(user):
    if request.method == 'POST':
        title = request.form['title']
        budget_ron = float(request.form['budget_ron'])
        months_to_save = int(request.form['months_to_save'])
        start_date_str = request.form['start_date']
        category = request.form['category']
        tags_str = request.form['tags']
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            tags_str = request.form['tags']
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            tag_id = request.form['tags']
            tag_object = Tag.query.get(tag_id)
            new_savings_project = SavingsProject(
                title=title,
                budget_ron=budget_ron,
                months_to_save=months_to_save,
                start_date=start_date,
                category=category,
                tags=[tag_object] if tag_object else []
            )
            db.session.add(new_savings_project)
            db.session.commit()
            create_savings_project_deadlines(new_savings_project, months_to_save, start_date, budget_ron)
            return redirect(url_for('savings_projects'))
        except ValueError:
            return "Formato data non valido. Utilizzare il formato 'YYYY-MM-DD'."

    projects = SavingsProject.query.all()
    tags = Tag.query.all()

    return render_template('savings_projects.html', projects=projects, tags=tags)

@app.route('/update_savings_deadline/<int:deadline_id>/<int:saved>', methods=['POST'])
@htpasswd.required
def update_savings_deadline(user, deadline_id, saved):
    deadline = SavingsProjectDeadline.query.get(deadline_id)
    if deadline:
        if saved == 1 and not deadline.saved:
            copy_savings_deadline_to_savings(deadline)
        elif saved == 0 and deadline.saved:
            remove_savings_deadline_from_savings(deadline, deadline.project_id)
        deadline.saved = bool(saved)
        db.session.commit()

    return redirect(url_for('savings_deadlines', project_id=deadline.project_id))

def copy_savings_deadline_to_savings(deadline):
    existing_savings = Savings.query.filter_by(date=deadline.date, amount_ron=deadline.amount_ron, project_id=deadline.project_id).first()
    if not existing_savings:
        new_savings = Savings(
            date=deadline.date,
            amount_ron=deadline.amount_ron,
            project_id=deadline.project_id,
        )
        for tag in deadline.project.tags:
            new_savings.tags.append(tag)
        db.session.add(new_savings)
        db.session.commit()

def remove_savings_deadline_from_savings(deadline, project_id):
    deadline_date_str = deadline.date.strftime('%Y-%m-%d %H:%M:%S.%f')
    matching_savings = Savings.query.filter_by(
        project_id=project_id,
        date=deadline_date_str,
        amount_ron=deadline.amount_ron
    ).first()
    if matching_savings:
        savings_id = matching_savings.id
        try:
            db.session.delete(matching_savings)
            print("Record eliminato da Savings")

            db.session.commit()
            print("Transazione completata")
        except Exception as e:
            print(f"Errore durante la rimozione del record: {str(e)}")
            db.session.rollback()
    else:
        print(f"Nessun record corrispondente trovato per project_id={project_id}, date={deadline.date}, amount_ron={deadline.amount_ron}")

@app.route('/add_savings_project', methods=['POST'])
@htpasswd.required
def add_savings_project(user):
    title = request.form['title']
    budget_ron = float(request.form['budget_ron'])
    months_to_save = int(request.form['months_to_save'])
    start_date_str = request.form['start_date']
    category = request.form['category']
    tags_str = request.form['tags']
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        tag_objects = [Tag.query.filter_by(name=tag).first() for tag in tags]
        new_savings_project = SavingsProject(
            title=title,
            budget_ron=budget_ron,
            months_to_save=months_to_save,
            start_date=start_date,
            category=category,
            tags=tag_objects
        )
        db.session.add(new_savings_project)
        db.session.commit()
        calculated_amount = budget_ron / months_to_save
        for i in range(months_to_save):
            deadline_date = start_date + timedelta(days=30 * i)
            new_deadline = SavingsProjectDeadline(
                date=deadline_date,
                amount_ron=calculated_amount,
                saved=False,
                project=new_savings_project
            )
            db.session.add(new_deadline)
        db.session.commit()
        return redirect(url_for('savings_project', project_id=new_savings_project.id))
    except ValueError:
        return "Formato data non valido. Utilizzare il formato 'YYYY-MM-DD'."

@app.route('/savings_deadlines/<int:project_id>')
@htpasswd.required
def savings_deadlines(user, project_id):
    project = SavingsProject.query.get_or_404(project_id)
    deadlines = project.deadlines  
    savings_list = []
    for deadline in deadlines:
        new_saving = Savings(
            amount_ron=deadline.amount_ron,
            date=deadline.date,
            tags=deadline.project.tags,
        )
        savings_list.append(new_saving)
    
    return render_template('savings_deadlines.html', project=project, deadlines=deadlines, savings_list=savings_list)

@app.route('/forecast')
@htpasswd.required
def forecast(user):
    try:
        # Extract data from the database
        expenses_data = db.session.query(Expense.date, db.func.sum(Expense.amount_ron)).group_by(Expense.date).all()
        incomes_data = db.session.query(Income.date, db.func.sum(Income.amount_ron)).group_by(Income.date).all()
        savings_data = db.session.query(Savings.date, db.func.sum(Savings.amount_ron)).group_by(Savings.date).all()
        # Convert data to DataFrame and resample to monthly format
        expenses_df = pd.DataFrame(expenses_data, columns=["Month", "Expenses"]).set_index("Month").resample('M').sum()
        incomes_df = pd.DataFrame(incomes_data, columns=["Month", "Income"]).set_index("Month").resample('M').sum()
        savings_df = pd.DataFrame(savings_data, columns=["Month", "Savings"]).set_index("Month").resample('M').sum()
        # Merge dataframes, fill NaN values, and get last 12 months
        merged_df = expenses_df.join(incomes_df).join(savings_df).fillna(0).loc[lambda x: x.index >= pd.to_datetime("today") - pd.DateOffset(months=12)]
        # Helper function to perform forecasting
        def get_forecast(df_column, periods=6):
            model = ARIMA(df_column, order=(5,1,0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=periods)
            return forecast
        # Obtain forecasts
        expenses_forecast = get_forecast(merged_df["Expenses"])
        incomes_forecast = get_forecast(merged_df["Income"])
        savings_forecast = get_forecast(merged_df["Savings"])
        # Prepare data for rendering
        historical_data = {
            "Month": merged_df.index.strftime("%Y-%m").tolist(),
            "Expenses": merged_df["Expenses"].tolist(),
            "Income": merged_df["Income"].tolist(),
            "Savings": merged_df["Savings"].tolist(),
        }
        forecast_data = {
            "Month": [(datetime.now() + relativedelta(months=i)).strftime("%Y-%m") for i in range(1, 7)],
            "Expenses": expenses_forecast.round(2).tolist(),
            "Income": incomes_forecast.round(2).tolist(),
            "Savings": savings_forecast.round(2).tolist(),
        }
        return render_template('forecast.html', historical_data=historical_data, forecast_data=forecast_data)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return render_template('404.html', error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
