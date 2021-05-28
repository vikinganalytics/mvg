import os
from mvg import MVG
from mvg.analysis_classes import parse_results


RERUN = False

ENDPOINT = "http://127.0.0.1:8000"
TOKEN = os.environ["VIB_TOKEN"]

ses = MVG(ENDPOINT, TOKEN)
SOURCE_ID_ALL = ["u0001", "u0002", "u0003", "u0004", "u0005", "u0006"]
SOURCE_ID_ALL = [
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0001",
    "u0004",
    "u0002",
    "u0003",
    "u0001",
]

if RERUN:
    bsd = ses.request_population_analysis(
        SOURCE_ID_ALL, "BlackSheep", parameters={"atypical_threshold": 0.15}
    )
    REQ_ID = bsd["request_id"]
    print(f"Waiting for {bsd}")
    ses.wait_for_analyses([REQ_ID])
    bsd_res = ses.get_analysis_results(REQ_ID)
else:
    REQ_ID = "0e8b182e2c88044960f56c866e35ac32"

res_dict = ses.get_analysis_results(REQ_ID)

# Parse results
res = parse_results(res_dict, "Europe/Stockholm", "s")
res.summary()
res.plot()
print(res.to_df().head())
res.save()
print("Bye")
