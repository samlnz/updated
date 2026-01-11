import os
import random
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS

from config import WEB_URL, WEBAPP_URL, CBE_ACCOUNT_NAME, CBE_ACCOUNT_NUMBER, TELEBIRR_NAME, TELEBIRR_NUMBER
from database import db, init_db
from models import User, Game, GameParticipant, Transaction
from game_logic import BingoGame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-12345")
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
CORS(app)

# Initialize database
init_db(app)

# In-memory storage for active games (in production, use Redis)
active_games = {}
player_sessions = {}

@app.route('/')
def index():
    """Home page redirects to lobby"""
    return redirect(url_for('lobby'))

@app.route('/lobby')
def lobby():
    """Game lobby page"""
    game_price = request.args.get('price', 10, type=int)
    user_id = session.get('user_id')
    
    # If no user_id in session, create one
    if not user_id:
        user_id = random.randint(100000, 999999)
        session['user_id'] = user_id
        session.permanent = True
    
    # Get active games from database
    active_db_games = Game.query.filter_by(status='waiting').all()
    
    return render_template('game_lobby.html',
                         web_url=WEB_URL,
                         webapp_url=WEBAPP_URL,
                         game_price=game_price,
                         active_games=active_db_games,
                         user_id=user_id)

@app.route('/game/create', methods=['POST'])
def create_game():
    """Create a new game"""
    try:
        data = request.json
        entry_price = float(data.get('entry_price', 10))
        user_id = data.get('user_id')
        
        if entry_price not in [10, 20, 50, 100]:
            return jsonify({'success': False, 'error': 'Invalid entry price'}), 400
        
        # Generate unique game code
        game_code = f"B{random.randint(1000, 9999)}"
        
        # Create game in database
        game = Game(
            game_code=game_code,
            entry_price=entry_price,
            status='waiting',
            created_at=datetime.utcnow()
        )
        db.session.add(game)
        db.session.commit()
        
        # Create in-memory game instance
        bingo_game = BingoGame(game_code, entry_price)
        active_games[game.id] = bingo_game
        
        logger.info(f"Game created: ID={game.id}, Code={game_code}, Price={entry_price}")
        
        return jsonify({
            'success': True,
            'game_id': game.id,
            'game_code': game_code,
            'entry_price': entry_price
        })
        
    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/game/<int:game_id>/select')
def select_cartela(game_id):
    """Cartela selection page"""
    if game_id not in active_games:
        return "Game not found or has ended", 404
    
    game = active_games[game_id]
    
    # Get used cartela numbers
    used_numbers = []
    for player in game.players.values():
        used_numbers.append(player['cartela_number'])
    
    return render_template('cartela_selection.html',
                         game_id=game_id,
                         game_code=game.game_code,
                         entry_price=game.entry_price,
                         used_numbers=used_numbers,
                         max_cartela=100)

