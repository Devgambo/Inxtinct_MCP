from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import os
import uvicorn
from typing import List, Optional

app = FastAPI(title="Expense Tracker Server")

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

class Expense(BaseModel):
    date: str
    amount: float
    category: str
    subcategory: str = ""
    note: str = ""

class ExpenseResponse(BaseModel):
    status: str
    id: int

class ExpenseItem(BaseModel):
    id: int
    date: str
    amount: float
    category: str
    subcategory: str
    note: str

class SummaryItem(BaseModel):
    category: str
    total_amount: float

@app.post("/expenses", response_model=ExpenseResponse)
def add_expense(expense: Expense):
    '''Add a new expense entry to the database.'''
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (expense.date, expense.amount, expense.category, expense.subcategory, expense.note)
            )
            return {"status": "ok", "id": cur.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses", response_model=List[ExpenseItem])
def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range.'''
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/summary", response_model=List[SummaryItem])
def summarize(start_date: str, end_date: str, category: Optional[str] = None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        with sqlite3.connect(DB_PATH) as c:
            query = (
                """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
                """
            )
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cur = c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    try:
        if os.path.exists(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read() # Returns raw JSON string as per original resource logic, or we could parse it.
        return "[]"
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
