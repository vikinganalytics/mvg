# This example requires sources to be uploaded to
# the server side

import os
from requests import HTTPError
from mvg import MVG
from mvg import analysis_classes
from mvg.analysis_classes import parse_results

## Preprartions
import pandas as pd

data = pd.read_csv("data.csv")

# for using RERUN=False
# a request_id for the feature needs to exist
RERUN = True

# replace token and server with your url/token
ENDPOINT = os.environ["TEST_URL"]
TOKEN = os.environ["TEST_TOKEN"]
ses = MVG(ENDPOINT, TOKEN)

try:
    # create source for KPI
    SOURCE_ID = "tabular_source"
    data = pd.read_csv("data.csv")
    cols = data.columns.to_list()
    ses.create_tabular_source(SOURCE_ID, {}, cols)
    jdata = data.to_dict("list")
    ses.create_tabular_measurement(SOURCE_ID, data.to_dict("list"))

    if RERUN:
        ANA = ses.request_analysis(SOURCE_ID, "ModeId")
        print(f"Waiting for {ANA}")
        ses.wait_for_analyses([ANA["request_id"]])
        ana_res = ses.get_analysis_results(ANA["request_id"])
    else:
        REQ_ID = "2f6dc5ae055f9e82f6f5311c23250f07"  # replace with valid ID
        ana_res = ses.get_analysis_results(REQ_ID)
        print(ana_res)

except HTTPError as exc:
    print(exc)
    print("Details on error")
    print(exc.response.json())

ana = parse_results(ana_res, t_zone="Europe/Stockholm", t_unit="s")
ana.plot()
ana.summary()
print("Bye")
