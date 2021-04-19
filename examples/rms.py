import os

from mvg import MVG
from mvg import analysis_classes

RERUN = False

ENDPOINT = "http://127.0.0.1:8000"
TOKEN = os.environ["VIB_TOKEN"]

ses = MVG(ENDPOINT, TOKEN)
SOURCE_ID = "u0001"

if RERUN:
    RMS = ses.request_analysis(SOURCE_ID, "RMS")
    print(f"Waiting for {RMS}")
    ses.wait_for_analyses([RMS["request_id"]])
    rms_res = ses.get_analysis_results(RMS["request_id"])
else:
    REQ_ID = "2f6dc5ae055f9e82f6f5311c23250f07"
    rms_res = ses.get_analysis_results(REQ_ID)
print(rms_res)


rms = analysis_classes.RMS(rms_res, t_zone="Europe/Stockholm", t_unit="s")
rms.plot()
rms.summary()
rms.save()
print("Bye")
