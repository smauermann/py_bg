# TODO: figure out how to efficiently batch import from a different directory
from board import Board, Dice
from bgexceptions import BackgammonException, IllegalMoveException


class BarMove(object):
    """ Methods for removing checkers from the Bar. """
    def __init__(self, player, die, board, end):
        self.player = player
        self.other_player = Board.get_opponent(player)
        self.die = die
        self.board = board.copy_board()
        
        # check if end is on the board
        if not Board.on_board(end):
            raise IllegalMoveException("End is not on the Board!")
        else:
            self.end = end

    def make_move(self):
        """ Validates the movement given the provided board situation. """
        if not (self.die == abs(Board.get_home(self.other_player) - self.end)):
            raise IllegalMoveException("Off-Bar not possible: \
                                Die cannot be used to perform this movement!")

        # check if bar is empty and raise error if yes
        if self.board.get_bar(self.player) == 0:
            raise IllegalMoveException("Off-Bar not possible: \
                                        No checkers on the Bar!")

        # check if end position is in the homeboard of the other player
        # if not raise Error, checkers leaving the bar must be placed in the
        # homeboard of the opponent (your starting quadrant)
        if not Board.in_home_board(self.other_player, self.end):
            raise IllegalMoveException("Off-Bar not possible: \
                            Checkers must go into the opponents home board!")

        # check if there is more than one opponent checker at end position
        # and raise error when yes 
        if self.board.get_checkers(self.end, self.other_player) > 1:
            raise IllegalMoveException("Off-Bar not possible: \
                                        Location occupied by other player")

        # now make the movement:
        # first kick enemy checkers onto the bar if there are any
        if self.board.get_checkers(self.end, self.other_player) == 1:
            self.board.remove_from_location(self.other_player, self.end)
            self.board.move_to_bar(self.other_player)

        self.board.remove_from_bar(self.player)
        self.board.move_to_location(self.player, self.end)

        return self.board

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
        return not self == other


class BearOffMove(object):
    """ Methods for bearing off a checker. """
    # rules for bear-off:
    # - all checkers must be in the homeboard of a color (end area)
    # - endboard numbered 1...6 with 1 closest to end of gameboard
    #   and 6 closest to bar
    # - roll a 1, bear off checker from 1
    # - roll a 6, bear off checker from 6
    # - if no checker at rolled position in homeboard, make legal move
    #   within the homeboard
    # - when number is rolled that is higher than the highest point with checkers,
    #   bear off next highest checker
    
    def __init__(self, player, die, board, start):
        self.player = player
        self.die = die
        self.board = board.copy_board()
        
        if not Board.on_board(start):
            raise IllegalMoveException("Start is not on the board!")
        else:
            self.start = start

    def can_use(self):
        """ Returns whether or not this movement can use the given
            dice roll to perform its movement. """     
        if self.die == abs(self.start - Board.get_home(self.player)):
            return True
        # if die roll is higher than highest checkers in homeboard,
        # the highest checker can be removed
        # this can be done only once
        elif self.die >= abs(self.start - Board.get_home(self.player)):
            return True
        else:
            return False

    def make_move(self):
        """ Validates this movement given the provided
            board situation. """
        if not self.can_use():
            raise IllegalMoveException("Bear-off not possible: \
                                        Cannot use dice for this movement!")
            
        if self.board.get_checkers(self.start, self.player) == 0:
            raise IllegalMoveException("Bear-off not possible: \
                                        No checkers at location!")

        if self.board.get_bar(self.player) > 0:
            raise IllegalMoveException("Bear-off not possible: \
                                    Checkers from the bar must be moved first!")

        # loop over whole board and check whether all checkers are in the homeboard
        # if not all checkers are in the homeboard, bear-off is NOT allowed
        for i in range(Board.NUM_POINTS):
            if (self.board.get_checkers(i, self.player) > 0) and \
                                    (not Board.in_home_board(self.player, i)):
                raise IllegalMoveException("Bear-off not possible: \
                                    Still checkers outside of the home board!")

        # now make the move
        self.board.remove_from_location(self.player, self.start)
        self.board.move_off(self.player)
        
        return self.board

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
        return not self == other


class NormalMove(object):
    """ Methods for a normal movement. """

    def __init__(self, player, die, board, start, end):
        self.player = player
        self.other_player = Board.get_opponent(player)
        self.die = die
        self.board = board.copy_board()

        if (not Board.on_board(start)) or (not Board.on_board(end)):
            raise IllegalMoveException("Start or end is not on the board!")
        else:
            self.start = start
            self.end = end

    def make_move(self):
        """ Validates this movement given the provided
            board situation. """
        if not (self.die == abs(self.start - self.end)):
            #print "make_move2"
            raise IllegalMoveException("Normal move not possible: \
                                            Cannot use die for this movement!")
            
        if self.start == self.end:
            raise IllegalMoveException("Normal move not possible: \
                                Start and end must not be the same position!")
            
        if abs(self.start - self.end) > Dice.MAX_VALUE:
            raise IllegalMoveException("Normal move not possible: \
                                        Move distance larger than 6!")
            
        if self.board.get_bar(self.player) > 0:
            raise IllegalMoveException("Normal move not possible:: \
                                    Checkers from the bar must be moved first!")

        if self.board.get_checkers(self.start, self.player) == 0:
            raise IllegalMoveException("Normal move not possible: \
                                        No checkers at the start location!")
            
        if ((self.start > self.end) and (Board.get_direction(self.player) > 0) or
            (self.start < self.end) and (Board.get_direction(self.player) < 0)):
            raise IllegalMoveException("Normal move not possible: \
                                        Backward movements are not allowed!")
            
        if self.board.get_checkers(self.end, self.other_player) > 1:
            raise IllegalMoveException("Normal move not possible: \
                        End location already occupied by opponent checkers!")

        # now perform movement:
        # check first whether the move bumps the opponent
        if self.board.get_checkers(self.end, self.other_player) == 1:
            self.board.remove_from_location(self.other_player, self.end)
            self.board.move_to_bar(self.other_player)

        # now perform the move
        self.board.remove_from_location(self.player, self.start)
        self.board.move_to_location(self.player, self.end)
        
        return self.board

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
        return not self == other


