from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
import os

from config import ADMIN_USERNAME, ADMIN_PASSWORD, SECRET_KEY
from database import db
from models import User, Game, Transaction

app = Flask(__name__, template_folder='templates/admin')
app.secret_key = SECRET_KEY

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/admin/dashboard')
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_games = Game.query.count()
    active_games = Game.query.filter_by(status='active').count()
    
    # Calculate total deposits
    total_deposits = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'deposit',
        Transaction.status == 'completed'
    ).scalar() or 0
    
    # Calculate total withdrawals
    total_withdrawals = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'withdrawal',
        Transaction.status == 'completed'
    ).scalar() or 0
    
    # Get pending withdrawals
    pending_withdrawals = Transaction.query.filter_by(
        type='withdrawal',
        status='pending'
    ).order_by(Transaction.created_at.desc()).all()
    
    # Get recent games
    recent_games = Game.query.order_by(Game.created_at.desc()).limit(10).all()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_users=total_users,
                         total_games=total_games,
                         active_games=active_games,
                         total_deposits=total_deposits,
                         total_withdrawals=abs(total_withdrawals),
                         pending_withdrawals=pending_withdrawals,
                         recent_games=recent_games,
                         recent_users=recent_users)

@app.route('/admin/users')
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=all_users)

@app.route('/admin/transactions')
@admin_required
def transactions():
    all_transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return render_template('transactions.html', transactions=all_transactions)

@app.route('/admin/games')
@admin_required
def games():
    all_games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('games.html', games=all_games)

@app.route('/admin/withdrawal/<int:tx_id>/approve', methods=['POST'])
@admin_required
def approve_withdrawal(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    user = User.query.get(transaction.user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('dashboard'))
    
    amount = abs(transaction.amount)
    
    if amount > user.balance:
        flash('Insufficient balance', 'danger')
        return redirect(url_for('dashboard'))
    
    # Update transaction status
    transaction.status = 'completed'
    transaction.completed_at = datetime.utcnow()
    transaction.admin_notes = f'Approved by admin on {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}'
    
    # Deduct from user balance
    user.balance -= amount
    
    db.session.commit()
    
    flash(f'Withdrawal of {amount:.2f} Birr approved for {user.username}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/withdrawal/<int:tx_id>/reject', methods=['POST'])
@admin_required
def reject_withdrawal(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    
    transaction.status = 'cancelled'
    transaction.admin_notes = f'Rejected by admin on {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}'
    
    db.session.commit()
    
    flash('Withdrawal request rejected', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/user/<int:user_id>/adjust', methods=['POST'])
@admin_required
def adjust_user_balance(user_id):
    user = User.query.get_or_404(user_id)
    adjustment = float(request.form.get('adjustment', 0))
    reason = request.form.get('reason', '')
    
    if adjustment == 0:
        flash('No adjustment made', 'warning')
        return redirect(url_for('users'))
    
    # Create adjustment transaction
    transaction = Transaction(
        user_id=user.id,
        type='adjustment',
        amount=adjustment,
        status='completed',
        description=f'Admin adjustment: {reason}',
        admin_notes=f'Adjusted by admin on {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}',
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    # Update user balance
    user.balance += adjustment
    
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Adjusted {user.username}\'s balance by {adjustment:.2f} Birr', 'success')
    return redirect(url_for('users'))

@app.route('/admin/logout')
@admin_required
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)