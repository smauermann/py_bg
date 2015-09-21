# The TD(lambda) Neural Net
import numpy as np
import random
# we need to save the network between serial trainings: we use pickle for that
# pickling transforms an object into a bytestream of ASCII signs, which can be
# written to a file
# unpickling does the opposite, retrieves an object from a file
try:
   import cPickle as pickle # cPickle is implemented in C and thus faster as pickle
except:
   import pickle 


class BaseLayer(object):
    """ Basis layer which implements functions shared
        by several other layers of the neural network. """
    
    # the range for randomly initializing the weights
    RANGE_WEIGHTS = [-1, 1]

    def __init__(self, size):
        self.size = size
        self.weights = None
        self.prior_layer = None
        self.output_values = None
    
    def randomize_weights(self):
        """ Assign random values to all weights. """
        for row in range(self.weights.shape[0]):
            for col in range(self.weights.shape[1]):
                self.weights[row, col] = ((self.RANGE_WEIGHTS[1] - self.RANGE_WEIGHTS[0])\
                                            * np.random.random_sample()\
                                            + self.RANGE_WEIGHTS[0])

    def sigmoid(self, x):
        return (1 / (1 + np.exp(-x)))

    def get_input(self):
        """ Gets the output from the previous layer. """
        return self.prior_layer.compute_output()

    def compute_output(self):
        """ Returns the output of the hidden unit. """
        # loop over all rows of the weights,
        # compute the dot product with input_values, squash it through sigmoid()
        # and put the output in the output array
        # initialize value array of the layer with zeros
        self.output_values = np.zeros(self.size)
        input_values = self.get_input()
      
        input_dot_weights = np.dot(self.weights, input_values)
        self.output_values = map(self.sigmoid, input_dot_weights)
        return self.output_values

    def __str__(self):
        return self.__repr__()


class InputLayer(BaseLayer):
    """ Class which represents the input layer of the network. """
    def __init__(self, size):
        super(InputLayer, self).__init__(size)
        
    def get_input(self, input_values):
        """ Get input from preceeding layer or from the environment.
            Latter in case of input layer. """
        self.output_values = np.array(input_values)

    def compute_output(self):
        """ Return an array of the inputs. """
        return self.output_values

    def __repr__(self):
        return "Input Layer, size {}".format(self.size)


class HiddenLayer(BaseLayer):
    """ Class which represents a hidden layer of the network. """ 
    def __init__(self, size):
        super(HiddenLayer, self).__init__(size)
    
    def __repr__(self):
        return "Hidden Layer, size {}".format(self.size)
     

class OutputLayer(BaseLayer):
    """ Class which represents the output layer of the network. """
    def __init__(self, size):
        super(OutputLayer, self).__init__(size)
    
    def __repr__(self):
        return "Output Layer, size {}".format(self.size)


class NeuralNetwork(object):
    """ Wraps the single layers and constructs a neural network. """
    # make a list with all the layers of the net
    # for feed forward propagation:
    # call compute_output() of the output layer
    def __init__(self, input_size, hidden_sizes, output_size, restore_from_file=None):
        if restore_from_file == None:
            # initialize size and number of layers by passing a list
            # hidden layers parameters are passed as list
            self.input_size = input_size
            self.output_size = output_size

            self.hidden_sizes = []
            for i in hidden_sizes:
                self.hidden_sizes.append(i)
                
            # dict containing all the network's layers
            # naming convention will use the keys: input, hidden1 ...hiddenN, output
            self.network_layers = {}
            
            # build layers and connect them
            self.build_layers()
        elif type(restore_from_file) == str:
            try:
                self.network_layers = self.restore_network(restore_from_file)
            except IOError:
                filename = raw_input("Enter correct filname (default = neural_net.pkl: ")
                self.network_layers = self.restore_network(filename)

    def build_layers(self):
        """ Constructs network layers with provided sizes. """
        tmp_layers = []
        # create input layer and add to list
        input_layer = InputLayer(self.input_size)
        tmp_layers.append(input_layer)
        
        # create hidden layers and add to list
        if self.hidden_sizes:
            for i, layer_size in enumerate(self.hidden_sizes):
                hidden_layer = HiddenLayer(layer_size)
                tmp_layers.append(hidden_layer)
        
        # create output layer and add to list 
        output_layer = OutputLayer(self.output_size)
        tmp_layers.append(output_layer)
        
        # connect the layers
        for i in range(len(tmp_layers) - 1):
            self.connect_layers(tmp_layers[i], tmp_layers[i + 1])

        # add layers connected layers to the interal dict network_layers
        self.network_layers['input'] = tmp_layers[0]
        self.network_layers['output'] = tmp_layers[-1]
        if self.hidden_sizes:
            for i in range(1, len(tmp_layers) - 1):    
                self.network_layers['hidden' + str(i)] = tmp_layers[i]
    
    def connect_layers(self, layer1, layer2, weights=None):
        """ Connects the layers of the network. """
        # set the previous layer for layer2
        layer2.prior_layer = layer1
        
        # check if weights were provided
        if weights is None:
            # determine number of weights and initialize the weight array
            layer2.weights = np.zeros((layer2.size, layer1.size))
            layer2.randomize_weights()
        else:
            layer2.weights = weights

    def get_network_output(self, input_values):
        """ Computes the output of the network
            given the provided input. """
        # feed the network with input
        self.network_layers['input'].get_input(input_values)
        # return the computed output
        return self.network_layers['output'].compute_output()

    def save_current_network(self, filename='neural_net.pkl'):
        """ Save the current state of the network to file. """
        with open(filename, 'wb') as handle:
            pickle.dump(self.network_layers, handle, -1)
    
    @staticmethod
    def restore_network(filename='neural_net.pkl'):
        """ Restores the settings of the neural network
            from the provided file. """
        with open(filename, 'rb') as handle:
            layers = pickle.load(handle)
        return layers

    def compute_gradient(self):
        """ Computes a gradient of the form: unit.output * (1 - unit.output). """
        pass

    def back_prop(self):
        """ Computes eligibility traces and backpropagates an error back
            through the network. """ 
        pass   
    

nn = NeuralNetwork(100, [40, 40], 3)
nn.save_current_network()
print nn.get_network_output([1,2,3,4,5]*20)

nn2 = NeuralNetwork(0, [0], 0, 'neural_net.pkl')
print nn2.get_network_output([1,2,3,4,5]*20)
# inpoot = InputLayer(100)
# hidden1 = HiddenLayer(80)
# hidden2 = HiddenLayer(20)
# output = OutputLayer(4)

# hidden1.connect_with(inpoot)
# hidden2.connect_with(hidden1)
# output.connect_with(hidden2)

# inpoot.get_input([1,2,3,4,5]*20)

# print output.compute_output()