class BoardFactory(object):
    """ Generates all distinct boards for the given gammon situation
        and the provided dice roll. """

    @classmethod
    def generate_all_boards(cls, player, dice, board):
        """ Function takes an initial backgammon situation (player, dice, board),
            and generates all possible moves and the resulting boards.
            Returns a list of all possible moves from all dice combinations. """
        
        # check if dice are doubles:
        if dice.is_doubles():
            all_dice_combinations = [[dice.get_die1()] * 4]
        else:
            all_dice_combinations = []
            # make all dice combinations by sorting and put them in the list
            all_dice_combinations.append(sorted(dice.get_dice(), reverse=True))
            all_dice_combinations.append(sorted(dice.get_dice(), reverse=False))

        # all_boards will contain all possible boards in the end
        all_boards = []

        # loop over the two dice combinations
        # if doubles, all_dice_combinations contains list of 4 numbers
        for all_dice in all_dice_combinations:
            # set boards to the starting board
            boards = [board]
            # loop over die in one dice combination
            for die in all_dice:
                
                # compute all boards for die on all previously generated boards
                # or the initial board of this turn
                computed_boards = cls.compute_boards(player, die, boards)
                # check if there were any boards created and set these as
                # the starting boards for the next moves using the next die
                if computed_boards is not None:
                    boards = computed_boards
                
            # store all generated boards in all_boards
            # now repeat this process for the next dice combination
            all_boards.append(boards)

        # flatten removes dimensions --> instead of list of lists of lists,
        # this will return a list with all possible moves (ie boards) 
        lst = [item for sublist in all_boards for item in sublist]
        # transform list to set to get rid of duplicate boards
        # boards entering a set get key depending on their hash value and
        # identical boards will have identical hashes and removed from the set
        result = set(lst)
        # now transfrom back into list, because sets are unordered and cant
        # be accessed by keys directly
        return list(result)

    @staticmethod
    def compute_boards(player, die, boards):
        """ Function takes a starting board and replaces it with all possible
            boards. Finally returns a list of all possible boards,
            or the starting board(s) if no boards could be created. """
        # boards is a list containing starting boards
        # loop over the boards in boards list
        for i, brd in enumerate(boards):
            new_boards = []
            # check if bar move must be made
            if brd.get_bar(player) > 0:
                try:
                    # make a bar move, and return the resulting board
                    destination = Board.get_home(Board.get_opponent(player)) + \
                                            die * Board.get_direction(player)
                    #print "bar dest: ", destination + 1
                    bar_move = BarMove(player, die, brd, destination)
                    tmp_board = bar_move.make_move()
                    #print "BarMove"
                except IllegalMoveException:
                    tmp_board = None
                # make sure a bar move was legal and a new board was generated
                # if yes, append new_boards
                if tmp_board is not None:
                    new_boards.append(tmp_board)
            
            # try normal or bear-off moves:
            else:   
                # loop over whole board
                for pos in range(Board.NUM_POINTS):
                    # pos occupied by player
                    if brd.get_checkers(pos, player) > 0:
                        try:
                            # try to make a normal move and return resulting board
                            destination = pos + (die * Board.get_direction(player))
                            normal_move = NormalMove(player, die, brd, pos, destination)
                            tmp_board = normal_move.make_move()
                            #print "NormalMove"
                        except IllegalMoveException, e:
                            tmp_board = None
                        # make sure normal move was legal and a new board was generated
                        # if yes, append new_boards
                        if tmp_board is not None:
                            new_boards.append(tmp_board)
                # loop over players homeboard, ie the target quadrant
                # of a player (white: 23...18 or black: 0...5)
                for pos in range(Board.get_home(player) - Board.get_direction(player),\
                    Board.get_home(player) - (7 * Board.get_direction(player)),\
                     - Board.get_direction(player)):
                        try:
                            # try to bear off checkers and return resulting board
                            bear_off_move = BearOffMove(player, die, brd, pos)
                            tmp_board = bear_off_move.make_move()
                            #print "BearOffMove"
                        except IllegalMoveException, e:
                            tmp_board = None
                        # make sure bearoff move was legal and a new board was generated
                        # if yes, append new_boards
                        if tmp_board is not None:
                            new_boards.append(tmp_board)
            
            # check if new boards were created
            # and if yes, replace each starting board in boards with
            # a list of possible boards originating from each starting board
            if len(new_boards) > 0:
                boards[i] = new_boards
            # lets say three boards go in and only one of these can generate a
            # new board. boards would look something like [b0, b1, [b31,..., b3n]]
            # this will give an error when trying to iterate b0 or b1
            # so instead put the initial board in a list and iteration works again
            elif len(new_boards) == 0:
                boards[i] = [boards[i]]

        # check if any new boards were created:
        # if yes flatten and return
        if len(new_boards) >= 0:
            # flatten boards, takes sublist elements and puts them a new list
            # and returns a list containing all possible boards
            #print boards
            return [item for sublist in boards for item in sublist]
        # if no new boards were created:
        # return the starting boards
        else:
            return None
    
