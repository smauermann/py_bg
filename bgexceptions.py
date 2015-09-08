

class BackgammonException(Exception):
	""" Super class for custom Exceptions in the Backgammon framework. """
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return repr(self.msg)
	

class IllegalMoveException(BackgammonException):
	""" Exceptions related to wrong or not possible moves. """
	def __init__(self, msg):
		super(IllegalMoveException, self).__init__(msg)