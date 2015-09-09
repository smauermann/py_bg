# TODO: figure out how to efficiently batch import from a different directory
from abc import ABCMeta, abstractmethod
from board import Board, Dice
from bgexceptions import BackgammonException, IllegalMoveException


class Movement(object):
	# declares this class as an abstract base class (ABC)
	# used to enforce implementation of class methods
	# (herein decorated with @abstractmethod) in derived subclasses,
	# otherwise raises TypeError
	__metaclass__ = ABCMeta

	def __init__(self, player):
		self.player = player

	def getPlayer(self):
		""" Returns the player making this movement. """
		return self.player

	@abstractmethod
	def apply(self, board):
		""" Validates this movement given the provided
			board situation. """
		pass
	
	@abstractmethod
	def canUse(self, board, die):
		""" Returns whether or not this movement can use the given
			dice roll to perfrom it's movement. """
		pass


class BarMovement(Movement):
	""" Methods for moving from the Bar. """

	def __init__(self, player, end):
		# calls the __init__ of the super class Movement
		# with player as the argument, makes it an instance attribute
		# within this class too
		super(BarMovement, self).__init__(player)
		
		self.other_player = Board.getOtherPlayer(self.player)
		
		if not Board.onBoard(end):
			raise IllegalMoveException("End is not on the Board!")

		self.end = end
		
	def getEnd(self):
		""" Returns end location of the movement. """
		return self.end

	# die is one number of one die 
	# java version passes also a board object, why?
	# prolly because abstract method needs to be implemented with same parameters
	# python is here more flexible
	def canUse(self, board_obj, die):
		""" Returns whether or not this movement can use the given
			dice roll to perform its movement. """
		# get home of opponent (24 for white or -1 for black)
		# subtract the end location, eg white rolls a 3 and can put on position 2 (3 in real board)
		return die == abs(Board.getHome(self.other_player) - self.end)

	def apply(self, board_obj):
		""" Validates the movement given the provided board situation. """
		# check if bar is empty and raise error if yes
		if board_obj.getBar(self.player) == 0:
			raise IllegalMoveException("Off-Bar not possible: No checkers on the Bar!")

		# check if end position is in the homeboard of the other player
		# if not raise Error, checkers leaving the bar must be placed in the
		# homeboard of the opponent (your starting quadrant)
		if not Board.inHomeBoard(self.other_player, self.end):
			raise IllegalMoveException("Off-Bar not possible: Checkers must go into the opponents home board!")

		# check if there is more than one opponent checker at end position
		# and raise error when yes 
		if board_obj.getCheckers(self.end, self.other_player) > 1:
			raise IllegalMoveException("Off-Bar not possible: Location occupied by other player")

		# now make the movement:
		# first kick enemy checkers onto the bar if there are any
		if board_obj.getCheckers(self.end, self.other_player) == 1:
			board_obj.removeFromLocation(self.other_player, self.end)
			board_obj.moveToBar(self.other_player)

		board_obj.removeFromBar(self.player)
		board_obj.moveToLocation(self.player, self.end)

	@classmethod
	def movePossible(cls, die, player, board_obj):
		""" Return whether or not a move is possible using 
			the given dice roll by the given player in the given board.
			Checks to see if a bar, bear-off, or normal movement 
			are possible. """
		other_player = Board.getOtherPlayer(player)
		
		try:
			destination = (Board.getHome(other_player) +
							(Board.getDirection(player) * die))
			
			bar_movement = cls(player, destination)
			scratch_board = board_obj.getScratch()
			bar_movement.apply(scratch_board)
			return True
		except IllegalMoveException, e:
			#print type(e).__name__, "-", e.msg
			pass

		return False

	def __str__(self):
		""" Returns string representation of this movement. """
		return "bar --> %s" %(self.end + 1)

	def __eq__(self, other):
		""" Returns whether this movement is equal to the provided object. """
		if isinstance(other, BarMovement):
			return other.end == self.end
		else:
			return False

	def __ne__(self, other):
		return (not self.__eq__(other))


