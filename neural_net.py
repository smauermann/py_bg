import numpy as np
import random
import sys
# we need to save the network between serial trainings: we use pickle for that
# pickling transforms an object into a bytestream of ASCII signs, which can be
# written to a file
# unpickling does the opposite, retrieves an object from a file
try:
   # cPickle is implemented in C and thus faster as pickle
   import cPickle as pickle
except:
   import pickle 


class InputLayer(object):
    """ Class which represents the input layer of the network. """
    
    def __init__(self, size, bias_unit=False):
        self.size = size
        self.output_values = None
        self.layer_type = 'input'
        if bias_unit:
            self.bias = np.array([1.0])
        else:
            self.bias = None
    
    def get_input(self, input_values):
        """ Get input from preceeding layer or from the environment.
            Latter in case of input layer. """
        try:
            inputs = np.array(input_values)
            self.output_values = inputs
        except ValueError:
            print "Input does not match input layer size!"

    def compute_output(self):
        """ Return an array of the inputs. """
        # if bias is True, stack the bias unit on top of outputs
        if self.bias is not None:
            self.output_values = np.hstack((self.bias, self.output_values))

        return self.output_values

    def __repr__(self):
        return "Input Layer, size {}".format(self.size)


class BaseLayer(object):
    """ Basis layer which implements functions shared
        by hidden layers and output layer of the neural network. """
    
    # the range for randomly initializing the weights
    RANGE_WEIGHTS = [-1, 1]

    def __init__(self, size, bias_unit=False):
        self.size = size
        self.layer_type = None
        self.output_values = None
        self.weights = None
        self.prior_layer = None
        self.next_layer = None
        self.e_traces = None
        if bias_unit and self.layer_type != 'output':
            self.bias = np.array([1.0])
        else:
            self.bias = None

    def randomize_weights(self):
        """ Assign random values to all weights. """
        for row in range(self.weights.shape[0]):
            for col in range(self.weights.shape[1]):
                self.weights[row, col] = ((self.RANGE_WEIGHTS[1] - self.RANGE_WEIGHTS[0])\
                                            * np.random.random_sample()\
                                            + self.RANGE_WEIGHTS[0])

    def sigmoid(self, x):
        return (1 / (1 + np.exp(-x)))

    def compute_output(self):
        """ Returns the output of a layer and caches the last computed value. """
        # get the output from prior layer
        input_values = self.prior_layer.compute_output()
        # compute the dot product with input_values, squash it through sigmoid()
        # and put the output in the output array
        weights_x_input = np.dot(self.weights, input_values)
        # map() applies provided function to all individual
        # elements of the provided list of inputs
        self.output_values = np.array(map(self.sigmoid, weights_x_input))
        # if bias is True, stack the bias unit on top of outputs
        if self.bias is not None:
            self.output_values = np.hstack((self.bias, self.output_values))
        
        return self.output_values

    def reset_e_traces(self):
        if self.layer_type == 'hidden':
            # 3-dimensional array, think of a sandwich of two hidden weights
            # arrays stacked
            self.e_traces = np.zeros((self.size, self.prior_layer.size, \
                                                       self.next_layer.size))
        elif self.layer_type == 'output':
            self.e_traces = np.zeros_like(self.weights)

    def __str__(self):
        return self.__repr__()


class HiddenLayer(BaseLayer):
    """ Class which represents a hidden layer of the network. """ 
    def __init__(self, size, bias_unit):
        super(HiddenLayer, self).__init__(size, bias_unit)
        self.layer_type = 'hidden'
        
    def __repr__(self):
        return "Hidden Layer, size {}. Weights: {}".format(self.size, self.weights.shape)
     

class OutputLayer(BaseLayer):
    """ Class which represents the output layer of the network. """
    def __init__(self, size):
        super(OutputLayer, self).__init__(size)
        self.layer_type = 'output'

    def __repr__(self):
        return "Output Layer, size {}. Weights: {}".format(self.size, self.weights.shape)


