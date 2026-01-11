from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    balance = db.Column(db.Float, default=0.0)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    referral_code = db.Column(db.String(10), unique=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrer = db.relationship('User', remote_side=[id], backref='referrals')
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    game_participations = db.relationship('GameParticipant', backref='player', lazy=True)

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    game_code = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished, cancelled
    entry_price = db.Column(db.Float, nullable=False)
    prize_pool = db.Column(db.Float, default=0.0)
    called_numbers = db.Column(db.Text, default='[]')  # JSON array of called numbers
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    current_number = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    max_players = db.Column(db.Integer, default=100)
    
    # Relationships
    participants = db.relationship('GameParticipant', backref='game', lazy=True)
    winner = db.relationship('User', backref='won_games', lazy=True)

class GameParticipant(db.Model):
    __tablename__ = 'game_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cartela_number = db.Column(db.Integer, nullable=False)
    cartela_numbers = db.Column(db.Text, nullable=False)  # JSON array of 25 numbers
    marked_numbers = db.Column(db.Text, default='[]')  # JSON array of marked indices
    is_winner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('game_id', 'cartela_number', name='unique_cartela_per_game'),
        db.UniqueConstraint('game_id', 'user_id', name='unique_user_per_game'),
    )

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, game_entry, prize
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    description = db.Column(db.Text)
    payment_method = db.Column(db.String(20))  # cbe, telebirr, manual
    transaction_ref = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )