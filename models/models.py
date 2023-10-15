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

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    amount_ron = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tags = db.relationship('Tag', secondary='expense_tag', back_populates='expenses')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    expenses = db.relationship('Expense', secondary='expense_tag', back_populates='tags')
    incomes = db.relationship('Income', secondary='income_tag', back_populates='tags')
    savings = db.relationship('Savings', secondary='savings_tag', back_populates='tags')
    future_expenses = db.relationship('FutureExpense', secondary='future_expense_tag', back_populates='tags')
    savings_projects = db.relationship('SavingsProject', secondary='savings_project_tag', back_populates='tags')

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    amount_ron = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tags = db.relationship('Tag', secondary='income_tag', back_populates='incomes')

class Savings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount_ron = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tags = db.relationship('Tag', secondary='savings_tag', back_populates='savings')
    project_id = db.Column(db.Integer, db.ForeignKey('savings_project.id'), nullable=False)
    project = db.relationship('SavingsProject', back_populates='savings')
 

expense_tag = db.Table(
    'expense_tag',
    db.Column('expense_id', db.Integer, db.ForeignKey('expense.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

income_tag = db.Table(
    'income_tag',
    db.Column('income_id', db.Integer, db.ForeignKey('income.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

savings_tag = db.Table(
    'savings_tag',
    db.Column('savings_id', db.Integer, db.ForeignKey('savings.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

future_expense_tag = db.Table(
    'future_expense_tag',
    db.Column('future_expense_id', db.Integer, db.ForeignKey('future_expense.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

savings_project_tag = db.Table(
    'savings_project_tag',
    db.Column('savings_project_id', db.Integer, db.ForeignKey('savings_project.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class FinancialCalendar:
    def get_all_financial_data(self):
        financial_data = []
        expenses = Expense.query.all()
        for expense in expenses:
            financial_data.append({
                "title": f"Spesa: {expense.title} - Ammontare: {expense.amount_ron} RON",
                "start": expense.date.strftime("%Y-%m-%d"),
                "end": expense.date.strftime("%Y-%m-%d"),
                "color": "red",
            })
        incomes = Income.query.all()
        for income in incomes:
            financial_data.append({
                "title": f"Introito: {income.title} - Ammontare: {income.amount_ron} RON",
                "start": income.date.strftime("%Y-%m-%d"),
                "end": income.date.strftime("%Y-%m-%d"),
                "color": "green",
            })
        savings = Savings.query.all()
        for saving in savings:
            financial_data.append({
                "title": f"Risparmio - Ammontare: {saving.amount_ron} RON",
                "start": saving.date.strftime("%Y-%m-%d"),
                "end": saving.date.strftime("%Y-%m-%d"),
                "color": "blue",
            })
        return financial_data

class FutureExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    amount_ron = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    category = db.Column(db.String(255))
    paid = db.Column(db.Boolean, default=True)
    tags = db.relationship('Tag', secondary='future_expense_tag', back_populates='future_expenses')

    def __init__(self, title, amount_ron, date, category):
        self.title = title
        self.amount_ron = amount_ron
        self.date = date
        self.category = category

class SavingsProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    budget_ron = db.Column(db.Float, nullable=False)
    months_to_save = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    tags = db.relationship('Tag', secondary='savings_project_tag', back_populates='savings_projects')
    deadlines = db.relationship('SavingsProjectDeadline', back_populates='project', lazy=True)
    savings = db.relationship('Savings', back_populates='project')

    def __init__(self, title, budget_ron, months_to_save, start_date, category, tags):
        self.title = title
        self.budget_ron = budget_ron
        self.months_to_save = months_to_save
        self.start_date = start_date
        self.category = category
        self.tags = tags

class SavingsProjectDeadline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount_ron = db.Column(db.Float, nullable=False)
    saved = db.Column(db.Boolean, default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('savings_project.id'), nullable=False)
    project = db.relationship('SavingsProject', back_populates='deadlines')

    def __init__(self, date, amount_ron, saved, project):
        self.date = date
        self.amount_ron = amount_ron
        self.saved = saved
        self.project = project