@app.route('/game/<int:game_id>/join', methods=['POST'])
def join_game(game_id):
    """Join a game with selected cartela"""
    try:
        data = request.json
        cartela_number = int(data.get('cartela_number'))
        user_id = session.get('user_id', random.randint(100000, 999999))
        
        if game_id not in active_games:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
        
        game = active_games[game_id]
        
        # Validate cartela number
        if cartela_number < 1 or cartela_number > 100:
            return jsonify({'success': False, 'error': 'Invalid cartela number'}), 400
        
        # Join game
        if game.add_player(user_id, cartela_number):
            # Store user session
            player_sessions[user_id] = game_id
            
            # Save to database
            db_game = Game.query.get(game_id)
            if db_game:
                participant = GameParticipant(
                    game_id=db_game.id,
                    user_id=user_id,
                    cartela_number=cartela_number,
                    cartela_numbers=json.dumps(game.players[user_id]['cartela']),
                    created_at=datetime.utcnow()
                )
                db.session.add(participant)
                db.session.commit()
            
            logger.info(f"Player {user_id} joined game {game_id} with cartela {cartela_number}")
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'cartela_number': cartela_number
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to join game'}), 400
            
    except Exception as e:
        logger.error(f"Error joining game: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/game/<int:game_id>')
def game_page(game_id):
    """Main game page"""
    if game_id not in active_games:
        return redirect(url_for('lobby'))
    
    game = active_games[game_id]
    user_id = session.get('user_id')
    
    if not user_id or user_id not in game.players:
        return redirect(f'/game/{game_id}/select')
    
    player = game.players[user_id]
    
    # Format called numbers for display
    formatted_called = []
    for num in game.called_numbers:
        if 1 <= num <= 15:
            formatted_called.append(f"B-{num}")
        elif 16 <= num <= 30:
            formatted_called.append(f"I-{num}")
        elif 31 <= num <= 45:
            formatted_called.append(f"N-{num}")
        elif 46 <= num <= 60:
            formatted_called.append(f"G-{num}")
        else:
            formatted_called.append(f"O-{num}")
    
    return render_template('game.html',
                         game_id=game_id,
                         game_code=game.game_code,
                         game=game,
                         player=player,
                         called_numbers=formatted_called,
                         current_number=game.current_number,
                         entry_price=game.entry_price,
                         prize_pool=game.prize_pool,
                         player_count=len(game.players))

@app.route('/game/<int:game_id>/call', methods=['POST'])
def call_number(game_id):
    """Call next number in game"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'}), 404
    
    game = active_games[game_id]
    
    if game.status != 'active':
        return jsonify({'success': False, 'error': 'Game is not active'}), 400
    
    number = game.call_next_number()
    
    if number:
        # Update database
        db_game = Game.query.get(game_id)
        if db_game:
            db_game.current_number = number
            db_game.called_numbers = json.dumps(game.called_numbers)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'number': number,
            'called_numbers': game.called_numbers
        })
    else:
        return jsonify({'success': False, 'error': 'No more numbers to call'}), 400

@app.route('/game/<int:game_id>/mark', methods=['POST'])
def mark_number(game_id):
    """Mark a number on player's cartela"""
    try:
        data = request.json
        number = int(data.get('number', 0))
        user_id = session.get('user_id')
        
        if game_id not in active_games:
            return jsonify({'success': False, 'error': 'Game not found'}), 404
        
        if not user_id or user_id not in active_games[game_id].players:
            return jsonify({'success': False, 'error': 'Player not in game'}), 404
        
        game = active_games[game_id]
        
        if game.mark_number(user_id, number):
            # Check for win
            if game.check_winner(user_id):
                game.declare_winner(user_id)
                return jsonify({
                    'success': True,
                    'winner': True,
                    'message': '🎉 BINGO! You won the game!'
                })
            
            return jsonify({
                'success': True,
                'marked': True,
                'marked_numbers': game.players[user_id]['marked']
            })
        else:
            return jsonify({'success': False, 'error': 'Cannot mark this number'}), 400
            
    except Exception as e:
        logger.error(f"Error marking number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/game/<int:game_id>/status')
def game_status(game_id):
    """Get current game status"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': 'Game not found'}), 404
    
    game = active_games[game_id]
    user_id = session.get('user_id')
    
    player_data = None
    if user_id in game.players:
        player_data = {
            'cartela_number': game.players[user_id]['cartela_number'],
            'marked': game.players[user_id]['marked']
        }
    
    return jsonify({
        'success': True,
        'game_code': game.game_code,
        'status': game.status,
        'current_number': game.current_number,
        'called_numbers': game.called_numbers,
        'player_count': len(game.players),
        'prize_pool': game.prize_pool,
        'player': player_data
    })

@app.route('/webhook/deposit', methods=['POST'])
def deposit_webhook():
    """Handle deposit webhook from Macrodroid"""
    try:
        data = request.json
        logger.info(f"Received deposit webhook: {data}")
        
        # Extract data
        amount = float(data.get('amount', 0))
        phone = data.get('phone', '').strip()
        method = data.get('method', 'unknown').lower()
        reference = data.get('reference', '')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid amount'}), 400
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number required'}), 400
        
        # Find user by phone number
        user = User.query.filter_by(phone=phone).first()
        if not user:
            logger.warning(f"No user found with phone: {phone}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Create transaction
        transaction = Transaction(
            user_id=user.id,
            type='deposit',
            amount=amount,
            status='completed',
            description=f'Deposit via {method}',
            payment_method=method,
            transaction_ref=reference,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # Update user balance
        user.balance += amount
        
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Deposit processed: User={user.id}, Amount={amount}, New Balance={user.balance}")
        
        return jsonify({
            'success': True,
            'message': f'Deposit of {amount:.2f} Birr processed successfully',
            'user_id': user.id,
            'username': user.username,
            'new_balance': user.balance,
            'transaction_id': transaction.id
        })
        
    except Exception as e:
        logger.error(f"Error processing deposit webhook: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/webhook/test', methods=['POST', 'GET'])
def test_webhook():
    """Test webhook endpoint"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'message': 'Webhook test endpoint is working',
            'timestamp': datetime.utcnow().isoformat(),
            'url': WEB_URL
        })
    
    # POST request
    data = request.json or {}
    
    return jsonify({
        'success': True,
        'message': 'Webhook test successful',
        'received_data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'deposit': f'{WEB_URL}/webhook/deposit',
            'test': f'{WEB_URL}/webhook/test'
        }
    })

@app.route('/deposit/instructions')
def deposit_instructions():
    """Show deposit instructions"""
    return jsonify({
        'success': True,
        'instructions': {
            'cbe': {
                'name': CBE_ACCOUNT_NAME,
                'account': CBE_ACCOUNT_NUMBER
            },
            'telebirr': {
                'name': TELEBIRR_NAME,
                'account': TELEBIRR_NUMBER
            },
            'webhook_url': f'{WEB_URL}/webhook/deposit',
            'required_fields': ['amount', 'phone', 'method', 'reference']
        }
    })

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Only run locally, not on Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)