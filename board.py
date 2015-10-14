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

    def get_dice(self):
        return self.dice
        
    def get_die1(self):
        return self.dice[0]

    def get_die2(self):
        return self.dice[1]

    def is_doubles(self):
        """ Returns whether dice are doubles or not. """
        return self.dice[0] == self.dice[1]

    def __str__(self):
        return "{0}, {1}".format(self.dice[0], self.dice[1])

    def __eq__(self, other):
        if isinstance(self, Dice):
            return self.dice == other.dice
        else:
            return False

    def __ne__(self, other):
        return not self == other


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
    def __init__(self, other_board=None):
        if other_board is None:
            # initialize the board
            self.board = None
            self.colors = None
            self.bar = None
            self.off = None
            self.move_history = []
            self.reset_board()
        else:
            # way faster than copy.deepcopy()
            self.board = list(other_board.board)
            self.colors = list(other_board.colors)
            self.bar = list(other_board.bar)
            self.off = list(other_board.off)
            self.move_history = list(other_board.move_history)
            # self.board = copy.deepcopy(other_board.get_board())
            # self.colors = copy.deepcopy(other_board.get_colors())
            # self.bar = copy.deepcopy(other_board.bar)
            # self.off = copy.deepcopy(other_board.off)
            # self.move_history = copy.deepcopy(other_board.move_history)
    
    def reset_board(self):
        """ Resets checkers on the board to the initial configuration. """
        self.board = [0] * Board.NUM_POINTS
        self.colors = [Board.NEITHER] * Board.NUM_POINTS
        self.bar = [0] * 2
        self.off = [0] * 2

        for i,loc in enumerate(Board.INITIAL_LOCATIONS):
            self.board[loc] = Board.INITIAL_NUMOFCHECKERS[i]
            self.colors[loc] = Board.INITIAL_COLORS[i]

    def update_move_history(self, move_string):
        self.move_history.append(move_string)

    def reset_move_history(self):
        self.move_history = []

    def copy_board(self):
        """ Return a deep copy of the current board,
            which can be changed without affecting the actual board itself. """
        board_copy = copy.deepcopy(self)
        return board_copy

    def get_winner(self):
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

    def is_gameover(self):
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

    def get_checkers(self, location, player=None):
        """ Returns the number of checkers at a given location.
            By passing a color, the method checks for it at location. """
        #print location
        if player is not None:
            if self.colors[location] == player:
                return self.board[location]
            else:
                return 0
        elif player == None:
            return self.board[location]

    def get_bar(self, player):
        """ Returns the number of checkers of a given color on the bar."""
        return self.bar[player]

    def get_off(self, player):
        """ Returns the number of checkers of the given color beared off. """
        return self.off[player]

    def get_pipcount(self, player):
        """ Calculates pip count for a given player. Pip count is the total
            number of points a player has to move its checkers in order to
            bear all of them off. """
        base = self.getHome(player)
        result = 0

        for i in range(Board.NUM_POINTS):
            if self.colors[i] == player:
                # get checkers of given color at i and multiply by distance
                # to home end point
                result += self.get_checkers(i) * abs(base - i)

        # add number of moves needed to clear the bar
        result += Board.NUM_POINTS * self.getBar(player)
        return result

    def move_to_location(self, player, location):
        """ Moves a checker of given color to the given location. """

        if self.colors[location] == self.get_opponent(player):
            raise IllegalMoveException("Unexpected error: \
                                    Position already occupied by other Player!")

        self.board[location] += 1

        # change color at position after move
        if self.board[location] == 1:
            self.colors[location] = player

    def remove_from_location(self, player, location):
        """ Removes a checker of given color from the given location. """
        if self.colors[location] != player:
            raise IllegalMoveException("Unexpected error: \
                                        no checkers to remove from position!")
        
        self.board[location] -= 1
        
        if self.board[location] == 0:
            self.colors[location] = Board.NEITHER

    def move_to_bar(self, player):
        """ Moves checker of given color to the bar. """
        self.bar[player] += 1

    def remove_from_bar(self, player):
        """ Removes checker of given color from the bar. """
        if self.bar[player] == 0:
            raise IllegalMoveException("Unexpected error - no checkers on bar!")
        
        self.bar[player] -= 1

    def move_off(self, player):
        """ Moves checker of given color off of the board. """
        self.off[player] += 1

    # termed getBase in Java implementation
    @staticmethod
    def get_home(player): 
        """ Returns the home location for a given color.
            Ergo the goal location of a color. """
        return (24 if player == Board.WHITE else -1)

    @staticmethod
    def get_direction(player):
        """ Return direction of given color, either 1 (white) or -1 (black). """
        return (1 if player == Board.WHITE else -1)

    @staticmethod
    def get_opponent(player):
        """ Returns color of the opponent. """
        return (Board.WHITE if player == Board.BLACK else Board.BLACK)

    @staticmethod
    def on_board(location):
        """ Returns whether given location is on the board. """
        return ((location >= 0) and (location < Board.NUM_POINTS))
        
    @staticmethod
    def is_between(location, lower, upper):
        """ Method to check whether given position
            is between two given points. """
        return ((location >= lower and location <= upper) or
                (location <= lower and location >= upper))

    @classmethod
    def in_home_board(cls, player, location):
        """ Method to check whether the point is
            in the given color's home board. """
        return (cls.is_between(location, cls.get_home(player),
                cls.get_home(player) - (6 * cls.get_direction(player))))

    def __str__(self):
        """ Prints the current board in a GNUBGish style to the console. """
        
        print "\n+13-14-15-16-17-18------19-20-21-22-23-24-+"

        # left upper field:
        # coordinates:
        # y = 1...5
        # x = 12...17
        for y in range(1, 6):
            print "|",
            for x in range(12, 18):
                if x == 17:
                    if y == 3:
                        # bar
                        print "{:1} |{:>2}".format(self.checker_print(x, y), self.bar[Board.BLACK]),
                    else:
                        print "{:1} |".format(self.checker_print(x, y)),    
                else:
                    print "{:1} ".format(self.checker_print(x, y)),
            
            # right upper field:
            # coordinates:
            # y = 1...5
            # loop over blacks starting board, ie whites homeboard
            # x = 18...23
            for x in range(18, 24):
                if x == 18:
                    if y == 3:
                        print "|{:>2} ".format(self.checker_print(x, y)),
                    else:
                        print "  | {:1} ".format(self.checker_print(x, y)),
                if x == 23:
                    # off
                    if y == 3:
                        print "{:1} | {:3}".format(self.checker_print(x, y), self.off_print(x, y))
                    else:
                        print "{:1} |".format(self.checker_print(x, y))  
                elif x != 18 and x != 23:
                    print "{:1} ".format(self.checker_print(x, y)),

        print "|                  |BAR|                  |OFF"

        # left lower field:
        # coordinates:
        # y = 5...1
        # x = 11...6
        for y in range(5, 0, -1):
            print "|",
            for x in range(11, 5, -1):
                if x == 6:
                    if y == 3:
                        # bar
                        print "{:1} | {:1}".format(self.checker_print(x, y), self.bar[Board.WHITE]),
                    else:
                        print "{:1} |".format(self.checker_print(x, y)),    
                else:
                    print "{:1} ".format(self.checker_print(x, y)),

            # right lower field:
            # coordinates:
            # y = 5...1
            # loop over white start, ie blacks homeboard
            # x = 5...0
            for x in range(5, -1, -1):
                if x == 5:
                    if y == 3:
                        print "| {:1} ".format(self.checker_print(x, y)),
                    else:
                        print "  | {:1} ".format(self.checker_print(x, y)),
                if x == 0:
                    # off
                    if y == 3:
                        print "{:1} | {:3}".format(self.checker_print(x, y), self.off_print(x, y))
                    else:
                        print "{:1} |".format(self.checker_print(x, y))
                elif x != 5 and x != 0:
                    print "{:1} ".format(self.checker_print(x, y)),
        
        print "+12-11-10--9--8--7-------6--5--4--3--2--1-+"
        return " "

    def checker_print(self, pos, count):
        """ Utility function for printing checkers on the GNUBG-style board. """
        if self.colors[pos] == Board.WHITE:
            player = Board.WHITE
            sign = "w"
        elif self.colors[pos] == Board.BLACK:
            player = Board.BLACK
            sign = "b"
        else:
            player = None
            sign = " "

        checkers = self.get_checkers(pos, player)
        if player is not None:
            if count == 5 and checkers > 5:    
                if checkers < 10:
                    return checkers
                else:
                    return "+"
            elif checkers >= count:
                return sign
            elif count > checkers:
                return " "
        else:
            return " "

    def off_print(self, pos, count):
        """ Utility function for printing borne-off
            checkers on the the GNUBG-style board. """
        if pos in range(0, 12):
            player = Board.BLACK
            sign = "black"
        elif pos in range(12, 24):
            player = Board.WHITE
            sign = "white"

        off = self.get_off(player)
        return str(off) + " " + str(sign)
        
    def __eq__(self, other):
        """ Compare this board with provided other board object. """
        if isinstance(other, Board): 
            return (self.board == other.board and
                    self.colors == other.colors and
                    self.bar == other.bar and
                    self.off == other.off)
        else:
            return False

    def __ne__(self, other):
        """ Returns True when objects are not equal. """
        return not self == other

    def __hash__(self):
        """ Returns hash value of the current board. """
        # hashing as it is recommended in the python doc
        return (hash(tuple(self.board)) ^
                hash(tuple(self.colors)) ^
                hash(tuple(self.bar)) ^
                hash(tuple(self.off)))

