#!/bin/bash

echo "Creating test dataset ..."
python generate_feas_rest_dataset.py 0 0
echo "Extend test dataset ..."
for (( i=1; i <= 9; ++i ))
do
    echo "Dataset Part $i"
    python generate_feas_rest_dataset.py 0 1
done

echo "Done!"
