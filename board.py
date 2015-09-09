from random import randint
import copy
from bgexceptions import BackgammonException, IllegalMoveException

class Dice(object):
	""" Roll da dice! """	
	
	# min and max dice values
	MIN_VALUE = 1
	MAX_VALUE = 6
	NUM_DICE = 2
	
	def __init__(self):
		self.dice = [None, None]
		#self.roll(die1, die2)

	def roll(self, die1=None, die2=None):
		""" Roll the dice. """
		# returns tuple of random numbers with 0 <= number < MAX_VALUE
		if die1 is None and die2 is None:
			self.dice = [randint(Dice.MIN_VALUE, Dice.MAX_VALUE),
								randint(Dice.MIN_VALUE, Dice.MAX_VALUE)]
			return self.dice
		else:
			self.dice[0] = die1
			self.dice[1] = die2
			return self.dice

	def getDie1(self):
		return self.dice[0]

	def getDie2(self):
		return self.dice[1]

	def isDoubles(self):
		""" Returns whether dice are doubles or not. """
		return self.dice[0] == self.dice[1]

	def __str__(self):
		print self.dice[0], self.dice[1],
		return ""


class Board(object):
	""" Methods to generate Board representation. """
	# class variables shared by all instances of Board()
	# board size and color assignments
	NUM_POINTS = 24
	WHITE = 0
	BLACK = 1
	NEITHER = -1
	
	# initial config of checkers on the board
	INITIAL_LOCATIONS = [0, 5, 7, 11, 12, 16, 18, 23]
	INITIAL_NUMOFCHECKERS = [2, 5, 3, 5, 5, 3, 5, 2]
	INITIAL_COLORS = [WHITE, BLACK, BLACK, WHITE, BLACK, WHITE, WHITE, BLACK]
	
	# "Constructor" for instance variables unique
	# to each instance like x = Board()
	def __init__(self, board_obj=None):
		# provides the ability to clone a specific board, by passing
		# it to __init__
		if board_obj is None:
			self.board = [0] * Board.NUM_POINTS
			self.colors = [Board.NEITHER] * Board.NUM_POINTS
			self.bar = [0] * 2
			self.off = [0] * 2
			self.resetBoard()
		else:
			self.board = board_obj.board
			self.colors = board_obj.colors
			self.bar = board_obj.bar
			self.off = board_obj.off
		
	def resetBoard(self):
		""" Resets checkers on the board to the initial configuration. """
		for i in range(len(Board.INITIAL_LOCATIONS)):
			self.board[Board.INITIAL_LOCATIONS[i]] = Board.INITIAL_NUMOFCHECKERS[i]
			self.colors[Board.INITIAL_LOCATIONS[i]] = Board.INITIAL_COLORS[i]

		self.bar = [0] * 2
		self.off = [0] * 2

	def getScratch(self):
		""" Return a deep copy of the current board,
			which can be changed without affecting the actual board itself. """
		return copy.deepcopy(self)

	def getWinner(self):
		""" Returns winner of the game if it is over. """
		# logic test if checkers on bar
		# return True if so, False if not
		black_win = (True if self.bar[self.BLACK] > 0 else False)
		white_win = (True if self.bar[self.WHITE] > 0 else False)

		# logic test if player has checkers on bar OR on board
		# no checkers on bar and board result in False for the color
		for i in range(Board.NUM_POINTS):
			black_win = black_win or (self.colors[i] == self.BLACK)
			white_win = white_win or (self.colors[i] == self.WHITE)

		# players with no checkers on bar and on board give False
		# False means winner and is reversed in the following if loop
		# in order to return the winner alias the color_code
		if not black_win:
			return Board.BLACK
		elif not white_win:
			return Board.WHITE
		else:
			return Board.NEITHER

	def isGameOver(self):
		""" Returns whether or not the game is over. """
		black_win = (True if self.bar[Board.BLACK] > 0 else False)
		white_win = (True if self.bar[Board.WHITE] > 0 else False)

		# loop over the board and check if still checkers are on it
		for i in range(Board.NUM_POINTS):
			black_win = black_win or (self.colors[i] == Board.BLACK)
			white_win = white_win or (self.colors[i] == Board.WHITE)

		# when a player has still checkers on the board or bar return true
		# both players yes: gameover = False
		# one player no checkers: gameover = True
		return not (black_win and white_win)

	def getBoard(self):
		return self.board

	def getColors(self):
		return self.colors
	
	def getColor(self, location):
		""" Return the color of a checker at a given location. """
		return self.colors[location]

	def getBlackCheckers(self, location):
		""" Returns the number of black checkers at a given location.
			If there are white pieces return 0. """
		if self.colors[location] == Board.BLACK: 
			self.getCheckers(location)
		else:
			return 0

	def getWhiteCheckers(self, location):
		""" Returns the number of white checkers at a given location.
			If there are black pieces return 0. """
		if self.colors[location] == Board.WHITE: 
			self.getCheckers(location)
		else:
			return 0

	def getCheckers(self, location, color=None):
		""" Returns the number of checkers at a given location.
			By passing a color, the method checks for it at location. """
		#print location
		if color is not None:
			if self.colors[location] == color:
				return self.board[location]
		else:
			return self.board[location]
		return 0

	def getBar(self, color):
		""" Returns the number of checkers of a given color on the bar."""
		return self.bar[color]

	def getBlackBar(self):
		""" Returns the number of black checkers on the bar."""
		return self.getBar(Board.BLACK)

	def getWhiteBar(self):
		""" Returns the number of black checkers on the bar."""
		return self.getBar(Board.WHITE)

	def getOff(self, color):
		""" Returns the number of checkers of the given color beared off. """
		return self.off[color]

	def getBlackOff(self):
		""" Returns the number of black checkers beared off. """
		return self.getOff(Board.BLACK)

	def getWhiteOff(self):
		""" Returns the number of white checkers beared off. """
		return self.getOff(Board.WHITE)

	def getPipCount(self, color):
		""" Calculates pip count for a given player. Pip count is the total
			number of points a player has to move its checkers in order to
			bear all of them off. """
		base = self.getHome(color)
		result = 0

		for i in range(Board.NUM_POINTS):
			if self.colors[i] == color:
				# get checkers of given color at i and multiply by distance
				# to home end point
				result += self.getCheckers(i) * abs(base - i)

		# add number of moves needed to clear the bar
		result += Board.NUM_POINTS * self.getBar(color)
		return result

	def getBlackPips(self):
		""" Returns pips for all black checkers. """
		return self.getPipCount(Board.BLACK)

	def getWhitePips(self):
		""" Returns pips for all white checkers. """
		return self.getPipCount(Board.WHITE)

	def moveToLocation(self, color, location):
		""" Moves a checker of given color to the given location. """
		other_color = self.getOtherPlayer(color)

		if self.colors[location] == other_color:
			# here I need to figure out how to raise an user-defined error
			# use class illegalMoveException(some Error class to inherit)
			raise IllegalMoveException("Unexpected error - position already occupied by other Player!")

		self.board[location] += 1

		# change color at position after move
		if self.board[location] == 1:
			self.colors[location] = color

	def removeFromLocation(self, color, location):
		""" Removes a checker of given color from the given location. """
		if self.colors[location] != color:
			raise IllegalMoveException("Unexpected error - no checkers to remove from position!")
		
		self.board[location] -= 1

		if self.board[location] == 0:
			self.colors[location] = Board.NEITHER

	def moveToBar(self, color):
		""" Moves checker of given color to the bar. """
		self.bar[color] += 1

	def removeFromBar(self, color):
		""" Removes checker of given color from the bar. """
		if self.bar[color] == 0:
			# here I need to figure out how to raise an user-defined error
			# use class RuntimeError(some Error class to inherit)
			raise IllegalMoveException("Unexpected error - no checkers on bar!")
		
		self.bar[color] -= 1

	def moveOff(self, color):
		""" Moves checker of given color off of the board. """
		self.off[color] += 1

	@staticmethod
	def isEqual(a, b):
		""" Utility function to detect equality. """
		for i in range(len(a)):
			if a[i] != b[i]:
				return False
		return True	
	
	# termed getBase in Java implementation
	@staticmethod
	def getHome(color): 
		""" Returns the home location for a given color.
			Ergo the goal location of a color. """
		return (24 if color == Board.WHITE else -1)

	@staticmethod
	def getDirection(color):
		""" Return direction of given color, either 1 (white) or -1 (black). """
		return (1 if color == Board.WHITE else -1)

	@staticmethod
	def getOtherPlayer(color):
		""" Returns color of the opponent. """
		return (Board.WHITE if color == Board.BLACK else Board.BLACK)

	@staticmethod
	def onBoard(location):
		""" Returns whether given location is on the board. """
		return ((location >= 0) and (location < Board.NUM_POINTS))
		
	@staticmethod
	def isBetween(location, lower, upper):
		""" Method to check whether given position is between two given points. """
		return ((location >= lower and location <= upper) or
				(location <= lower and location >= upper))

	@staticmethod
	def inHomeBoard(color, location):
		""" Method to check whether the point is in the given color's home board. """
		return (Board.isBetween(location, Board.getHome(color),
				Board.getHome(color) - (6 * Board.getDirection(color))))

	def __str__(self):
		print "black off:", self.off[1]
		for i in range(Board.NUM_POINTS):
			print "Pos: %s, %s %s" %(i + 1, self.board[i], ("white" if self.colors[i] == 0 else "black" if self.colors[i] == 1 else "-----"))
			if i == 11:
				print "Bar: %s white, %s black" % (self.bar[0], self.bar[1])
		print "white off:", self.off[0]
		
		return " "

	def __eq__(self, other):
		""" Compare this board with provided other board object. """
		if isinstance(other, Board): 
			return (Board.isEqual(self.board, other.board) and
					Board.isEqual(self.colors, other.colors) and
					Board.isEqual(self.bar, other.bar) and
					Board.isEqual(self.off, other.off))
		else:
			return False

	def __ne__(self, other):
		""" Returns True when objects are not equal. """
		return not self.__eq__(other)

	def __hash__(self):
		""" Returns hash value of the current board. """
		base = 19283
		base = Board.javaTempHash(base, self.off)
		base = Board.javaTempHash(base, self.bar)
		base = Board.javaTempHash(base, self.board)
		base = Board.javaTempHash(base, self.colors)
		return base

	# following funcions are different versions for hashing
	# the attributes of board
	@staticmethod
	def javaTempHash(base, a_list):
		""" Hash function from the Java Template. """
		for i in range(len(a_list)):
			if a_list[i] == 0:
				base = base * 273891
			else:
				base = (base + a_list[i]) ^ (a_list[i] + 55)
		return base

	@staticmethod
	def djbhash(a_list): 
		""" Hash function from D J Bernstein. """ 
		h = 5381L 
		for i in a_list: 
			t = (h * 33) & 0xffffffffL 
			h = t ^ i 
		return h 

	@staticmethod
	def fnvhash(a_list): 
		""" Fowler, Noll, Vo Hash function. """ 
		h = 2166136261 
		for i in a_list: 
			t = (h * 16777619) & 0xffffffffL 
			h = t ^ i 
		return h 

