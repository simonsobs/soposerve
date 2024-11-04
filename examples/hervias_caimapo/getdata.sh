# Script, written as a bash script, to provide wget commands for all associated data products.


#        ACT Targeted Transient Flux Constraints
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_adv/flux/table_SNe.txt
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_adv/flux/table_TDEs.txt
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_adv/flux/table_GRBs.txt