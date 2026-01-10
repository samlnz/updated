# File: app/routes.py
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import User, Game, GameParticipant, Transaction
from app.game_logic import BingoGame
from config import WEBAPP_URL, GAME_PRICES, MIN_PLAYERS

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# In-memory game storage
active_games = {}

@bp.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@bp.route('/game.html')
def game_page():
    """Game interface"""
    return render_template('game.html', webapp_url=WEBAPP_URL)

@bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "Addis Bingo",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@bp.route('/api/game/create', methods=['POST'])
def create_game():
    """Create a new game"""
    try:
        data = request.json
        user_id = data.get('user_id')
        entry_price = int(data.get('entry_price', 10))
        
        if entry_price not in GAME_PRICES:
            return jsonify({'error': 'Invalid entry price'}), 400
        
        # Generate game ID
        game_id = len(active_games) + 1
        while game_id in active_games:
            game_id += 1
        
        active_games[game_id] = BingoGame(game_id, entry_price)
        
        # Deduct entry fee from user
        with db.session.begin():
            user = User.query.get(user_id)
            if user.balance < entry_price:
                return jsonify({'error': 'Insufficient balance'}), 400
            
            user.balance -= entry_price
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                type='game_entry',
                amount=-entry_price,
                status='completed',
                completed_at=datetime.utcnow(),
                game_id=game_id
            )
            db.session.add(transaction)
        
        return jsonify({
            'status': 'success',
            'game_id': game_id,
            'entry_price': entry_price,
            'game_url': f"{WEBAPP_URL}/play.html?game_id={game_id}&user_id={user_id}"
        })
        
    except Exception as e:
        logger.exception(f"Error creating game: {str(e)}")
        return jsonify({'error': 'Failed to create game'}), 500

@bp.route('/api/game/<int:game_id>/join', methods=['POST'])
def join_game(game_id):
    """Join an existing game"""
    try:
        if game_id not in active_games:
            return jsonify({'error': 'Game not found'}), 404
        
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        game = active_games[game_id]
        
        # Check if user already in game
        if user_id in game.players:
            return jsonify({
                'status': 'success',
                'message': 'Already in game',
                'cartela': game.players[user_id]['cartela_numbers']
            })
        
        # Check user balance
        with db.session.begin():
            user = User.query.get(user_id)
            if user.balance < game.entry_price:
                return jsonify({'error': 'Insufficient balance'}), 400
            
            # Deduct entry fee
            user.balance -= game.entry_price
            
            # Create transaction
            transaction = Transaction(
                user_id=user.id,
                type='game_entry',
                amount=-game.entry_price,
                status='completed',
                completed_at=datetime.utcnow(),
                game_id=game_id
            )
            db.session.add(transaction)
        
        # Add player to game
        cartela = game.add_player(user_id)
        if not cartela:
            return jsonify({'error': 'Failed to join game'}), 400
        
        # Try to start game if enough players
        if len(game.players) >= MIN_PLAYERS and game.status == "waiting":
            game.start_game()
        
        return jsonify({
            'status': 'success',
            'game_id': game_id,
            'cartela': cartela,
            'cartela_display': game.get_player_cartela_display(user_id),
            'players_count': len(game.players),
            'game_status': game.status
        })
        
    except Exception as e:
        logger.exception(f"Error joining game: {str(e)}")
        return jsonify({'error': 'Failed to join game'}), 500

@bp.route('/api/game/<int:game_id>/status')
def game_status(game_id):
    """Get game status"""
    try:
        if game_id not in active_games:
            # Check database for finished games
            game_db = Game.query.get(game_id)
            if game_db:
                return jsonify({
                    'status': 'success',
                    'game_id': game_id,
                    'game_status': game_db.status,
                    'winner_id': game_db.winner_id,
                    'finished_at': game_db.finished_at.isoformat() if game_db.finished_at else None
                })
            return jsonify({'error': 'Game not found'}), 404
        
        game = active_games[game_id]
        
        # Check for timeout
        if game.check_timeout():
            game.end_game()
        
        return jsonify({
            'status': 'success',
            'game_id': game_id,
            'game_status': game.status,
            'players_count': len(game.players),
            'called_numbers': game.called_numbers,
            'current_number': game.called_numbers[-1] if game.called_numbers else None,
            'winner': game.winner,
            'pool': game.pool
        })
        
    except Exception as e:
        logger.exception(f"Error getting game status: {str(e)}")
        return jsonify({'error': 'Failed to get game status'}), 500

@bp.route('/api/game/<int:game_id>/call', methods=['POST'])
def call_number(game_id):
    """Call the next number"""
    try:
        if game_id not in active_games:
            return jsonify({'error': 'Game not found'}), 404
        
        game = active_games[game_id]
        
        if game.status != "active":
            return jsonify({'error': 'Game not active'}), 400
        
        number = game.call_number()
        if not number:
            return jsonify({'error': 'No more numbers to call'}), 400
        
        return jsonify({
            'status': 'success',
            'number': game.format_number(number),
            'raw_number': number,
            'called_numbers': game.called_numbers,
            'remaining_numbers': len(game.available_numbers)
        })
        
    except Exception as e:
        logger.exception(f"Error calling number: {str(e)}")
        return jsonify({'error': 'Failed to call number'}), 500