b = Board()
b.resetBoard()

print b.__hash__()
# java function definition:
#	access - eg. public
#	return type - eg int
#	name
#	(args) - args passed to function
# eg. public void functionName(args1, args2)

# not sure what they do, and whether we need it:
	# /**
	#   * Public equals
	#   *
	#   * @param other To compare to
	#   * @return equality
	#   */
	#  public boolean equals(Object o) {
	#    Board board = (Board) o;
	    
	#    return (isEqual(this.board, board.board) && isEqual(colors, board.colors) && 
	#            isEqual(bar, board.bar) && isEqual(off, board.off));
	#  }
	#	/**
	#   * Returns the hashCode of this move
	#   *
	#   * @return the hasCode of the final board
	#   */
	#  public int hashCode() {
	#    int base = 19283;
	    
	#    base = hash(base, off);
	#    base = hash(base, bar);
	#    base = hash(base, board);
	#    base = hash(base, colors);
	#    return base;
	#  }
	  
	
	#  protected int hash(int base, int[] array) {
	#    for (int i=0; i<array.length; i++) {
	#      if (array[i] == 0)
	#        base = (base * 273891);
	#      else
	#        base = (base + array[i]) ^ (array[i] + 55);
	#    }
	#    return base;
	#  }

	
	# /**
	# * Constructor, builds a copy of the given board
	# */
	# protected Board(Board other) {
	# // initialze this board
	# this();
	# // place the pieces
	# System.arraycopy(other.board, 0, this.board, 0, this.board.length);
	# System.arraycopy(other.colors, 0, this.colors, 0, this.colors.length);
	# System.arraycopy(other.bar, 0, this.bar, 0, this.bar.length);
	# System.arraycopy(other.off, 0, this.off, 0, this.off.length);
	# }

	# /**
	# * Returns a scratch copy of the board, which is a clone and
	# * can be changes without any problems.
	# *
	# * @return a scratch copy of this board
	# */
	# public Board getScratch() {
	# return new Board(this);
	# }

