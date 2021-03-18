# mvg

## Run the backend server for testing

Backend URL: (https://api.beta.multiviz.com)

### Starting local server

Navigate to top level on vibium-cloud repo
```
uvicorn vibium_app.main:app --reload
```

Open your browser at http://127.0.0.1:8000

### Interactive API docs
Go to http://127.0.0.1:8000/docs

Find API definitions [here](https://github.com/vikinganalytics/coreip/blob/master/core-vib/core-vib.pdf)

### Generating docs for mvg package

From project root
```
pdoc -o doc/ mvg/
````


### Linting and testing instructions
These commands should all be run locally and made sure to be passing before opening a PR

```
black .
flake8 mvg
pylint mvg
python -m pytest --verbose tests
```

### venv

Create (all commands from root directory)
```
python -m venv venv
pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install -e .  # to secure imports
```

Activate (bash)
```
source venv/Scripts/activate
```

###
