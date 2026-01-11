import random
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class BingoGame:
    def __init__(self, game_code: str, entry_price: float, max_players: int = 100):
        self.game_code = game_code
        self.entry_price = entry_price
        self.prize_pool = 0.0
        self.players: Dict[int, Dict] = {}  # user_id -> player data
        self.called_numbers: List[int] = []
        self.status = "waiting"  # waiting, active, finished
        self.winner_id = None
        self.current_number = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.finished_at = None
        self.min_players = 2
        self.max_players = max_players
        
    def generate_cartela(self, cartela_number: int) -> List[int]:
        """Generate a 5x5 BINGO board with FREE center"""
        # Set seed for reproducibility based on cartela number
        seed_value = cartela_number * 12345  # Arbitrary multiplier for uniqueness
        random.seed(seed_value)
        
        # Generate numbers for each column
        columns = {
            'B': sorted(random.sample(range(1, 16), 5)),      # 1-15
            'I': sorted(random.sample(range(16, 31), 5)),     # 16-30
            'N': sorted(random.sample(range(31, 46), 4)),     # 31-45 (4 numbers, center is FREE)
            'G': sorted(random.sample(range(46, 61), 5)),     # 46-60
            'O': sorted(random.sample(range(61, 76), 5))      # 61-75
        }
        
        # Build 5x5 grid
        board = []
        for row in range(5):
            for col_idx, col in enumerate(['B', 'I', 'N', 'G', 'O']):
                if row == 2 and col_idx == 2:  # Center position
                    board.append(0)  # FREE space
                else:
                    # Get the appropriate number from the column
                    if col == 'N' and row > 2:
                        # Adjust index for N column (has only 4 numbers)
                        board.append(columns[col][row-1])
                    else:
                        board.append(columns[col][row])
        
        # Reset random seed
        random.seed()
        return board
    
    def add_player(self, user_id: int, cartela_number: int) -> bool:
        """Add a player to the game"""
        if self.status != "waiting":
            return False
        
        if len(self.players) >= self.max_players:
            return False
        
        # Check if cartela number is already taken
        for player in self.players.values():
            if player['cartela_number'] == cartela_number:
                return False
        
        # Generate cartela
        cartela = self.generate_cartela(cartela_number)
        
        # Add player
        self.players[user_id] = {
            'cartela_number': cartela_number,
            'cartela': cartela,
            'marked': [12],  # Center (index 12) is automatically marked as FREE
            'joined_at': datetime.utcnow()
        }
        
        # Update prize pool
        self.prize_pool += self.entry_price
        
        # Auto-start if we have minimum players
        if len(self.players) >= self.min_players and self.status == "waiting":
            self.start_game()
        
        return True
    
    def start_game(self) -> bool:
        """Start the game"""
        if self.status != "waiting":
            return False
        
        if len(self.players) < self.min_players:
            return False
        
        self.status = "active"
        self.started_at = datetime.utcnow()
        
        # Call first number
        self.call_next_number()
        
        return True
    
    def call_next_number(self) -> Optional[str]:
        """Call the next random number"""
        if self.status != "active":
            return None
        
        # Get available numbers (1-75)
        available = [n for n in range(1, 76) if n not in self.called_numbers]
        
        if not available:
            self.status = "finished"
            return None
        
        # Call random number
        number = random.choice(available)
        self.called_numbers.append(number)
        self.current_number = number
        
        # Format: B-1, I-16, N-31, G-46, O-61
        if 1 <= number <= 15:
            prefix = "B"
        elif 16 <= number <= 30:
            prefix = "I"
        elif 31 <= number <= 45:
            prefix = "N"
        elif 46 <= number <= 60:
            prefix = "G"
        else:  # 61-75
            prefix = "O"
        
        return f"{prefix}-{number}"
    
    def mark_number(self, user_id: int, number: int) -> bool:
        """Mark a number on player's cartela"""
        if user_id not in self.players:
            return False
        
        player = self.players[user_id]
        
        # Check if number is in cartela
        if number not in player['cartela']:
            return False
        
        # Check if number has been called (except FREE space which is 0)
        if number != 0 and number not in self.called_numbers:
            return False
        
        # Get index of number in cartela
        index = player['cartela'].index(number)
        
        # Mark if not already marked
        if index not in player['marked']:
            player['marked'].append(index)
            return True
        
        return False
    
    def check_winner(self, user_id: int) -> bool:
        """Check if player has a winning pattern"""
        if user_id not in self.players:
            return False
        
        player = self.players[user_id]
        marked_set = set(player['marked'])
        
        # Check rows (0-4, 5-9, 10-14, 15-19, 20-24)
        for row in range(5):
            indices = [row * 5 + col for col in range(5)]
            if all(idx in marked_set for idx in indices):
                return True
        
        # Check columns
        for col in range(5):
            indices = [row * 5 + col for row in range(5)]
            if all(idx in marked_set for idx in indices):
                return True
        
        # Check diagonal: top-left to bottom-right
        diagonal1 = [0, 6, 12, 18, 24]
        if all(idx in marked_set for idx in diagonal1):
            return True
        
        # Check diagonal: top-right to bottom-left
        diagonal2 = [4, 8, 12, 16, 20]
        if all(idx in marked_set for idx in diagonal2):
            return True
        
        # Check four corners
        corners = [0, 4, 20, 24]
        if all(idx in marked_set for idx in corners):
            return True
        
        return False
    
    def declare_winner(self, user_id: int) -> bool:
        """Declare a winner and end the game"""
        if user_id not in self.players:
            return False
        
        if not self.check_winner(user_id):
            return False
        
        self.winner_id = user_id
        self.status = "finished"
        self.finished_at = datetime.utcnow()
        
        return True
    
    def get_player_cartela(self, user_id: int) -> Optional[List[int]]:
        """Get player's cartela numbers"""
        if user_id in self.players:
            return self.players[user_id]['cartela']
        return None
    
    def get_player_marked(self, user_id: int) -> List[int]:
        """Get player's marked positions"""
        if user_id in self.players:
            return self.players[user_id]['marked']
        return []