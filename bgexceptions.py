""" Defines some custom Errors for Backgammon. """

class BackgammonException(Exception):

	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return repr(self.msg)
	

class IllegalMoveException(BackgammonException):
	
	def __init__(self, msg):
		super(IllegalMoveException, self).__init__(msg)

# class test(object):
# 	def exception(self):
# 		try:
# 			raise BackgammonException("blabla")
# 		except BackgammonException, e:
# 			print "BackgammonException:", e

# 		print "yeehaw"

# t = test()
# t.exception()