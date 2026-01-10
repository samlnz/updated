# File: app/models.py
from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    balance = db.Column(db.Float, default=0.0)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    total_deposits = db.Column(db.Float, default=0.0)
    total_withdrawals = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(20), unique=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]))
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    games = db.relationship('GameParticipant', backref='player', lazy=True)
    
    def __repr__(self):
        return f"<User {self.telegram_id}>"

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='waiting')
    entry_price = db.Column(db.Float, nullable=False)
    pool = db.Column(db.Float, default=0.0)
    called_numbers = db.Column(db.Text, default='')
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    current_number = db.Column(db.Integer, nullable=True)
    max_players = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    participants = db.relationship('GameParticipant', backref='game', lazy=True, cascade="all, delete-orphan")
    winner = db.relationship('User', backref='won_games', lazy=True, foreign_keys=[winner_id])

class GameParticipant(db.Model):
    __tablename__ = 'game_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cartela_number = db.Column(db.Integer, nullable=False)
    cartela_numbers = db.Column(db.Text, nullable=False)
    marked_numbers = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('game_id', 'cartela_number', name='unique_cartela_per_game'),
        db.UniqueConstraint('game_id', 'user_id', name='unique_player_per_game'),
    )
    
    def __repr__(self):
        return f"<Participant {self.user_id} in Game {self.game_id}>"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # For deposits
    deposit_phone = db.Column(db.String(20), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    sms_text = db.Column(db.Text, nullable=True)
    
    # For withdrawals
    withdrawal_phone = db.Column(db.String(20), nullable=True)
    withdrawal_status = db.Column(db.String(20), nullable=True)
    admin_note = db.Column(db.Text, nullable=True)
    
    # For game entries
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    
    def __repr__(self):
        return f"<Transaction {self.type} {self.amount}>"