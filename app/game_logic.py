# File: app/game_logic.py
import random
import json
from datetime import datetime, timedelta
from config import GAME_TIMEOUT, SELECTION_TIME

class BingoGame:
    def __init__(self, game_id, entry_price, max_players=10):
        self.game_id = game_id
        self.entry_price = entry_price
        self.status = "waiting"
        self.players = {}
        self.called_numbers = []
        self.all_numbers = list(range(1, 76))
        self.available_numbers = self.all_numbers.copy()
        self.winner = None
        self.pool = 0
        self.min_players = 2
        self.max_players = max_players
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
    def add_player(self, user_id, cartela_number=None):
        """Add a player to the game"""
        if user_id in self.players:
            return self.players[user_id]['cartela_numbers']
        
        if len(self.players) >= self.max_players:
            return None
        
        # Generate cartela number if not provided
        if cartela_number is None:
            used_numbers = {p.get('cartela_number') for p in self.players.values()}
            cartela_number = 1
            while cartela_number in used_numbers:
                cartela_number += 1
        
        # Generate cartela (5x5 bingo card)
        cartela_numbers = self.generate_cartela()
        
        self.players[user_id] = {
            'cartela_numbers': cartela_numbers,
            'marked': [False] * 25,
            'cartela_number': cartela_number,
            'joined_at': datetime.utcnow()
        }
        
        # Mark center as free
        self.players[user_id]['marked'][12] = True
        self.pool += self.entry_price
        self.last_activity = datetime.utcnow()
        
        return cartela_numbers
    
    def generate_cartela(self):
        """Generate a random Bingo cartela (5x5 grid)"""
        cartela = []
        
        # Bingo columns: B(1-15), I(16-30), N(31-45), G(46-60), O(61-75)
        ranges = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75)]
        
        for col in range(5):
            start, end = ranges[col]
            numbers = random.sample(range(start, end + 1), 5)
            cartela.extend(numbers)
        
        # Set center as FREE (0 represents FREE)
        cartela[12] = 0
        
        return cartela
    
    def start_game(self):
        """Start the game if enough players have joined"""
        if len(self.players) >= self.min_players and self.status == "waiting":
            self.status = "active"
            self.last_activity = datetime.utcnow()
            return True
        return False
    
    def call_number(self):
        """Call a random number that hasn't been called yet"""
        if not self.available_numbers or self.status != "active":
            return None
        
        number = random.choice(self.available_numbers)
        self.available_numbers.remove(number)
        self.called_numbers.append(number)
        self.last_activity = datetime.utcnow()
        
        return number
    
    def mark_number(self, user_id, number):
        """Mark a number on a player's cartela"""
        if user_id not in self.players or self.status != "active":
            return False
        
        player = self.players[user_id]
        
        # Check if number is on the cartela
        try:
            index = player['cartela_numbers'].index(number)
            player['marked'][index] = True
            self.last_activity = datetime.utcnow()
            return True
        except ValueError:
            return False
    
    def check_winner(self, user_id):
        """Check if a player has won"""
        if user_id not in self.players:
            return False, "Player not found"
        
        player = self.players[user_id]
        marked = player['marked']
        
        # Check rows
        for row in range(5):
            if all(marked[row*5 + col] for col in range(5)):
                return True, "Bingo! Row complete!"
        
        # Check columns
        for col in range(5):
            if all(marked[row*5 + col] for row in range(5)):
                return True, "Bingo! Column complete!"
        
        # Check diagonals
        if all(marked[i*5 + i] for i in range(5)):  # Top-left to bottom-right
            return True, "Bingo! Diagonal complete!"
        
        if all(marked[i*5 + (4-i)] for i in range(5)):  # Top-right to bottom-left
            return True, "Bingo! Diagonal complete!"
        
        return False, "No win yet"
    
    def check_timeout(self):
        """Check if the game has timed out"""
        if self.status == "waiting":
            timeout = timedelta(seconds=GAME_TIMEOUT)
        else:
            timeout = timedelta(seconds=SELECTION_TIME * 2)
        
        return datetime.utcnow() - self.last_activity > timeout
    
    def end_game(self, winner_id=None):
        """End the game"""
        self.status = "finished"
        self.winner = winner_id
        self.last_activity = datetime.utcnow()
        return True
    
    def format_number(self, number):
        """Format number with BINGO letter"""
        if number <= 15:
            return f"B{number}"
        elif number <= 30:
            return f"I{number}"
        elif number <= 45:
            return f"N{number}"
        elif number <= 60:
            return f"G{number}"
        else:
            return f"O{number}"
    
    def get_player_cartela_display(self, user_id):
        """Get formatted cartela display for a player"""
        if user_id not in self.players:
            return None
        
        player = self.players[user_id]
        cartela = player['cartela_numbers']
        marked = player['marked']
        
        display = []
        for i in range(5):  # 5 rows
            row = []
            for j in range(5):  # 5 columns
                idx = i * 5 + j
                num = cartela[idx]
                if num == 0:
                    row.append("FREE")
                elif marked[idx]:
                    row.append(f"[{self.format_number(num)}]")
                else:
                    row.append(self.format_number(num))
            display.append(" ".join(row))
        
        return "\n".join(display)