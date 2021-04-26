import os
import pickle
from mvg import MVG
from mvg.analysis_classes import parse_results


ENDPOINT = "http://127.0.0.1:8000"
TOKEN = os.environ["VIB_TOKEN"]
ses = MVG(ENDPOINT, TOKEN)

req_ids = [
    "34ab72e0f2419fd716941a2e74566c7f",
    "2f6dc5ae055f9e82f6f5311c23250f07",
    "fbf673d3e5ebe21227537428b40b7312",
]


# local wrapper for parse_results
def parse_request(req_id):
    # parse funcrtion, also take time info
    result = parse_results(
        ses.get_analysis_results(req_id), # call API
        t_zone="Europe/Stockholm",
        t_unit="s")
    return result

breakpoint()

# Get class, parse will return object of correct class
res = parse_request(req_ids[1])
res.feature()

# use (interactive) functions
s_table = res.summary() # Reasonable summary
res.plot() # default plot
print(res.to_df().head()) # get results as dataFrame
res.save() # save object as pickle

# Class accessor functions
res.request_id()
res.feature()
res.status()
res.raw_results # more for internal use

# Repeat execise for other features
res = parse_request(req_ids[2])
dump_file = res.save()
res_pkl = pickle.load(open(dump_file, "rb"))
res_pkl.summary()
res_pkl.plot()
print(res_pkl.to_df().head())

res = parse_request(req_ids[0])
res.summary()
res.plot()
print(res.to_df().head())
res.save()

print("Bye")
