################################################################################
# Multidimensional Lattice Model Generator 
# Version 1.0
#
# Authors: Michael Manhart and Willow Kion-Crosby
# Contact: mmanhart@fas.harvard.edu
#
# [Add license, copyright]
#
# [Add brief description]
################################################################################


import numpy
import scipy.misc
import random
import argparse
import math
import os


###########################################################################
# The following function calculates the rate between 
# two locations on the lattice given the energies at those 
# sites, an effective inverse-temperature and maximum rate.
###########################################################################
def Find_Rate(beta, Ei, Ef, Gamma_0):
	
	# The Monte-Carlo transition rates are calculated 
	# using the difference in energy between the 
	# initial and final states. beta is understood 
	# as the inverse-temperature of the system.
	deltaE = Ef-Ei
	Gamma = Gamma_0*min([1, math.exp(-deltaE*beta)])
	return Gamma
	
###########################################################################
# This functions provides a basic energy landscape given 
# 
###########################################################################
def Find_Energy(E_0, position):
	
	# If no energy file is found, a landscape
	# will be developed using the following function.
	
	return E_0*sum(position)

###########################################################################
# This calculates the nth moment of an exponential 
# distribution given the mean, tau.
###########################################################################
def Exponential_Moment(n, tau): 

	return scipy.misc.factorial(n)*(tau**n)
	
###########################################################################
# To limit failed lattice development, this function
# checks various properties of the input parameters.
###########################################################################
def Check_Args(args):
	
	if args.lattice_size == 0:
		print("ERROR: Trying to generate a lattice of size 0.  Exiting.\n")
		exit()
		
	if args.dimension <= 0:
		print("ERROR: Dimension less than or equal to 0.  Exiting.\n")
		exit()
		
	if args.start_sites == None:
		args.start_sites = ",".join(["_".join([str(1) for d in range(args.dimension)])])
		
	if args.final_sites == None:
		args.final_sites = ",".join(["_".join([str(args.lattice_size) for d in range(args.dimension)])])
		
	if args.energy_file == None:
		args.energy_file = str(args.dimension)+"D_lattice"