@bp.route('/api/game/<int:game_id>/mark', methods=['POST'])
def mark_number(game_id):
    """Mark a number on player's cartela"""
    try:
        if game_id not in active_games:
            return jsonify({'error': 'Game not found'}), 404
        
        data = request.json
        user_id = data.get('user_id')
        number = data.get('number')
        
        if not user_id or not number:
            return jsonify({'error': 'User ID and number required'}), 400
        
        game = active_games[game_id]
        
        if user_id not in game.players:
            return jsonify({'error': 'Player not in game'}), 400
        
        # Mark the number
        success = game.mark_number(user_id, number)
        if not success:
            return jsonify({'error': 'Number not found on cartela'}), 400
        
        # Check for win
        winner, message = game.check_winner(user_id)
        
        response_data = {
            'status': 'success',
            'marked': True,
            'winner': winner,
            'message': message
        }
        
        if winner:
            game.end_game(user_id)
            response_data['game_status'] = 'finished'
            
            # Record win in database
            with db.session.begin():
                user = User.query.get(int(user_id))
                if user:
                    user.games_won += 1
                    user.games_played += 1
                    user.balance += game.pool
                    
                    # Create win transaction
                    transaction = Transaction(
                        user_id=user.id,
                        type='win',
                        amount=game.pool,
                        status='completed',
                        completed_at=datetime.utcnow(),
                        game_id=game_id
                    )
                    db.session.add(transaction)
                    
                    # Save game to database
                    game_db = Game(
                        id=game_id,
                        status='finished',
                        entry_price=game.entry_price,
                        pool=game.pool,
                        called_numbers=json.dumps(game.called_numbers),
                        winner_id=user.id,
                        created_at=game.created_at,
                        finished_at=datetime.utcnow()
                    )
                    db.session.add(game_db)
                    
                    # Save participants
                    for player_id, player_data in game.players.items():
                        participant = GameParticipant(
                            game_id=game_id,
                            user_id=int(player_id),
                            cartela_number=player_data['cartela_number'],
                            cartela_numbers=json.dumps(player_data['cartela_numbers']),
                            marked_numbers=json.dumps([i for i, marked in enumerate(player_data['marked']) if marked])
                        )
                        db.session.add(participant)
            
            # Remove from active games
            if game_id in active_games:
                del active_games[game_id]
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception(f"Error marking number: {str(e)}")
        return jsonify({'error': 'Failed to mark number'}), 500

@bp.route('/webhook/deposit', methods=['POST'])
def deposit_webhook():
    """Handle deposit webhook"""
    try:
        data = request.get_json()
        logger.info(f"Received deposit webhook: {data}")

        if not data or 'amount' not in data or 'phone' not in data:
            error_msg = 'Invalid webhook data - must include amount and phone'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400

        # Find user by phone number
        user = User.query.filter_by(phone=data['phone']).first()
        if not user:
            return jsonify({'error': f'No user found with phone: {data["phone"]}'}), 404

        # Find pending transaction
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='deposit',
            status='pending',
            amount=amount
        ).order_by(Transaction.created_at.desc()).first()

        if transaction:
            # Approve the deposit
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            transaction.transaction_id = data.get('transaction_id', 'manual')

            # Update user balance
            user.balance += amount
            user.total_deposits += amount
            
            # Check if first deposit and add referral bonus
            if user.total_deposits == amount and user.referrer_id:
                referrer = User.query.get(user.referrer_id)
                if referrer:
                    from config import REFERRAL_BONUS
                    referrer.balance += REFERRAL_BONUS
                    
                    # Create referral bonus transaction
                    ref_transaction = Transaction(
                        user_id=referrer.id,
                        type='referral',
                        amount=REFERRAL_BONUS,
                        status='completed',
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(ref_transaction)
            
            db.session.commit()

            logger.info(f"Deposit approved for user {user.id}: {amount} birr")
            
            return jsonify({
                'status': 'success',
                'message': f'Deposit of {amount} birr processed successfully',
                'new_balance': user.balance
            })
        else:
            return jsonify({'error': 'No pending deposit found'}), 404

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error processing webhook: {error_msg}")
        db.session.rollback()
        return jsonify({'error': error_msg}), 500

@bp.route('/api/user/<int:user_id>/balance')
def user_balance(user_id):
    """Get user balance"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'balance': user.balance,
            'username': user.username,
            'phone': user.phone
        })
        
    except Exception as e:
        logger.exception(f"Error getting user balance: {str(e)}")
        return jsonify({'error': 'Failed to get user balance'}), 500

@bp.route('/api/user/<int:user_id>/transactions')
def user_transactions(user_id):
    """Get user transaction history"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transactions = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.created_at.desc())\
            .limit(20)\
            .all()
        
        return jsonify({
            'status': 'success',
            'transactions': [{
                'id': t.id,
                'type': t.type,
                'amount': t.amount,
                'status': t.status,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None
            } for t in transactions]
        })
        
    except Exception as e:
        logger.exception(f"Error getting user transactions: {str(e)}")
        return jsonify({'error': 'Failed to get transactions'}), 500