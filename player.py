from board import Board, Dice
from neural_net import NeuralNetwork
from move import BoardFactory
import random
import numpy as np


class Player(object):
    """ Class which represents a backgammon player. """

    COLOR_CODE = {'white': Board.WHITE, 'black': Board.BLACK}

    def __init__(self, color, neural_network, learning_mode):
        """ Player can be initialized by specifying color:
            E.g.: 'white' or 0 vs. 'black' or 1. """
        self.neural_network = neural_network
        # the mode indicates whether the board backprops errors,
        # or just predicts which boards are best for player
        self.learning_mode = learning_mode

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

    def choose_move(self, backgammon):
        """ Function passes the list of all possible boards to the net and
            evaluates them. Training can be disabled by the Player class
            parameter - 'learning_mode'. In this case the net only
            predicts the chances of winning for a board. """
        
        best_board = None
        # the value representing the expected contribution of a distinct
        # board to win the game
        expected_utility = -1.0
        # next_out is the network output of the selected new board
        next_output = []

        # get all possible boards from BoardFactory
        all_boards = BoardFactory.generate_all_boards(backgammon.current_player, \
                                                        backgammon.dice, \
                                                        backgammon.board)

        # loop over all boards
        for board in all_boards:
            board_vector = self.board_to_vector(board)
            output = self.neural_network.get_network_output(board_vector)
            # translate network output into an actual meaning for player
            # eg if output [0.1, 0.3], white odds of winning are lower
            # than black's odds
            utility = self.compute_utility(output)

            if utility > expected_utility:
                best_board = board
                expected_utility = utility
                next_output = output

        # learning_mode indicates whether the network propagates back errors
        # or only evaluates boards
        if self.learning_mode:
            current_input = self.board_to_vector(backgammon.board)
            # pass the current board (board before this move is about to happen)
            # to the network
            current_output = self.neural_network.get_network_output(current_input)

            self.neural_network.back_prop(current_output, next_output)

        return best_board

    def compute_utility(self, network_output):
        """ Takes output from the neural net and returns the
            expected utility of a board winning the game. """
        # the net returns the array = [white_odds, black_odds]
        
        # check if this player is white, and say no to racism!
        # maybe only use the one output for the specific color
        if self.color == Board.WHITE:
            # simple average of the probabilities
            # one might also apply Bayes' Rule
            utility = (network_output[0] + (1 - network_output[1])) / 2
        # if this player is black
        else:
            utility = (network_output[1] + (1 - network_output[0])) / 2

        return utility

    def lost(self, final_board):
        if self.learning_mode:
            if self.color == Board.WHITE:
                # contains the actual reward values
                # if white has lost, odds are 0.0 and black has won
                actual_output = [0.0, 1.0]
            else:
                actual_output = [1.0, 0.0]

            # this is the board that led to the loss/win
            current_input = self.board_to_vector(final_board)
            current_output = self.neural_network.get_network_output(current_input)
            # backprop the final board
            self.neural_network.back_prop(current_output, actual_output)
            # reset e_traces after each game ended
            self.neural_network.reset_all_traces()

    def won(self, final_board):
        if self.learning_mode:
            if self.color == Board.WHITE:
                # contains the actual reward values
                # if white won, odds are 1.0 and black has lost
                actual_output = [1.0, 0.0]
            else:
                actual_output = [0.0, 1.0]

            # this is the board that led to the loss/win
            current_input = self.board_to_vector(final_board)
            current_output = self.neural_network.get_network_output(current_input)
            # backprop the final board
            self.neural_network.back_prop(current_output, actual_output)
            # reset e_traces after each game ended
            self.neural_network.reset_all_traces()
            # increment number of training games
            self.neural_network.update_counter()

    def board_to_vector(self, board_obj):
        """ Creates a 198-dimensional input vector
            of the current gammon situation. """
        current_player = self.color
        
        board = board_obj.board
        colors = board_obj.colors
        bar = [board_obj.get_bar(Board.WHITE), board_obj.get_bar(Board.BLACK)]
        off = [board_obj.get_off(Board.WHITE), board_obj.get_off(Board.BLACK)]
        
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

        return np.array(vector)


class RandomPlayer(Player):
    """ A random player. """
    
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

    def choose_move(self, backgammon):
        """ Chooses a random board from all possible boards. """
        # get a list of all possible moves
        all_boards = BoardFactory.generate_all_boards(backgammon.current_player,\
                                            backgammon.dice, backgammon.board)
        
        # pick a random move
        random_board = random.choice(all_boards)
        return random_board

    def lost(self, board):
        pass
    
    def won(self, board):
        pass
