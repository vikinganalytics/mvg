import pytest
from pathlib import Path
import papermill as pm


@pytest.mark.skip(
    reason="Notebooks rely depend on data from, which needs to be fixed "
    "(https://github.com/vikinganalytics/va-data-charlie)."
)
def test_notebooks(vibium):
    notebooks_path = (
        Path(__file__).parents[1] / "docs" / "source" / "content" / "examples"
    )
    for nbook in sorted([f for f in notebooks_path.glob("*.ipynb") if f.is_file()]):
        pm.execute_notebook(nbook, nbook, parameters={"ENDPOINT": vibium})
