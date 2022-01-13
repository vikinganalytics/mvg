#!/bin/bash
set -e

# Setup requirements for executing jupyter notebooks
python -m pip install -r requirements.txt
python -m pip install -r requirements_docs.txt

# Cleanup
do_cleanup() {
    echo "Performing cleanup of temporary resources"
    rm -rf ./va-data-charlie
}

# Execute notebooks containing examples
exec_examples() {
    echo "Running notebooks containing examples"
    for file in ./docs/source/content/examples/*.ipynb; do
        papermill "$file" "$file"
    done
    do_cleanup
    echo "Done"
}

# Setup SIGINT, EXIT trap to finish the script with cleanup
trap do_cleanup INT EXIT

# Execute main function
exec_examples