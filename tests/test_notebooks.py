import papermill as pm
from pathlib import Path


def test_notebook0(vibium):
    notebooks_path = (
        Path(__file__).parents[1] / "docs" / "source" / "content" / "examples"
    )
    for nbook in sorted([f for f in notebooks_path.glob("*.ipynb") if f.is_file()]):
        pm.execute_notebook(nbook, nbook, parameters=dict(ENDPOINT=vibium))