class BearOffMovement(Movement):
	""" Methods for bearing off a checker. """
	# rules for bear-off:
	# - all checkers must be in the homeboard of a color (end area)
	# - endboard numbered 1...6 with 1 closest to end of gameboard
	#	and 6 closest to bar
	# - roll a 1, bear off checker from 1
	# - roll a 6, bear off checker from 6
	# - if no checker at rolled position in homeboard, make legal move within the homeboard
	# - when number is rolled that is higher than the highest point with checkers,
	#	bear off next highest checker
	
	def __init__(self, player, start):
		# calls the __init__ of the super class Movement with player 
		# as the argument, makes it an instance attribute
		# within this class too
		super(BearOffMovement, self).__init__(player)

		if not Board.onBoard(start):
			raise IllegalMoveException("Start is not on the board!")

		self.start = start
		
	def getStart(self):
		return self.start

	@classmethod
	def movePossible(cls, die, player, board_obj):
		""" Return whether or not a move is possible using the
			given dice roll by the given player on the given
			board. Checks if bar, bear-off, or normal Movement
			are possible. """
		# returns 1 for white, black -1
		direction = Board.getDirection(player)

		# 18 for white, 5 for black
		start = Board.getHome(player) - (6 * direction)
		
		# 23 for white, 0 for black
		end = Board.getHome(player) - direction

		# loop through homeboard (23...18 for white and 0..5 for black)
		for i in range(start, end + direction, direction):
			bear_off_movement = cls(player, i)
			
			if bear_off_movement.canUse(board_obj, die):
				try:
					scratch_board = board_obj.getScratch()
					bear_off_movement.apply(scratch_board)
					return True
				except IllegalMoveException, e:
					#print type(e).__name__, "-", e.msg
					pass
		return False

	def canUse(self, board_obj, die):
		""" Returns whether or not this movement can use the given
			dice roll to perform its movement. """
		# returns 1 for white, black -1
		direction = Board.getDirection(self.player)
		
		# not sure why they subtract direction?
		# difference between real 1..24 numbering and internal 0...23 system?
		start = self.start - direction
		
		# end must be start of the own homeboard
		# which is 18 for white, and 5 for black
		end = Board.getHome(self.player) - (direction * 6)
		
		# loop from start position of movement towards the own starting zone
		# (the opponents homeboard), while staying in own homeboard
		for i in range(start, end - direction, -direction):
			if board_obj.getCheckers(i, self.player) > 0:
				# check if roll matches homeboard position 1..6
				return die == abs(self.start - Board.getHome(self.player))
				
		return die >= abs(self.start - Board.getHome(self.player))

	def apply(self, board_obj):
		""" Validates this movement given the provided
			board situation. """
		if board_obj.getCheckers(self.start, self.player) == 0:
			raise IllegalMoveException("Bear-off not possible: No checkers at location!")

		if board_obj.getBar(self.player) > 0:
			raise IllegalMoveException("Bear-off not possible: Checkers from the bar must be moved first!")

		# loop over whole board and check whether all checkers are in the homeboard
		# if not all checkers are in the homeboard, bear-off is NOT allowed
		for i in range(Board.NUM_POINTS):
			if (board_obj.getCheckers(i, self.player) > 0) and (not Board.inHomeBoard(self.player, i)):
				raise IllegalMoveException("Bear-off not possible: Still checkers outside of the home board!")

		# now make the move
		board_obj.removeFromLocation(self.player, self.start)
		board_obj.moveOff(self.player)

	def __str__(self):
		""" Returns string representation of this movement. """
		return "%s --> off" %(self.start + 1)

	def __eq__(self, other):
		""" Returns whether this movement is equal to the provided object. """
		if isinstance(other, BearOffMovement):
			return other.start == self.start
		else:
			return False

	def __ne__(self, other):
		return (not self.__eq__(other))


