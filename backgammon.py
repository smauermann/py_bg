from board import Board, Dice
from player import Player, RandomPlayer
from neural_net import NeuralNetwork


class Backgammon(object):
    """ This class wraps all of the backgammon functionality. Basically,
        the use model for this class is to build a new Backgammon with
        two players, execute backgammon.run(), which runs the game, and
        the call backgammon.reset(), backgammon.run() if you
        want to play again. """
    def __init__(self, training_mode, restore_net):
        # the dice
        self.dice = Dice()
        # internal board, which is the state before the current move
        self.board = Board()
        
        # the neural network used by the players, both players share the same net
        if restore_net == False:
            self.neural_network = NeuralNetwork(198, 40, 2, restore_from_file=False)
        elif restore_net == True:
            self.neural_network = NeuralNetwork(0, 0, 0, restore_from_file=True)
        
        # list of players
        if training_mode:
            self.players = [Player('white', self.neural_network, learning_mode=True), \
                            Player('black', self.neural_network, learning_mode=True)]
        # let white play against RandomPlayer black for evaluating performance
        elif not training_mode:
            self.players = [Player('white', self.neural_network, learning_mode=False), \
                            RandomPlayer('black')]
        
        # the current player of this instance
        self.current_player = None
        # winner of this game
        self.winner = None

        self.reset()
    
    def save_network(self):
        """ Saves the Neural Network of this Backgammon instance to a file. """
        self.neural_network.save_network()
    
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
        # because white is first in the initial list
        if self.current_player == 1:
            self.players = list(reversed(self.players))
                            
    def run(self):
        """ Runs a game of backgammon, and does not return until the game
            is over. Returns the player who won the game. """
        while not self.board.is_gameover():
            # request players to choose a board
            self.get_move(self.players[0])
            if self.board.is_gameover():
                break

            self.get_move(self.players[1])
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
        #print player.color
        new_board = player.choose_move(self)
        self.apply_move(new_board)

    def apply_move(self, new_board):
        """ Updates the board according to chosen move
            and initiates the next turn. """
        # update board according to chosen board
        self.board = new_board
        # roll new dice
        self.dice.roll()
        # update player
        self.current_player = Board.get_opponent(self.current_player)

if __name__ == '__main__':
    
    bg = Backgammon(training_mode=False, restore_net=True)
    wins = [0,0]
    
    for i in range(100):
        bg.run()
        print "Game {}, won by {}".format(i + 1, bg.winner.identity)
        if bg.winner.color == 0:
            wins[0] += 1
        else:
            wins[1] += 1
        bg.reset()
    
    #bg.save_network()
 
    print wins

    

