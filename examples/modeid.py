import os
from mvg import MVG
from mvg.analysis_classes import parse_results

RERUN = True

# Instantiate a session object with mvg library
ENDPOINT = "http://127.0.0.1:8000"
TOKEN = os.environ["VIB_TOKEN"]
ses = MVG(ENDPOINT, TOKEN)
SOURCE_ID = "u0001"

if RERUN:
    req = ses.request_analysis(SOURCE_ID, "ModeId")
    REQ_ID = req["request_id"]
    print(f"Waiting for {REQ_ID}")
    ses.wait_for_analyses([REQ_ID])
else:
    REQ_ID = "c82db3fa8c31d8424ba32fd2e8c597a6"

res_dict = ses.get_analysis_results(REQ_ID)
print(res_dict)

# Parse results
res = parse_results(res_dict, "Europe/Stockholm", "s")
res.to_df("t.csv")
res.summary()
res.plot()
res.to_df().head()
res.save()
print("Bye")
