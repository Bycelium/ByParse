import math
import random
import numpy as np

def square(x):
	"""
		Return the square of a given number
	"""
	return x*x

def next_collatz(a):
	"""
		Return the next number in the collatz sequence.
		Extended to work for real numbers.
	"""
	return math.cos(a*math.pi/2)**2*a/2 + \
	math.sin(a*math.pi/2)**2 * (3*a+1)/2

def collatz(a: int):
	"""
		Return the degree of a before it reachs the 1,2,4 cycle
		a should be an integer
	"""
	i = 0
	while a != 1:
		a = int(next_collatz(a))
		i += 1
	return i
