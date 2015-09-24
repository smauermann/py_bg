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
        self.layer_type = 'input'

    def get_input(self, input_values):
        """ Get input from preceeding layer or from the environment.
            Latter in case of input layer. """
        # give input shape (198,1)
        try:
            self.output_values = np.array(input_values)
        except ValueError:
            print "Input does not match input layer size!"

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
        weights_x_input = np.dot(self.weights, input_values)
        
        # map() applies provided function to all individual
        # elements of the provided list of inputs
        self.output_values = np.array(map(self.sigmoid, weights_x_input))
        
        # add bias output (=1) if hidden layer
        if self.layer_type == 'hidden':
            bias = np.array([1.0])
            self.output_values = np.hstack((bias, self.output_values))
        
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
    def __init__(self, size):
        super(HiddenLayer, self).__init__(size)
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

    def __init__(self, input_size, hidden_size, output_size,\
                    restore_from_file=None):
        if restore_from_file == None:
            # initialize size and number of layers by passing a list
            # hidden layers parameters are passed as list
            self.input_size = input_size
            self.output_size = output_size
            self.hidden_size = hidden_size
           
                
            # dict containing all the network's layers
            # naming convention will use the keys: input, hidden1 ...hiddenN, output
            # a dict of all layers is convenient for saving its state
            self.layer_dict = {}
            # list containing all layers
            self.layer_list = []
            # build layers, connect them, set weights, set eligibility traces
            self.initialize_layers()
        
        # check if string was provided for restoring net from file
        elif type(restore_from_file) == str:
            # perhaps i must put a while True: around try/except block  
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
                    self.layer_dict = thing
                elif type(thing) == list:
                    self.layer_list = thing

    def initialize_layers(self):
        """ Constructs network layers with provided sizes. """
        # create input layer and add to list
        input_layer = InputLayer(self.input_size)
        self.layer_list.append(input_layer)
        
        # create hidden layer and add to list
        hidden_layer = HiddenLayer(self.hidden_size)
        self.layer_list.append(hidden_layer)
        
        # create output layer and add to list 
        output_layer = OutputLayer(self.output_size)
        self.layer_list.append(output_layer)
        
        # connect the layers, also initializes weights
        self.connect_layers(input_layer, hidden_layer)
        self.connect_layers(hidden_layer, output_layer)

        # initialize eligibility traces
        # dont set e_traces for input layer, it has none
        for layer in self.layer_list[1:]:            
            layer.reset_e_traces()

        # add connected layers to the interal dict layer_dict
        self.layer_dict['input'] = self.layer_list[0]
        self.layer_dict['hidden'] = self.layer_list[1]
        self.layer_dict['output'] = self.layer_list[-1]
            
    def connect_layers(self, layer1, layer2, weights=None):
        """ Connects the layers of the network, sets weights (either random or
            to provided values) and initializes eligibility traces. """
        # set the previous layer for layer2
        layer2.prior_layer = layer1
        layer1.next_layer = layer2
        
        # check if weights were provided
        if weights is None:
            # check if prior layer is hidden layer and add weights for bias unit
            if layer1.layer_type != 'input':
                # determine number of weights and initialize the weight array
                layer2.weights = np.zeros((layer2.size, layer1.size + 1))
            else:
                layer2.weights = np.zeros((layer2.size, layer1.size))
            layer2.randomize_weights()
        else:
            layer2.weights = weights

    def inspect_layers(self, layer_name=None):
        """ The function returns the requested layer.
            Layers are named as follows:
                * 'input'
                * 'hidden1' ... 'hiddenN'
                * 'output'. """
        if layer_name == None:
            for layer in self.layer_list:
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
    def compute_gradient(layer):
        """ Computes a gradient of the form: unit.output * (1 - unit.output). """
        # layer_output is an array 
        gradient = layer.output_values * (1 - layer.output_values)
        return gradient

    def back_prop(self, current_input, current_output, expected_output):
        """ Computes eligibility traces and backpropagates an error back
            through the network. """ 
        # layer_list and layer_dict could be used interchangebly, but
        # layer_dict provides more insight because of its named keys
        input_layer = self.layer_dict['input']
        hidden_layer = self.layer_dict['hidden']
        output_layer = self.layer_dict['output']

        # compute gradient for output layer output
        # need to convert 1d array to 2d array for later matrix multiplication
        output_grad = self.compute_gradient(output_layer).reshape(self.output_size, 1)
        hidden_output = hidden_layer.output_values.reshape(self.hidden_size + 1, 1)
        
        # compute eligibility traces for output layer (ie between hidden and output)
        # e_traces matches dimension of weight array for output layer (2x41)
        output_layer.e_traces = self.LAMBDA * output_layer.e_traces \
                                + np.dot(output_grad, hidden_output.T)

        # compute e_traces for hidden layer (ie between input and hidden layer) 
        # these e_traces are 3d, in our case (40x198x2)
        hidden_grad = self.compute_gradient(hidden_layer).reshape(self.hidden_size + 1, 1)
        # need to remove bias output and the corresponding weights
        hidden_grad_no_bias = hidden_grad[1:,:] # 40x1
        hidden_output_no_bias = hidden_output[1:,:] # 40x1
        output_weights_no_bias = output_layer.weights[:,1:] # slice out first colum --> 2x40
        # need to make input 2d array
        input_2d = current_input.reshape(self.input_size, 1) # 198x1
        
        # slice a row:
        # a[0, None, :]
        # slice a column:
        # a[:, 1, None]
        
        # loop over output layer
        for i in range(output_layer.size):
            weight = (output_weights_no_bias[i, None, :])
            # product must have dimension of (40x1)
            product = output_grad[i] * weight.T * hidden_output_no_bias
            # the hidden e_traces array is of shape (40(hidden)x198(input)x2(output))
            hidden_layer.e_traces[:,:,i] = self.LAMBDA \
                                            * hidden_layer.e_traces[:,:,i] \
                                            + np.dot(product, input_2d.T)
        
        # the error between next and current network output
        # shape (2,1)
        output_error = (expected_output - current_output)
        
        # update output layer weights (ie between hidden and output)
        # learning rate BETA used here
        # loop over output layer
        for i in range(output_layer.size):
            product = self.BETA * output_error[i] * output_layer.e_traces[i, None, :]
            output_layer.weights[i, None, :] += product

        # update hidden layer weights, that shit was difficult man
        # here learning rate ALPHA is used
        # loop over output layer
        for i in range(output_layer.size):
            # loop over hidden layer
            for j in range(hidden_layer.size):
                hidden_layer.weights[j,:] += self.ALPHA * output_error[i] \
                                                * hidden_layer.e_traces[j,:,i] 

    def save_network(self, filename='neural_net.pkl'):
        """ Save the current state of the network to file. """
        # save layer_dict dict and the number of hidden units
        # put both in a list and loop over it to save both objects
        things_to_save = [self.layer_dict, self.layer_list]
        
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

# nn = NeuralNetwork(20, 10, 2)
# print nn.get_network_output([1,0,1,0,0]*4)