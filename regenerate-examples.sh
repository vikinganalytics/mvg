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
    local _d="./docs/source/content/examples"
    for file in `ls -v $_d/*.ipynb`; do
        papermill "$file" "$file" -p ENDPOINT http://127.0.0.1:8000
    done
    echo "Finished executing examples"
}

# Setup SIGINT, EXIT trap to finish the script with cleanup
trap do_cleanup INT EXIT

# Execute main function
exec_examples