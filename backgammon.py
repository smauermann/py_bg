from board import Board, Dice
from player import Player


class Backgammon(object):
    """ This class wraps all of the backgammon functionality. Basically,
        the use model for this class is to build a new Backgammon with
        two players, execute backgammon.run(), which runs the game, and
        the call backgammon.reset(), backgammon.run() if you
        want to play again. """
    def __init__(self):
        # the dice
        self.dice = Dice()
        # internal board, which is the state before the current move
        self.board = Board()
        # color of the current player
        self.current_player = None
        # list of players
        # white = 0, black = 1
        self.players = [Player('white'), Player('black')]
        self.reset()
    
    def reset(self):
        """ Resets this backgammon instance to the initial state, with
            a new board and determines starting player. """
        self.board.reset_board()
        self.dice.roll()
        
        # decide which player starts the game by rolling dice
        # die1 > die2 player 0 starts and vice versa
        # if die1==die2, roll until different
        if self.dice.get_die1() != self.dice.get_die2():
            # determine starting player:
            # die1 rolls for white and die2 rolls for black
            self.current_player = (0 if self.dice.get_die1() >
                                    self.dice.get_die2() else 1)
        # make sure that dice dont show same number
        elif self.dice.get_die1() == self.dice.get_die2():
            same = True
            # roll until different
            while same:
                self.dice.roll()
                if self.dice.get_die1() != self.dice.get_die2():
                    self.current_player = (0 if self.dice.get_die1() >
                                            self.dice.get_die2() else 1)
                    same = False
        
        # if black starts game, reverse players list
        # because white is first initially
        if self.current_player == 1:
            self.players = list(reversed(self.players))
                            
    def run(self):
        """ Runs a game of backgammon, and does not return until the game
            is over. Returns the player who won the game. """
        while not self.board.is_gameover():
            # loop over players
            for player in self.players:
                # request players to choose a board
                self.get_board_from_player(player)
                if self.board.is_gameover():
                    break

        # check whether a player has all checkers beared off
        # and return it as winner. 
        if self.board.get_off(0) == 15:
            winner = 0
        elif self.board.get_off(1) == 15:
            winner = 1
        return winner

    def get_board_from_player(self, player):
        """ Receives a board from the player and initiates the next turn. """
        board = player.choose_board(self)
        self.next_turn(board)

    def next_turn(self, board):
        """ Updates the board according to chosen move
            and initiates the next turn. """
        # update board according to chosen board
        self.board = board
        # roll new dice
        self.dice.roll()
        # set the opponent as current_player
        self.current_player = Board.get_opponent(self.current_player)
        #print "\nIt's {0}'s turn, with the roll: {1} ".format("white" if self.current_player == 0 else "black", self.dice)

wins = [0, 0]
bg = Backgammon()
bg.run()
bg.reset()

# for timed runs:
# def timed():
#     """Stupid test function"""
#     bg.run()
#     bg.reset()

# if __name__ == '__main__':
#     import timeit
#     total = 0
#     for i in range(10):
#         time = timeit.timeit("timed()", setup="from __main__ import timed", number=1)
#         print i+1,time, "s"
#         total += time

#     print "Mean:", total/10, "s"


