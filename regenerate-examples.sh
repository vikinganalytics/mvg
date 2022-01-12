#!/bin/bash

# Setup requirements for executing jupyter notebooks
python -m pip install -r requirements.txt
python -m pip install -r requirements_docs.txt

# Cleanup
cleanup() {
    echo "Performing cleanup"
    rm .??*.ipynb
    rm -rf ./va-data-charlie
    kill $$
}

# Run examples
run_examples() {
    echo "Running notebooks containing examples"
    for file in ./docs/source/content/examples/*.ipynb; do
        filename="${file##*/}"
        cp "$file" ".$filename"
        jupyter nbconvert --execute --to notebook --ExecutePreprocessor.timeout=-1 --inplace ".$filename" --output "$file"
    done
    echo "Done"
}

# Set up SIGINT trap to call function.
trap "cleanup" INT

# Run examples and run cleanup function on error
run_examples || cleanup