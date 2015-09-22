# The TD(lambda) Neural Net
import numpy as np
import random
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
    def __init__(self, size):
        self.size = size
        self.output_values = None
        
    def get_input(self, input_values):
        """ Get input from preceeding layer or from the environment.
            Latter in case of input layer. """
        self.output_values = np.array(input_values)

    # overwrites compute_output() from BaseLayer, since no calculation
    # is needed and the values of the input vector are directly returned
    def compute_output(self):
        """ Return an array of the inputs. """
        return self.output_values

    def __repr__(self):
        return "Input Layer, size {}".format(self.size)


class BaseLayer(object):
    """ Basis layer which implements functions shared
        by hidden layers and output layer of the neural network. """
    
    # the range for randomly initializing the weights
    RANGE_WEIGHTS = [-1, 1]

    def __init__(self, size):
        self.size = size
        self.layer_type = None
        self.output_values = None
        self.weights = None
        self.prior_layer = None
        self.next_layer = None
        self.e_traces = None

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
        # get the output from prior layer
        input_values = self.get_input()
        # compute the dot product with input_values, squash it through sigmoid()
        # and put the output in the output array
        input_dot_weights = np.dot(self.weights, input_values)
        # map() applies provided function to all individual
        # elements of the provided list of inputs
        self.output_values = np.array(map(self.sigmoid, input_dot_weights))
        return self.output_values

    def reset_e_traces(self):
        if self.layer_type == 'hidden':
            self.e_traces = np.zeros((self.size, self.prior_layer.size, self.next_layer.size))
        else:
            self.e_traces = np.zeros_like(self.weights)

    def __str__(self):
        return self.__repr__()


class HiddenLayer(BaseLayer):
    """ Class which represents a hidden layer of the network. """ 
    def __init__(self, size):
        super(HiddenLayer, self).__init__(size)
        self.layer_type = 'hidden'
    
    def __repr__(self):
        return "Hidden Layer, size {}".format(self.size)
     

class OutputLayer(BaseLayer):
    """ Class which represents the output layer of the network. """
    def __init__(self, size):
        super(OutputLayer, self).__init__(size)
        self.layer_type = 'output'

    def __repr__(self):
        return "Output Layer, size {}".format(self.size)


class NeuralNetwork(object):
    """ Wraps the single layers and constructs a neural network. """
    # learning rate alpha
    ALPHA = 0.1
    # alpha splitting can be used as indicated by the java version
    # beta applies to output layer weights while alpha applies to hidden weights
    BETA = ALPHA
    # trace decay parameter, discounts the effects of actions far back in time
    LAMBDA = 0.7

    def __init__(self, input_size, hidden_sizes, output_size,\
                    restore_from_file=None):
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
            # a dict of all layers is convenient for saving its state
            self.network_layers = {}
            
            # build layers and connect them
            self.build_layers()
        
        # check if string was provided for restoring net from file
        elif type(restore_from_file) == str:
            # try to load file
            try:
                saved_things = self.restore_network(restore_from_file)
            # when file doesnt exist or wrong filename provided
            # prompt for correct filename
            except IOError:
                filename = raw_input("Enter correct filename \
                                        (default = neural_net.pkl): ")
            
            for thing in saved_things:
                if type(thing) == dict:
                    self.network_layers = thing
                elif type(thing) == list:
                    self.hidden_sizes = thing

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

        # add connected layers to the interal dict network_layers
        self.network_layers['input'] = tmp_layers[0]
        self.network_layers['output'] = tmp_layers[-1]
        if self.hidden_sizes:
            for i in range(1, len(tmp_layers) - 1):    
                self.network_layers['hidden' + str(i)] = tmp_layers[i]
    
    def connect_layers(self, layer1, layer2, weights=None):
        """ Connects the layers of the network, sets weights (either random or
            to provided values) and initializes eligibility traces. """
        # set the previous layer for layer2
        layer2.prior_layer = layer1
        layer1.next_layer = layer2
        # check if weights were provided
        if weights is None:
            # determine number of weights and initialize the weight array
            layer2.weights = np.zeros((layer2.size, layer1.size))
            layer2.randomize_weights()
        else:
            layer2.weights = weights

        layer2.reset_e_traces()

    def get_network_output(self, input_values):
        """ Computes the output of the network
            given the provided input. """
        # feed the network with input
        self.network_layers['input'].get_input(input_values)
        # return the computed output
        return self.network_layers['output'].compute_output()

    @staticmethod
    def compute_gradient(layer):
        """ Computes a gradient of the form: unit.output * (1 - unit.output). """
        # layer_output is an array 
        return layer.output_values * (1 - layer.output_values)
    
    def back_prop(self):#, current_input, current_output, next_output):
        """ Computes eligibility traces and backpropagates an error back
            through the network. """ 
        output_layer = self.network_layers['output']
        
        # extract the hidden layers from network_layers dict
        # figure out how to sort hidden layers when more than one!
        hidden_layer = self.network_layers['hidden1']
        #for key, layer in self.network_layers.items():
            #if key.startswith('hidden'):
                #hidden_layers.append(layer)
    
        # compute eligibility traces for output layer (ie between hidden and output)
        # shape of e_traces array must be identical to corresponding weight array
        output_layer.e_traces = self.LAMBDA * output_layer.e_traces \
                                # cross product between hidden output and output layer
                                # resulting array contains product of each
                                # hidden unit and each output unit:
                                # h1*y1, h1*y2
                                # h2*y1, h2*y2
                                # h3*y1, h3*y2 ... shape will be (40x2)
                                + np.dot(hidden_layer.output_values, self.compute_gradient(output_layer).T)

        # compute e_traces for hidden layer (ie between input and hidden layer)
        # lambda * e + (gradient(y) x Wout x grad(hidden) x input)
        hidden_layer.e_traces = self.LAMBDA * hidden_layer.e_traces \
                                + np.dot()

        # the error between next and current network output
        # array contains (error y1, error y2)
        output_error = (next_output - current_output)

        # update output layer weights (ie between hidden and output)
        # learning rate BETA used here
        # first column of e_trace * output_error[0] --> applies to output unit 1
        # second colum of e_trace * output_error[1] --> applies to output unit 2
        # loop over output layers
        for i in range(output_layer.size):
            output_layer.weights[i,:] += self.BETA * output_error[i] * output_layer.e_traces[i]


    def save_current_network(self, filename='neural_net.pkl'):
        """ Save the current state of the network to file. """
        # save network_layers dict and the number of hidden units
        # put both in a list and loop over it to save both objects
        things_to_save = [self.network_layers, self.hidden_sizes]
        
        with open(filename, 'wb') as fhandle:
            pickle.dump(len(things_to_save), fhandle)
            for thing in things_to_save:
                pickle.dump(thing, fhandle)

    @staticmethod
    def restore_network(filename='neural_net.pkl'):
        """ Restores the settings of the neural network
            from the provided file. """
        # restoring works also after restarting macbook
        # thus it looks pretty robust 
        with open(filename, 'rb') as fhandle:
            while True:
                try:
                    yield pickle.load(fhandle)
                except EOFError:
                    break

    


nn = NeuralNetwork(100, [40], 2)
nn.save_current_network()
print nn.get_network_output([1,2,3,4,5]*20)


# inpoot = InputLayer(100)
# hidden1 = HiddenLayer(80)
# hidden2 = HiddenLayer(20)
# output = OutputLayer(4)

# hidden1.connect_with(inpoot)
# hidden2.connect_with(hidden1)
# output.connect_with(hidden2)

# inpoot.get_input([1,2,3,4,5]*20)

# print output.compute_output()

