# This example requires sources to be uploaded to
# the server side

import os
from mvg import MVG
from mvg.analysis_classes import parse_results

# for using RERUN=False
# a request_id for the feature needs to exist
RERUN = True

# Instantiate a session object with mvg library
# replace token and server with your url/token
ENDPOINT = os.environ["SERVER_URL"]
TOKEN = os.environ["SERVER_TOKEN"]

ses = MVG(ENDPOINT, TOKEN)

# replace with your source
SOURCE_ID = "u0001"

if RERUN:
    req = ses.request_analysis(SOURCE_ID, "ModeId")
    REQ_ID = req["request_id"]
    print(f"Waiting for {REQ_ID}")
    ses.wait_for_analyses([REQ_ID])
else:
    REQ_ID = "3e2b074eef3526a1e53669958ff91f25" # replace with valid 

res_dict = ses.get_analysis_results(REQ_ID)

# Parse results
res = parse_results(res_dict, "Europe/Stockholm", "s")
res.summary()
res.plot()
res.to_df().head()
res.save()
print("Bye")
