from board import Board, Dice
from player import Player, RandomPlayer
from neural_net import NeuralNetwork

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
        # the neural network used by the players, both players share the same net
        self.neural_network = NeuralNetwork(198, 40, 2)
        # color of the current player
        self.current_player = None
        self.winner = None
        # list of players
        # learning_mode is True per default, pass False as second parameter
        # to Player() to disable network training
        self.players = [Player('white', self.neural_network), \
                        Player('black', self.neural_network)]
        self.reset()
    
    def save_network(self):
        """ Saves the Neural Network of this Backgammon instance to a file. """
        self.neural_network.save_network()

    def restore_network(self):
        self.neural_network.restore_network()
    
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
                self.get_move(player)
                if self.board.is_gameover():
                    break

        # check whether a player has all checkers beared off
        # and return it as winner. 
        if self.board.get_off(Board.WHITE) == 15:
            for player in self.players:
                if player.color == Board.WHITE:
                    player.won(self.board)
                    self.winner = player
                else:
                    player.lost(self.board)
        elif self.board.get_off(Board.BLACK) == 15:
            for player in self.players:
                if player.color == Board.BLACK:
                    player.won(self.board)
                    self.winner = player
                else:
                    player.lost(self.board)
        
        return self.winner
        
    def get_move(self, player):
        """ Receives a board from the player and applies the move. """
        new_board = player.choose_move(self)
        self.apply_move(new_board)

    def apply_move(self, new_board):
        """ Updates the board according to chosen move
            and initiates the next turn. """
        # update board according to chosen board
        self.board = new_board
        #print self.board
        # roll new dice
        self.dice.roll()
        # set the opponent as current_player
        self.current_player = Board.get_opponent(self.current_player)
        #print "\nIt's {0}'s turn, with the roll: {1} ".format("white" if self.current_player == 0 else "black", self.dice)


if __name__ == '__main__':

    bg = Backgammon()
    #bg.restore_network()
    
    for i in range(1000):
        bg.run()
        print "Game: {}, {} wins.".format(i + 1, bg.winner.identity)
        bg.reset()

    bg.save_network()
    #nn = NeuralNetwork(198, [40], 2)
    #print nn.inspect_layer('output')