class NormalMovement(Movement):
	""" Methods for a normal movement. """

	def __init__(self, player, start, end):
		# reminder: invoke the init of the superclass with player as argument
		super(NormalMovement, self).__init__(player)

		self.other_player = Board.getOtherPlayer(self.player)
		
		if not (Board.onBoard(start) or Board.onBoard(end)):
			raise IllegalMoveException("Start or end is not on the board!")

		self.start = start
		self.end = end

	def getStart(self):
		""" Returns the start position of the movement. """
		return self.start

	def getEnd(self):
		""" Returns the end position of the movement. """
		return self.end

	def canUse(self, board_obj, die):
		""" Returns whether or not this movement can use the given
			dice roll to perform its movement. """
		return die == abs(self.start - self.end)

	def apply(self, board_obj):
		""" Validates this movement given the provided
			board situation. """
		if self.start == self.end:
			raise IllegalMoveException("Normal move not possible: Start and end must not be the same position!")

		if abs(self.start - self.end) > Dice.MAX_VALUE:
			raise IllegalMoveException("Normal move not possible: Move distance larger than 6!")

		if board_obj.getBar(self.player) > 0:
			raise IllegalMoveException("Normal move not possible:: Checkers from the bar must be moved first!")

		if board_obj.getCheckers(self.start, self.player) == 0:
			raise IllegalMoveException("Normal move not possible: No checkers at the start location!")

		if ((self.start > self.end) and (board_obj.getDirection(self.player) > 0) or
			(self.start < self.end) and (board_obj.getDirection(self.player) < 0)):
			raise IllegalMoveException("Normal move not possible: Backward movements are not allowed!")

		if board_obj.getCheckers(self.end, self.other_player) > 1:
			raise IllegalMoveException("Normal move not possible: End location already occupied by opponent checkers!")

		# now perform movement:
		# check first whether the move bumps the opponent
		if board_obj.getCheckers(self.end, self.other_player) == 1:
			board_obj.removeFromLocation(self.other_player, self.end)
			board_obj.moveToBar(self.other_player)

		# now perform the move
		board_obj.removeFromLocation(self.player, self.start)
		board_obj.moveToLocation(self.player, self.end)

	@classmethod
	def movePossible(cls, die, player, board_obj):
		""" Return whether or not a move is possible using the
			given dice roll by the given player on the given
			board. Checks if bar, bear-off, or normal Movement
			are possible. """
		# is a static method
		# direction is 1 for white and -1 for black
		direction = Board.getDirection(player)
		
		# getHome is a staticmethod, hence called with class not instance
		# Board.getHome() returns 24 for white else -1 
		# start is (0 for white, and 23 for black)
		start = Board.getHome(Board.getOtherPlayer(player)) + direction

		# end is 23 for white else 0
		end = Board.getHome(player) - direction
		
		# loop over the whole board (eg. 0...23 for white)
		for i in xrange(start, end, direction):
			# check if movement is still on board from location i
			if not Board.onBoard(i + (die * direction)):
				break
			else:
				try:
					normal_movement = cls(player, i, i + (die * direction))
					scratch_board = board_obj.getScratch()
					normal_movement.apply(scratch_board)
					return True
				except IllegalMoveException, e:
					#print type(e).__name__, "-", e.msg
					pass
		return False

	def __str__(self):
		""" Returns a String representation of this movement. """
		return "%s --> %s" %(self.start + 1, self.end + 1)

	def __eq__(self, other):
		""" Returns whether this movement is equal to the provided object. """
		if isinstance(other, NormalMovement):
			return (other.start == self.start) and (other.end == self.end)
		else:
			return False

	def __ne__(self, other):
		return (not self.__eq__(other))