def main():

	# Read user input lattice parameters
	
	parser = argparse.ArgumentParser(description="This script generates a multi-dimensional Euclidean lattice with a general energy landscape.")
	
	parser.add_argument("--lattice-size",		type=int,	default=10,	action="store",		help="Number of positions for each dimension  (default 10)")
	parser.add_argument("--dimension",		type=int, 	default=2,	action="store",		help="Dimension of Euclidean lattice (default 2)")
	parser.add_argument("--max-moment",		type=int, 	default=1,	action="store",		help="Maximum moment include calculate for waiting time distributions at each site (default 1)")
	parser.add_argument("--start-sites",		type=str, 			action="store",		help="Location of each start site on the lattice written as x1_x2_...xD with xi between 1 and L, represented as a list of strings e.g. 1_1,1_2,1_3 (default 1_1_1_..._1)")	
	parser.add_argument("--final-sites",		type=str, 			action="store",		help="Location of each final site on the lattice written as x1_x2_...xD with xi between 1 and L, represented as a list of strings e.g. 8_10,9_10,10_10 (default L_L_L_..._L)")	
	parser.add_argument("--beta",			type=float, 	default=0.0,	action="store",		help="Effective temperature (default 0)")
	parser.add_argument("--E-scale",		type=float, 	default=1.0,	action="store",		help="Energy scale of landscape (default 1)")
	parser.add_argument("--rate-coefficient",	type=float, 	default=1.0,	action="store",		help="Rate coefficient (default 1)")
	parser.add_argument("--energy-file",		type=str, 			action="store",		help="Name of energy landscape file that will be used to compute rates. If file does not exist, it will be generated using an exponential distribution to find the energies. File extension is '.energy' (default DD__lattice.energy)")
	parser.add_argument("--periodic-boundary", 					action="store_true",	help="Set if the lattice has periodic boundary conditions")
	
	args = parser.parse_args()
	
	# Check validity of input
	
	Check_Args(args)
	
	L = args.lattice_size
	D = args.dimension
	
	energy_file = args.energy_file
	run_name = energy_file
	max_moment = args.max_moment
	start_sites = args.start_sites.split(",")
	final_sites = args.final_sites.split(",")
	beta = args.beta
	E_0 = args.E_scale
	Gamma_0 = args.rate_coefficient
	pbcheck = args.periodic_boundary

	# Define a position vector to recursively build each location on the lattice

	position = numpy.ones(D)
	
	# Initialize the rate matrix dictionary, the nearest-neighbor dictionary, and a total list of sites
	
	trans_rates = {}
	list_of_nn = {}
	sites = ["" for x in range(L**D)]
	
	# Initialize energy dictionary which will specify the barrier heights between sites
	
	energies = {}
	
	# Check if .energy file already exists. If so, read in energy dictionary.
	# If not, generate .energy file
	
	try:
		energy_file = open(energy_file+".energy", "r")
		energy_file_exists = True
		
		for line in energy_file.readlines():
		
			line_elements = line.split()
			tran_sites = line_elements[0]
			
			energy = line_elements[1]
			energies[tran_sites] = float(energy)
			
		energy_file.close()

	except IOError:
	
		energy_file_exists = False
		energy_file = open(energy_file + ".energy", "w")
	
	for i in range(L**D):

		sites[i] = "_".join([str(int(k)) for k in position])
		site = sites[i]
		trans_rates[site+"->"+site] = 0.0
		
		neighbors = ["" for j in range(2*D)]
		
		for j in range(2*D):
		
			increment = 1*(j%2 == 0)-1*(j%2 == 1)

			if not pbcheck:
				nn = "_".join([str(int(position[k]+(k == int(j/2))*increment)) for k in range(len(position))])
			else:
				nn = "_".join([str(int(position[k]+(k == int(j/2))*increment)*int(position[k]+(k == int(j/2))*increment<L+1)*int(position[k]+(k == int(j/2))*increment>0)+L*int(position[k]+(k == int(j/2))*increment==0)+int(position[k]+(k == int(j/2))*increment==L+1)) for k in range(len(position))])
			
			
			neighbors[j] = nn
			
			if (position[int(j/2)]+increment > 0 and position[int(j/2)]+increment < L+1) or pbcheck:
				
				if energy_file_exists:
				
					Ei = energies[site]
					Ef = energies[nn]
				
				else:
					neighbor_position = [int(coordinate) for coordinate in nn.split('_')]
					Ei = Find_Energy(E_0, position)
					Ef = Find_Energy(E_0, neighbor_position)
					energies[site] = Ei
					energies[nn] = Ef
				
				trans_rates[site+"->"+nn] = Find_Rate(beta, Ei, Ef, Gamma_0)
				trans_rates[nn+"->"+site] = Find_Rate(beta, Ef, Ei, Gamma_0)
			else:
				trans_rates[site+"->"+nn] = 0
				trans_rates[nn+"->"+site] = 0
				
				energies[site+"->"+nn] = 0
				energies[nn+"->"+site] = 0
				
		list_of_nn[site] = neighbors
			
		shift = True
		for j in range(D):
			if shift:
				position[j] = position[j] + 1
			if position[j]>L:
				position[j] = 1
				shift = True
			else:
				shift = False
	
	
	network_file = open(run_name + ".network", "w")
	
	for site in sites:
		rate_total = 0
		
		for nn in list_of_nn[site]:
			rate_total = rate_total + trans_rates[site+"->"+nn]
			
			if not energy_file_exists:
				if  trans_rates[site+"->"+nn]>0:
					energy_file.write(site+"\t"+str(energies[site])+"\n")
					energy_file.write(nn+"\t"+str(energies[nn])+"\n")
		
		network_file.write(site + "\t" + ";".join([nn+","+str(trans_rates[site+"->"+nn]) for nn in list_of_nn[site] if trans_rates[site+"->"+nn]>0]))
		
		network_file.write("\t"+",".join([str(Exponential_Moment(n, 1./rate_total)) for n in range(1,max_moment + 1)]))
		network_file.write("\t"+",".join([x for x in site.split("_")]))
		network_file.write("\n")
		
	network_file.close()
	if not energy_file_exists:
		energy_file.close()

	bc_file = open(run_name + ".bc", "w")
	part_func = len(start_sites)
	bc_file.write("\t".join([start_site+","+str(1./part_func) for start_site in start_sites]))
	bc_file.write("\n")
	bc_file.write("\t".join(final_sites))
	bc_file.close()

if __name__ == '__main__':
	main()
