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


def parse_request(req_id):
    result = parse_results(ses.get_analysis_results(req_id))
    return result


res = parse_request(req_ids[0])
res.summary()
res.plot()
print(res.to_df().head())
res.save()

res = parse_request(req_ids[1])
res.summary()
res.plot()
print(res.to_df().head())
res.save()

res = parse_request(req_ids[2])
dump_file = res.save()
res_pkl = pickle.load(open(dump_file, "rb"))
res_pkl.summary()
res_pkl.plot()
print(res_pkl.to_df().head())

print("Bye")
