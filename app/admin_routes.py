# File: app/admin_routes.py
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, Game, Transaction
from config import ADMIN_USERNAME, ADMIN_PASSWORD

bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

@bp.context_processor
def inject_now():
    return {'now': datetime.now()}

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
            
    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

@bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_games = Game.query.count()
    active_games = Game.query.filter_by(status='active').count()
    total_transactions = Transaction.query.count()
    
    # Calculate total deposits and withdrawals
    total_deposits = db.session.query(db.func.sum(Transaction.amount))\
        .filter(Transaction.type == 'deposit', Transaction.status == 'completed')\
        .scalar() or 0
    
    total_withdrawals = db.session.query(db.func.sum(db.func.abs(Transaction.amount)))\
        .filter(Transaction.type == 'withdraw', Transaction.status == 'completed')\
        .scalar() or 0
    
    pending_withdrawals = Transaction.query.filter_by(type='withdraw', status='pending').count()
    
    recent_transactions = Transaction.query\
        .order_by(Transaction.created_at.desc())\
        .limit(10)\
        .all()
    
    recent_users = User.query\
        .order_by(User.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_games=total_games,
                         active_games=active_games,
                         total_transactions=total_transactions,
                         total_deposits=total_deposits,
                         total_withdrawals=total_withdrawals,
                         pending_withdrawals=pending_withdrawals,
                         recent_transactions=recent_transactions,
                         recent_users=recent_users)

@bp.route('/users')
@admin_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@bp.route('/transactions')
@admin_required
def transactions_list():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return render_template('admin/transactions.html', transactions=transactions)

@bp.route('/withdrawals')
@admin_required
def withdrawals_list():
    withdrawals = Transaction.query\
        .filter_by(type='withdraw')\
        .order_by(Transaction.created_at.desc())\
        .all()
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@bp.route('/withdrawal/approve/<int:transaction_id>', methods=['POST'])
@admin_required
def approve_withdrawal(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.type != 'withdraw' or transaction.status != 'pending':
        flash('Invalid transaction', 'error')
        return redirect(url_for('admin.withdrawals_list'))
    
    user = User.query.get(transaction.user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.withdrawals_list'))
    
    # Check if user has sufficient balance
    if user.balance < abs(transaction.amount):
        flash('Insufficient balance', 'error')
        return redirect(url_for('admin.withdrawals_list'))
    
    try:
        # Process withdrawal
        user.balance -= abs(transaction.amount)
        user.total_withdrawals += abs(transaction.amount)
        
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        transaction.withdrawal_status = 'approved'
        
        db.session.commit()
        
        flash('Withdrawal approved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving withdrawal: {e}")
        flash('Error approving withdrawal', 'error')
    
    return redirect(url_for('admin.withdrawals_list'))

@bp.route('/withdrawal/reject/<int:transaction_id>', methods=['POST'])
@admin_required
def reject_withdrawal(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.type != 'withdraw' or transaction.status != 'pending':
        flash('Invalid transaction', 'error')
        return redirect(url_for('admin.withdrawals_list'))
    
    try:
        transaction.status = 'failed'
        transaction.withdrawal_status = 'rejected'
        transaction.admin_note = request.form.get('reason', 'Rejected by admin')
        
        db.session.commit()
        
        flash('Withdrawal rejected', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting withdrawal: {e}")
        flash('Error rejecting withdrawal', 'error')
    
    return redirect(url_for('admin.withdrawals_list'))

@bp.route('/games')
@admin_required
def games_list():
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('admin/games.html', games=games)

@bp.route('/user/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    transactions = Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.created_at.desc())\
        .limit(20)\
        .all()
    return render_template('admin/user_detail.html', user=user, transactions=transactions)