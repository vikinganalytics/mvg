import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#from mvg import MVG,
import plotting

filepath = r"C:\Users\Sergio\Documents\VikingAnalytics\Research\Projects\ABB Electrification\Experiments\analysis_v4\analysis_results\3___after_damper_defect__cmucoil_OPEN__upd"
filename = "results.df.csv"
#plot_title = "Angular Sensor waveforms - OPEN"
plot_title = "Electrical waveforms - OPEN (Update)"

file_to_load = os.path.join(filepath, filename)

df = pd.read_csv(file_to_load)

#image_modes = plotting.modes_over_time(df, plot_title, timeunit="us")
image_modes = plotting.modes_over_time(df, plot_title)

plt.show()
