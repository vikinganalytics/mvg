# This example requires sources to be uploaded to
# the server side

import os
import json
import typer
from typing import Optional
from mvg import MVG
from mvg.analysis_classes import parse_results
import logging
import sys

root_logger = logging.getLogger()
root_logger.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
stream_handler = logging.StreamHandler(stream=sys.stderr)
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

# Instantiate a session object with mvg library
# replace token and server with your url/token
ENDPOINT = os.environ["TEST_URL"]
TOKEN = os.environ["TEST_TOKEN"]

app = typer.Typer() # Create typer app

@app.command()
def run(
        source_id: str = typer.Argument(
            ...,
            help='Source ID'),
        feature: Optional[str] = typer.Argument("ModeId",
                                                help='Feature'),
        start: Optional[int] = typer.Argument(None,
                                                help='Start timestamp [epoch]'),
        end: Optional[int] = typer.Argument(None,
                                            help='End timestamp [epoch]'),
        show: bool = typer.Option(True, help='Show plot rather than saving it'),
        pdb: bool = typer.Option(False, help='Enter pdb debugger'),
        params: bool = typer.Option(False, help='Use ./params.json file')
):
    """Run an analyis on Source ID"""
    
    
    ses = MVG(ENDPOINT, TOKEN)

    # Fetch parameters if given
    if params:
        with open("params.json", "r", encoding="utf-8") as json_data:
            params = json.load(json_data)
            print(f"Params loaded from ./params.json")
            print(json.dumps(params, indent=4))
    else:
        params = {}

    req = ses.request_analysis(sid=source_id,
                               feature=feature,
                               parameters=params,
                               start_timestamp=start,
                               end_timestamp=end)
    request_id = req["request_id"]
    print(f"Waiting for {request_id}")
    ses.wait_for_analyses([request_id])
    get_and_display_results(ses, request_id, show, pdb)

@app.command()
def retrieve(
        request_id: str = typer.Argument(
            ...,
        help='Request ID'),
        show: bool = typer.Option(True, help='Show plot rather than saving it'),
        pdb: bool = typer.Option(False, help='Enter pdb debugger')
):
    """Retrieve a previous analyis with request ID"""
        
    ses = MVG(ENDPOINT, TOKEN)
    get_and_display_results(ses, request_id, show, pdb)

    
    
def get_and_display_results(ses, request_id, show, pdb):

    # Get results
    res_dict = ses.get_analysis_results(request_id)

    # Parse results
    res = parse_results(res_dict, "Europe/Stockholm", "s")
    if pdb:
        breakpoint()
    
    res.summary()
    res.plot(show)
    res.to_df().head()
    res.save()
    print("Bye")


if __name__ == '__main__':
    app()  
