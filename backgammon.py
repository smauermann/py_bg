from board import Board, Dice
from move import BarMove, BearOffMove, NormalMove, BoardFactory
import random

class Player(object):
    """ Class which represents a backgammon player. The Backgammon
        object will repeatedly call getMoveFromPlayer() on this player, asking
        the agent to pick a move. """

    COLOR_CODE = {'white': 0, 'black': 1}

    def __init__(self, color):
        """ Player can be initialized by specifying color:
            E.g.: 'white' or 0 vs. 'black' or 1. """
        if type(color) is int:
            self.color = color
            self.identity = next((key for key, val in Player.COLOR_CODE.items() \
                                    if val == color), None)
        elif type(color) is str:
            color = color.lower()
            self.identity = color
            self.color = Player.COLOR_CODE[color]
        else:
            print "Enter valid player: Either 'white' - 0, or 'black' - 1!"

    def choose_board(self, backgammon):
        """ Requests the player to pick a board given
            the current backgammon situation. """
        # get a list of all possible moves
        boards = BoardFactory.generate_all_boards(backgammon.current_player,\
                                            backgammon.dice, backgammon.board)
        
        # prompt player to chose a move
        #pick_board = int(raw_input("Pick from %s boards: " %(len(boards))))
        #print boards[pick_board - 1]
        #return boards[pick_board - 1]
        
        # pick a random move
        random_board = random.choice(boards)
        #print random_board
        return random_board

    @staticmethod
    def board_to_vector(backgammon):
        """ Creates a 198-dimensional input vector
            of the current gammon situation. """
        # i need to fetch boards from player.choose_board()
        bg_board = backgammon.get_current_board()
        current_player = backgammon.get_current_player()
        
        board = bg_board.board
        colors = bg_board.colors
        bar = [bg_board.get_bar(0),bg_board.get_bar(1)]
        off = [bg_board.get_off(0),bg_board.get_off(1)]
        
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
            # check color at current position, proceed when color is not -1
            # (means no checkers)
            if colors[pos] != -1:
                # start of the 4-unit stretch in vector
                # first 96
                start = (pos * units) if colors[pos] == 0 else \
                        ((len_vector/2 - 1) + pos * units)
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
            vector[white_bar_input] = bar[0] / 2.0 #'wBar: %s' %(white_bar_input)
            vector[black_bar_input] = bar[1] / 2.0 #'bBar: %s' %(black_bar_input)
            # encode off
            # white: unit 98 (vector[97]) and black: unit 194 (vector[193])
            white_off_input = white_bar_input + 1
            black_off_input = black_bar_input + 1
            vector[white_off_input] = off[0] / 15.0  # 'wOff: %s' %(white_off_input)
            vector[black_off_input] = off[1] / 15.0 # 'bOff: %s' %(black_off_input)
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
    """ This class wraps all of the backgammon functionality. Basically,
        the use model for this class is to build a new Backgammon with
        two players, execute backgammon.run(), which runs the game, and
        the call backgammon.reset(), backgammon.run() if you
        want to play again. """

    def __init__(self, player1, player2):
        # the dice
        self.dice = Dice()
        # internal board, which is the state before the current move
        self.board = Board()
        # color of the current player
        self.current_player = None
        # list of players
        # white = 0, black = 1
        self.players = [player1, player2]
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

white_player = Player(0)
black_player = Player(1)

wins = [0, 0]
bg = Backgammon(white_player, black_player)
# for i in range(1000):
#     print "Game: ", i
#     winner = bg.run()
#     bg.reset()

#     if winner == 0:
#         wins[0] += 1
#     elif winner == 1:
#         wins[1] += 1

# print wins

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