class Move(object):
	""" Class which represents a move in backgammon.  Clients
		can either build specific moves themselves, possibly from 
		human input, or use the movement factory to build moves.
		Moves are constructed by adding a number of movements until
		all of the dice have been used or no more moves are possible.
		When evalutaing a move, a client can use the 
		Move.getCurrentBoard() method, which will return the state
		of the board after the move. """
	
	# placeholder for a used move
	USED = -1
	
	# input order: *args = dice_obj, board_obj, player
	def __init__(self, *args):
		if len(args) == 3:
			# the dice used for this move
			self.dice = args[0]
			# the original board
			self.board = args[1]
			# the player this move is for
			self.player = args[2]
		
			# Build a new Move, using the provided dice roll
			# Check for doubles: player who rolls doubles plays numbers on dice twice.
			# A roll of 6 and 6 means that the player has four sixes to use.
			if self.dice.isDoubles():
				# set of movements used to perform this move in this order
				self.movements = [None] * Dice.NUM_DICE * 2
				# hypothetical boards, with the intermediate movements applied
				self.boards =  [None] * Dice.NUM_DICE * 2
				# list of usable die numbers, upon use items become -1
				self.used = [self.dice.getDie1()] * Dice.NUM_DICE * 2
			else:
				# two dice, which roll two numbers, gives two moves
				self.movements = [None] * Dice.NUM_DICE
				self.boards =  [None] * Dice.NUM_DICE
				self.used = [None] * Dice.NUM_DICE
				self.used[0] = self.dice.getDie1()
				self.used[1] = self.dice.getDie2()
		# when cloning a move, len(args) = 1, containing only move to be cloned
		elif len(args) == 1:
			self.dice = args[0].dice
			self.board = args[0].board
			self.player = args[0].player
			self.movements = args[0].movements
			self.boards = args[0].boards
			self.used = args[0].used
		else:
			print "Move could neither be initialized nor cloned!"

	def movePossible(self):
		""" Returns whether or not a move is possible for current player. """
		for die in self.used:
			if (die != Move.USED and
				MovementFactory.movePossible(die, self.player, self.getCurrentBoard())):
				return True
		return False

	def getNumMovements(self):
		""" Returns the number of movements applied to the current move. """	
		# loop through movements list and return number of movements left,
		# i.e. the items in the list until the loop hits a None
		for i in range(len(self.movements)):
			if self.movements[i] == None:
				# i returns the number of movements made
				return i
		# returns only when no movements were added to this move
		return len(self.movements)
	
	def isFull(self):
		""" Returns whether or not all moves have already been made. """
		# returns True if no more movements can be added to the move 
		# returns False still movements can be made
		return self.getNumMovements() == len(self.movements)

	def addMovement(self, movement_obj):
		""" Adds a movement to the game. """
		if self.isFull():
			raise IllegalMoveException("Cannot add more movements to this move!")

		use = Move.USED
		
		# self.used is the list containing the two or four numbers rolled by the dice
		# loop thru self.used while no roll was not used yet
		while use == Move.USED:
			for n, die in enumerate(self.used):
				# check if dice number is not used yet and movement can be done via
				# the rolled dice
				if die != Move.USED and (movement_obj.canUse(self.getCurrentBoard(), die)):
					use = n

		if use == Move.USED:
			raise IllegalMoveException("You cannot make that move using the dice!")

		# do the movement
		# get the current board
		current_board = self.getCurrentBoard()
		# put a scratch copy of it in the intermediate boards list
		self.boards[self.getNumMovements()] = current_board.getScratch()
		# apply the movement to the scratch board
		movement_obj.apply(self.boards[self.getNumMovements()])

		# update meta data
		self.used[use] = Move.USED
		self.movements[self.getNumMovements()] = movement_obj

	def getCurrentBoard(self):
		""" Returns current scratch board, or the board with all
			intermediate movements applied. """
		for i in range(len(self.boards) - 1, 0, -1):
			if self.boards[i] is not None:
				# return the current intermediate board
				return self.boards[i]
		# or the starting board, if no intermediate boards exist
		return self.board.getScratch()

	def getOriginalBoard(self):
		""" Returns the starting board of the move. """
		return self.board

	def __str__(self):
		""" Returns string representation of this move and its single movements. """
		for movement in self.movements:
			print movement
			
	def __eq__(self, other):
		""" Returns whether or not this move is equal to the other. """
		if isinstance(other, Move):
			return (self.player == other.player and
					self.dice == other.dice and
					# Board.isEqual is a utility function looping thru two lists
					Board.isEqual(self.used, other.used) and
					self.getCurrentBoard() == other.getCurrentBoard())
		else:
			return False

	def __ne__(self, other):
		return (not self.__eq__(other))

	def __hash__(self):
		""" Returns the hash code of this move based on hashing the board situation. """
		return self.getCurrentBoard().__hash__()


