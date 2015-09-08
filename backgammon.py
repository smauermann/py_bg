from board import Board, Dice
from move import Movement, BarMovement, BearOffMovement, NormalMovement,\
Move, MovementFactory
import random

class Player(object):
	""" Class which represents a backgammon player. The Backgammon
		object will repeatedly call getMoveFromPlayer() on this player, asking
		the agent to pick a move. """

	COLOR_CODE = {'white': 0, 'black': 1}

	def __init__(self, color):
		""" Player can be initialized by specifying color:
			E.g.: 'white' or 0; or 'black' and 1, respectively. """
		if type(color) is int:
			self.color = color
			self.identity = next((key for key, val in Player.COLOR_CODE.items() if val == color), None)
		elif type(color) is str:
			color = color.lower()
			self.identity = color
			self.color = Player.COLOR_CODE[color]
		else:
			print "Enter valid player: Either 'white' - 0, or 'black' - 1!"

	@staticmethod
	def chooseMove(backgammon_obj):
		""" Requests the player to pick a move given the current backgammon situation. """
		# get a list of all possible moves
		all_moves = backgammon_obj.getMoves()
		num_moves = len(all_moves)
		print "Current player: ", backgammon_obj.current_player
		print backgammon_obj.dice
		print backgammon_obj.board
		
		pick_move = int(raw_input("Choose from %s different possible moves: " %(num_moves)))
		# for now: pick a random move
		#random_move = random.choice(all_moves)
		return all_moves[pick_move - 1]
		#return random_move

	@staticmethod
	def makeInputVector(backgammon_obj):
		""" Creates a 198-dimensional input vector of the current gammon situation. """
		board_obj = backgammon_obj.getCurrentBoard()
		current_player = backgammon_obj.getCurrentPlayer()
		
		board = board_obj.getBoard()
		colors = board_obj.getColors()
		bar = [board_obj.getWhiteBar(),board_obj.getBlackBar()]
		off = [board_obj.getWhiteOff(),board_obj.getBlackOff()]
		
		# initialize the vector:
		# 4 units per point on board: 0-3 checkers --> 0-3 inputs active.
		units = 4
		# Eg. 2 checkers --> 1, 1, 0, 0; 3 checkers --> 1, 1, 1, 0
		# for n > 4 checkers --> 1, 1, 1, (n - 3)/2 --> 96 units each, total 192
		# two units represent each players bar with n/2 --> 194 items
		# another two units stand for beared off checkers with n/15 --> 196 items
		# the last 2 units encode whose turn it is: white --> 01 or black --> 10
		len_vector = len(board) * units * 2 + len(bar) + len(off) + 2
		vector = [0] * len_vector
		
		# loop over board --> first 96 units each
		for pos in range(len(board)):
			# check color at current position, proceed when color is not -1 (means no checkers)
			if colors[pos] != -1:
				# start of the 4-unit stretch in vector
				# first 96
				start = (pos * units) if colors[pos] == 0 else ((len_vector/2 - 1) + pos * units)
				# get number of checkers at pos
				num = board[pos]
				# set the 4 units according to checker number
				if num < 4:
					for i in range(num):
						vector[start + i] = 1
				elif num >= 4:
					for i in range(units - 1):
						vector[start + i] = 1
					vector[start + units - 1] = (num - 3.0) / 2

			# now encode bar
			# unit 97 (vector[96]) for white and unit 193 (vector[192]) for black 
			white_bar_input = (len_vector / 2) - 3
			black_bar_input = len_vector - 4
			vector[white_bar_input] = 'wBar: %s' %(white_bar_input)#bar[0] / 2.0
			vector[black_bar_input] = 'bBar: %s' %(black_bar_input) #bar[1] / 2.0
			# encode off
			# white: unit 98 (vector[97]) and black: unit 194 (vector[193])
			white_off_input = white_bar_input + 1
			black_off_input = black_bar_input + 1
			vector[white_off_input] = 'wOff: %s' %(white_off_input) #off[0] / 15.0
			vector[black_off_input] = 'bOff: %s' %(black_off_input) #off[1] / 15.0
			# turn indicator
			if current_player == Board.WHITE:
				# last units --> 0, 1
				vector[-2] = 0
				vector[-1] = 1
			elif current_player == Board.BLACK:
				# last units --> 1, 0
				vector[-2] = 1
				vector[-1] = 0

		return vector


class Backgammon(object):
	""" This class wraps all of the backgammon functionality.  Basically, the use model
		for this class is build a new Backgammon with two players, execute backgammon.run(),
		which runs the game, and the call backgammon.reset(), backgammon.run() if you
		want to play again. """

	def __init__(self, player1_obj, player2_obj):
		# the dice
		self.dice = Dice()
		# internal board, which is the state before the current move
		self.board = Board()
		# color of the current player
		self.current_player = None
		# list of players
		# white = 0, black = 1
		self.players = [player1_obj, player2_obj]
		self.reset()
	
	def getDice(self):
		return self.dice

	def getCurrentBoard(self):
		return self.board

	def getCurrentPlayer(self):
		return self.current_player

	def reset(self):
	  	""" Resets this backgammon instance to the initial state, with
			a new board and determines starting player. """
		self.board.resetBoard()
		self.dice.roll()
		# java sets player to black!
		# in my version the player that rolls the higher number starts
		if self.dice.getDie1() != self.dice.getDie2():
			# determine starting player:
	  		# die1 rolls for white and die2 rolls for black
			self.current_player = (0 if self.dice.getDie1() >
									self.dice.getDie2() else 1)
		# make sure that dice dont show same number
		elif self.dice.getDie1() == self.dice.getDie2():
			same = True
			# roll until different
			while same:
				self.dice.roll()
				if self.dice.getDie1() != self.dice.getDie2():
					self.current_player = (0 if self.dice.getDie1() >
											self.dice.getDie2() else 1)
					same = False		
	 	
	def getMoves(self):
		""" Returns a list of all possible moves the player can currently make. """
		return MovementFactory.getAllMoves(self.current_player, self.dice, self.board)

	def run(self):
		""" Runs a game of backgammon, and does not return until the game
			is over. Returns the player who won the game. """
		while not self.board.isGameOver():
			self.getMoveFromPlayer(self.players[0])
			if self.board.isGameOver():
				break

			self.getMoveFromPlayer(self.players[1])
			if self.board.isGameOver():
				break

		# check whether a player has all checkers beared off
		# and return it as winner. 
		if self.board.getWhiteOff() == 15:
			winner = self.players[0]
		else:
			winner = self.players[1]
		return winner

	def getMoveFromPlayer(self, player_obj):
		""" Get's a player's move and makes the move. """
		# call Player's move() and create move from current backgammon situation
		chosen_move = player_obj.chooseMove(self)

		# check if the starting board of the move to be made
		# equals the actual current board situation
		if not chosen_move.getOriginalBoard().equals(self.board):
			print "Error: Current backgammon situation and starting board for the next move are not equal!"
			self.getMoveFromPlayer(player_obj)
		else:
			self.makeMove(chosen_move)

	def makeMove(self, chosen_move):
		""" Performs the provided move. """
		self.board = chosen_move.getCurrentBoard()
		for i in chosen_move.movements:
			print i.toString()
		self.dice.roll()
		self.current_player = Board.getOtherPlayer(self.current_player)


# white_player = Player(0)
# black_player = Player(1)

# bg = Backgammon(white_player, black_player)
# bg.run()
