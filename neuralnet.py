import cPickle
import numpy as np
import matplotlib.pyplot as plt
from genetics import Gene
from nnmath import *
import itertools

import matplotlib.pyplot as plt

def prikaziMatricuKonfuzije(cm):

    plt.figure()
    dimenzija = len(cm)
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Matrica kofuzije')
    plt.colorbar()
    plt.xticks(range(dimenzija), range(1, dimenzija+1))
    plt.yticks(range(dimenzija), range(1, dimenzija+1))


    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j]),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")


    plt.ylabel('Tacne vrednosti')
    plt.xlabel('Predvidjene vrednosti')
    plt.tight_layout()

    plt.show()
    plt.close()
    
class NeuralNet(Gene):
	errors = []
	test_accuracies = []
	train_accuracies = []
	alpha_max = 0.8
	alpha_min = 0.1
	decay_speed = 100

	def __init__(self, args, build=True):
		self.biases = []
		self.weights = []
		self.skeleton = args
		if build:
			self.build(self.skeleton)
			self.encode()

	def build(self, skeleton):
		for i, width in enumerate(skeleton[1:], start=1):
			# Inicijalizacije parametara sa nasumicnim vrednostima
			weights = (2 * np.random.sample((width, skeleton[i-1])) - 1)
			biases = (2 * np.random.sample(width) - 1)
			self.weights.append(weights)
			self.biases.append(biases)

		self.n = len(self.weights) + 1

	def feed_forward(self, activation):
		zs = []
		activations = [activation]
		z = activation

		# Iteriranje kroz skriveni sloj mreze
		for w, b in zip(self.weights[:-1], self.biases[:-1]):
			z = np.dot(w, activation) + b
			zs.append(z)
			activation = sigmoid(z)
			activations.append(activation)

		
		z = np.dot(self.weights[-1], activation) + self.biases[-1]
		zs.append(z)
		activations.append(softmax(z))
		return (activations, zs)

	def backpropagate(self, activation, target):
		# Inicijalizacija delta vrednosti
		nabla_b = [np.zeros(b.shape) for b in self.biases]
		nabla_w = [np.zeros(w.shape) for w in self.weights]

		activations, zs = self.feed_forward(activation)
		self.errors[-1] += square_error(target, activations[-1])
		if np.argmax(target) == np.argmax(activations[-1]):
			self.train_accuracies[-1] += 1

		# Izracunavanje izlazne vrednosti delte koriscenjem sigmoidne funkcije
		delta = softmax_prime(zs[-1]) * (activations[-1] - target)

		nabla_w[-1] = delta[:, None] * activations[-2][None, :]
		nabla_b[-1] = delta

		# Iteriranje kroz skriveni sloj mreze
		for i in xrange(2, self.n):
			# Izracunavnaje delte za svaki sloj
			delta = np.dot(self.weights[-i+1].T, delta) * sig_prime(zs[-i])

			nabla_w[-i] = delta[:, None] * activations[-i-1][None, :]
			nabla_b[-i] = delta

		return (nabla_w, nabla_b)

	def gradient_descent(self, training_data, targets, epochs, test_data=None,
	vis=False):
		m = len(training_data)

		for i in range(epochs):
			nabla_b = [np.zeros(b.shape) for b in self.biases]
			nabla_w = [np.zeros(w.shape) for w in self.weights]
			self.errors.append(0) # Restartovanje greske
			self.train_accuracies.append(0)

			for tag, img in training_data:
				target = map(lambda x: int(x in tag), targets)
				delta_nabla_w, delta_nabla_b = self.backpropagate(img, target)

				
				for j in range(self.n - 1):
					nabla_w[j] += delta_nabla_w[j]
					nabla_b[j] += delta_nabla_b[j]

			# Azuriranje tezine i bajesa
			self.weights = [w-(self.learning_rate(i)/m)*nw for w, nw in zip(self.weights, nabla_w)]

			self.biases = [b-(self.learning_rate(i)/m)*nb for b, nb in zip(self.biases, nabla_b)]

			# Funkcija validacije neuronske mreze
			if test_data:
				self.test_accuracies.append(self.validate(targets, test_data))

			self.errors[-1] /= m # Normalizacija greske
			self.train_accuracies[-1] /= float(m)
			print ("Epoch: " + str(i) + " error: " + str(self.errors[-1]) + " accuracy: " + str(self.test_accuracies[-1]) + " train_accuracy: " + str(self.train_accuracies[-1]))





	def validate(self, targets, test_data):
		accuracy = 0.0
		matrica=np.zeros( (3, 3) )
		for tag, img in test_data:
			target = map(lambda x: int(x in tag), targets)
			activations, zs = self.feed_forward(img)
                        matrica[np.argmax(target)][np.argmax(activations[-1])]+=1
                        
                        
                        
                        
			if np.argmax(target) == np.argmax(activations[-1]):
                                
				accuracy += 1
                prikaziMatricuKonfuzije(matrica)
                
                
		return accuracy/len(test_data)

	def learning_rate(self, i):
		return self.alpha_min + (self.alpha_max - self.alpha_min) * np.exp(-i/self.decay_speed)

	def load(self, filename):
		#Postavljanje parametara neuronske mreze iz fajla
		with open(filename, "r") as f:
			self.weights, self.biases = cPickle.loads(f.read())

	def save(self, filename):
		#Cuvanje parametara neuronske mreze u fajl
		with open(filename, "w+") as f:
			f.write(cPickle.dumps((self.weights,self.biases)))


	

	def encode(self):
		
		genotype = np.array([]) # Inicijalizacija novog genotipa
		for w, b in zip(self.weights, self.biases):
			genotype = np.concatenate((genotype, w.flatten(), b))

		self.genotype = genotype

	def decode(self):
	
		self.weights = []
		self.biases = []
		for i, width in enumerate(self.skeleton[1:], start=1):
			d = (self.skeleton[i-1]) * width
			# Citanje vrednosti tezina i postavljanje na 2D
			weights = self.read_genotype(d).reshape(width, self.skeleton[i-1])
			biases = self.read_genotype(width)

			self.weights.append(weights)
			self.biases.append(biases)

		self.cursor = 0 
		self.n = len(self.weights) + 1

	def evaluate(self, training_data, targets):
		error = 0

		for tag, img in training_data:
			target = np.array(map(lambda x: int(x in tag), targets))
			activations, zs = self.feed_forward(img)
			error += square_error(activations[-1], target)

		self.fitness = 1 - error/len(training_data)