class MovementFactory(object):
	""" Generates all distinct moves for the given Board and the
		provided dice roll. """

	@staticmethod
	def movePossible(die, player, board_obj):
		""" Return whether or not a move is possible using 
			the given dice roll by the given player in the given board.
			Checks to see if a bar, bear-off, or normal movement
			are possible. """
		return (BarMovement.movePossible(die, player, board_obj) or
				BearOffMovement.movePossible(die, player, board_obj) or
				NormalMovement.movePossible(die, player, board_obj))

	@classmethod
	def getAllMoves(cls, player, dice_obj, board_obj):
		""" Returns a list of all possible distinct moves for the given player,
			given the starting board and the given dice roll. """
		result = set()
		# make a base move upon which possible movements are added
		base_move = Move(dice_obj, board_obj, player)
		result.update(cls.generateMoves(base_move))
		
		print len(result)
		return [item for item in result]

	@classmethod
	def generateMoves(cls, base_move):
		""" Returns a set of all possible moves given the board situation
			and using the given dice roll. """
		# construction of moves and their objects:
		# a move consists of 2 or 4 movements, contained in movements list
		# generateMoves

		result = set()
		
		# if no more movements can be added, or no more moves are possible,
		# return just this move
		if base_move.isFull() or (not base_move.movePossible()):
			result.add(base_move)
			return result

		# get current Board
		board = base_move.getCurrentBoard()
		player = base_move.player

		# try to add any off-bar movements to base_move
		if board.getBar(player) > 0:
			# loop thru used dice
			for die in base_move.used:
				# take the roll, which wasnt used yet
				if die != Move.USED:
					try:
						# create a new bar move by cloning from base_move
						bar_move = Move(base_move)
						# destination is position 1...6 in opponents homeboard
						destination = (Board.getHome(Board.getOtherPlayer(player))
										+ die * Board.getDirection(player))
						# add the movement to the move
						# updates intermediate board and adds movement to movements
						bar_move.addMovement(BarMovement(player, destination))
						#cls.generateMoves(bar_move)
						result.update(cls.generateMoves(bar_move))
					# exceptions in the try block must be handled with the corresponding
					# exception type in the except block, otherwise script ends
					except IllegalMoveException, e:
						#print type(e).__name__, "-", e.msg
						pass
		# try normal moves
		else:
			# loop over whole board from start to end
			direction = Board.getDirection(player)
			start = Board.getHome(Board.getOtherPlayer(player)) + direction
			end = Board.getHome(player)
			
			for pos in range(start, end, direction):
				if board.getCheckers(pos, player) > 0:
					# when two different numbers were rolled
					if len(base_move.used) == 2:
						for die in base_move.used:
							if die != Move.USED:
								try:
									normal_move = Move(base_move)
									destination = pos + die * direction
									normal_move.addMovement(NormalMovement(player, pos, destination))
									#cls.generateMoves(normal_move)
									result.update(cls.generateMoves(normal_move))
								except IllegalMoveException, e:
									#print type(e).__name__, "-", e.msg
									pass
					# when a double was rolled
					else:
						try:
							normal_move = Move(base_move)
							destination = pos + base_move.dice.getDie1() * direction
							normal_move.addMovement(NormalMovement(player, pos, destination))
							#cls.generateMoves(normal_move)
							result.update(cls.generateMoves(normal_move))
						except IllegalMoveException, e:
							#print type(e).__name__, "-", e.msg
							pass

			# lastly try any bear-off moves
			start = Board.getHome(player) - Board.getDirection(player)
			direction = Board.getDirection(player)
			i = start
			#for pos in range(start, start + 6 * )
			while Board.inHomeBoard(i, player):
				if board.getCheckers(i, player) > 0:
					try:
						bearoff_move = Move(base_move)
						bearoff_move.addMovement(BearOffMovement(player, i))
						result.update(cls.generateMoves(bearoff_move))
					except IllegalMoveException, e:
						#print type(e).__name__, "-", e.msg
						pass
				#update i
				i -= direction

		return result

# dice = Dice()
# dice.roll(1,2)
# print dice
# board = Board()
# print board
# move = Move(dice, board, 0)
# mf = MovementFactory()
# all_moves = mf.generateMoves(move)
# move_from_set = all_moves.pop()
# for item in move_from_set.movements:
# 	print item.toString()