class NeuralNetwork(object):
    """ Wraps the single layers and constructs a neural network. """
    # learning rate alpha
    ALPHA = 0.1
    # alpha splitting can be used as indicated by the java version
    # beta applies to output layer weights while alpha applies to hidden weights
    BETA = ALPHA
    # trace decay parameter, discounts the effects of actions far back in time
    LAMBDA = 0.7
    # switch for input and hidden bias units
    BIAS_UNITS = True
    # filename, where weights and sizes are saved
    SAVE_FILE = 'neural_net.pkl'
    
    def __init__(self, input_size=None, hidden_size=None, output_size=None, \
                                                    restore_from_file=False):
        if not restore_from_file:
            # initialize size and number of layers
            self.input_size = input_size
            self.output_size = output_size
            self.hidden_size = hidden_size
            # number of games the network was trained
            self.num_games = 0
            # dict containing all the network's layers
            # naming convention will use the keys: input, hidden, output
            self.layer_dict = {}
            
            # build layers, connect them, set weights, set eligibility traces
            self.initialize_layers()
        
        elif restore_from_file: 
            # try to load file
            try:
                saved_things = self.restore_network()
            # when file doesnt exist or wrong filename provided
            # prompt for correct filename
            except IOError, e:
                print "Neural net could not be restored: ", e
                sys.exit()
            
            # dict containing all the network's layers
            # naming convention will use the keys: input, hidden, output
            self.layer_dict = {}
            
            # restore layer sizes 
            self.num_games = saved_things['num_games']
            self.input_size = saved_things['input_size']
            self.hidden_size = saved_things['hidden_size']
            self.output_size = saved_things['output_size']
            hidden_weights = saved_things['hidden_weights']
            output_weights = saved_things['output_weights']

            self.initialize_layers(hidden_weights, output_weights)
    
    def initialize_layers(self, hidden_weights=None, output_weights=None):
        """ Constructs network layers with provided sizes. """
        # check if biases are neede
        if self.BIAS_UNITS:
            bias_unit = True
        else:
            bias_unit = False
        
        # create input layer and add to list
        input_layer = InputLayer(self.input_size, bias_unit)
        
        # create hidden layer and add to list
        hidden_layer = HiddenLayer(self.hidden_size, bias_unit)
        
        # create output layer and add to list 
        output_layer = OutputLayer(self.output_size)
        
        # connect the layers, also initializes weights
        self.connect_layers(input_layer, hidden_layer, hidden_weights)
        self.connect_layers(hidden_layer, output_layer, output_weights)

        # add connected layers to the interal dict layer_dict
        self.layer_dict['input'] = input_layer
        self.layer_dict['hidden'] = hidden_layer
        self.layer_dict['output'] = output_layer
        
        # initialize eligibility traces
        self.reset_all_traces()
    
    def update_counter(self):
        self.num_games += 1

    def reset_all_traces(self):
        """ Resets the eligibility trace arrays of all layers to np.zeros-arrays. """
        # dont set e_traces for input layer, it has none
        for key, layer in self.layer_dict.items():            
            if key != 'input':
                layer.reset_e_traces()

    def connect_layers(self, layer1, layer2, weights):
        """ Connects the layers of the network, sets weights to random values. """
        if weights is None:
            # set the previous layer for layer2
            layer2.prior_layer = layer1
            layer1.next_layer = layer2
            
            # check if bias units are required
            if self.BIAS_UNITS:
                layer2.weights = np.zeros((layer2.size, layer1.size + 1))
            else:
                layer2.weights = np.zeros((layer2.size, layer1.size))
            
            layer2.randomize_weights()
        
        # if weights are provided
        elif isinstance(weights, np.ndarray):
            layer2.prior_layer = layer1
            layer1.next_layer = layer2
            layer2.weights = weights
    
    def inspect_layers(self, layer_name=None):
        """ The function returns the requested layer.
            Layers are named as follows:
                * 'input'
                * 'hidden'
                * 'output'. """
        if layer_name == None:
            for key, layer in self.layer_dict:
                print layer
        else:
            print self.layer_dict[layer_name].__dict__

    def get_network_output(self, input_values):
        """ Computes the output of the network
            given the provided input. """
        # feed the network with input
        self.layer_dict['input'].get_input(input_values)
        # return the computed output
        return self.layer_dict['output'].compute_output()

    @staticmethod
    def gradient(value):
        """ Computes gradient via derived sigmoid activation function. """
        gradient = value * (1 - value)
        return gradient

    def back_prop(self, current_output, expected_output):
        """ Computes eligibility traces and backpropagates an error back
            through the network. """ 
        # re-referencing attributes here for less typing later
        input_layer = self.layer_dict['input']
        input_out = input_layer.output_values
        
        hidden_layer = self.layer_dict['hidden']
        hidden_out = hidden_layer.output_values
        hidden_weights = hidden_layer.weights
        hidden_traces = hidden_layer.e_traces
        
        output_layer = self.layer_dict['output']
        output_out = output_layer.output_values
        output_weights = output_layer.weights
        output_traces = output_layer.e_traces
        
        # compute e_traces
        for o in range(self.output_size):
            for h in range(self.hidden_size):
                output_traces[o, h] = self.LAMBDA * output_traces[o, h] \
                                    + self.gradient(output_out[o]) \
                                    * hidden_out[h]
                
                for i in range(self.input_size):
                    hidden_traces[h, i, o] = self.LAMBDA * hidden_traces[h, i, o] \
                                            + self.gradient(output_out[o]) \
                                            * output_weights[o, h] \
                                            * self.gradient(hidden_out[h]) \
                                            * input_out[i]

        # calculate TD error between next and current network output
        error = expected_output - current_output
        
        # update weights
        for o in range(self.output_size): 
            for h in range(self.hidden_size):
                # update output weights
                output_weights[o, h] += self.BETA * error[o] * output_traces[o, h]
                # update hidden weights
                for i in range(self.input_size):
                    hidden_weights[h, i] += self.ALPHA * error[o] * hidden_traces[h, i, o]
        
    def save_network(self):
        """ Save the current state of the network to file. """
        # save weights of hidden and output layer
        things_to_save = {  'num_games': self.num_games, \
                            'input_size': self.layer_dict['input'].size, \
                            'hidden_size': self.layer_dict['hidden'].size, \
                            'hidden_weights': self.layer_dict['hidden'].weights, \
                            'output_size': self.layer_dict['output'].size, \
                            'output_weights': self.layer_dict['output'].weights}
        
        with open(self.SAVE_FILE, 'wb') as fhandle:
            pickle.dump(things_to_save, fhandle)
            
    def restore_network(self):
        """ Restores the settings of the neural network
            from the provided file. """
        with open(self.SAVE_FILE, 'rb') as fhandle:
            restored_things = pickle.load(fhandle)
        return restored_things
 
