#!/bin/bash

echo "Creating train dataset ..."
python generate_feas_rest_dataset.py 1 0
echo "Extend train dataset ..."
for (( i=1; i <= 9; ++i ))
do
    echo "Dataset Part $i"
    python generate_feas_rest_dataset.py 1 1
done

echo "Done!"
