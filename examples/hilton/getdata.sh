# Script, written as a bash script, to provide wget commands for all associated data products.


#        DR5_SZ cluster catalog
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_dr5/DR5_cluster-catalog_v1.1.fits
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_dr5/DR5_multiple-systems_v1.0.fits
wget -q -t 5 -nc -w 3 https://lambda.gsfc.nasa.gov/data/suborbital/ACT/ACT_dr5/DR5_cluster-search-area-mask_v1.0.fits