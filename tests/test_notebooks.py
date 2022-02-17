from pathlib import Path
import papermill as pm


def test_notebooks(vibium):
    notebooks_path = (
        Path(__file__).parents[1] / "docs" / "source" / "content" / "examples"
    )
    for nbook in sorted([f for f in notebooks_path.glob("*.ipynb") if f.is_file()]):
        pm.execute_notebook(nbook, nbook, parameters={"ENDPOINT": vibium})
