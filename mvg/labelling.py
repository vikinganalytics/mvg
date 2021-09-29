"""
MVG library for supporting labelling features
-----------
Library to plot, analyze labelling results
For more information see README.md.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

logger = logging.getLogger(__name__)


# Dictionary the defines color coding for labels
# where code -1 represents "No Data"
LABEL_COLOR_CODES = dict(
    (
        [-1, "white"],
        [0, "coral"],
        [1, "crimson"],
        [2, "red"],
        [3, "tomato"],
        [4, "plum"],
        [5, "lavender"],
        [6, "purple"],
        [7, "salmon"],
        [8, "sienna"],
        [9, "silver"],
        [10, "tan"],
        [11, "wheat"],
        [12, "khaki"],
    )
)


# pylint: disable=too-many-locals
def plot_labels_over_time(
    data,
    source_id,
    colors=None,
    height=100,
    width=5,
    timeticks_interval=None,
    timeunit="ms",
    axes=None,
    only_start_end_timeticks=False,
    timetick_angle=85,
    time_format=None,
):
    """Creates a rectangular timeline of labels.

    The rectangle presents the timeline of the labels for a source.

    Parameters
    ----------
    data: dataframe
        data from labels table.

    source_id: string
        string with source_Id. Can be replaced by other name

    colors: dictionary, optional
        color code for each mode.

    height: int, optional
        height of timeline.

    width: int, optional
        width of each measurement of source.

    timeticks_interval: int, optional
        time interval (in days) to separate the X-ticks.

    timeunit: str, optional
        unit of time corresponding to the timestamp epoch

    axes: object of class matplotlib.axes, optional
        the axes to be used by boxplot.

    only_start_end_timeticks: bool, optional
        If True, only print the time stamps for the first and last element of data.

    timetick_angle: float, optional
        the angle of time tick texts.

    time_format: str, optional
        strftime format specifier for tick_x_lables. If not given
        only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

    Returns
    ----------
    image: object of class matplotlib.axes

    """

    data["Date"] = pd.to_datetime(data["timestamp"], unit=timeunit)
    # Categorize the labels as integers
    data["label_idx"] = pd.factorize(data["label"])[0]

    colors = colors or LABEL_COLOR_CODES

    # Create figure with blank plot
    if axes is None:
        fig = plt.figure(figsize=(10, 3))
        axes = fig.add_subplot(111)
    image = axes.plot()

    ts_range = data["timestamp"].iloc[-1] - data["timestamp"].iloc[0]
    scaling_factor = len(data) / ts_range

    def _plot_row(row_data, y_pos=0):
        # Collect the indices of data where modes change plus start and end points
        interval_list = (
            [0]
            + [i for i in range(1, len(row_data)) if row_data[i] != row_data[i - 1]]
            + [len(row_data) - 1]
        )

        for idx in range(len(interval_list) - 1):
            i = interval_list[idx]
            col = row_data[i]
            label = data["label"].iloc[i]
            i_next = interval_list[idx + 1]
            block_len = (
                data["timestamp"].iloc[i_next] - data["timestamp"].iloc[i]
            ) * scaling_factor
            start_pos = (
                data["timestamp"].iloc[i] - data["timestamp"].iloc[0]
            ) * scaling_factor
            if label is not None:
                rect = patches.Rectangle(
                    (width * start_pos, y_pos),
                    width * block_len,
                    height - y_pos,
                    edgecolor=colors[col],
                    facecolor=colors[col],
                    fill=True,
                )
            else:
                rect = patches.Rectangle(
                    (width * start_pos, y_pos),
                    width * block_len,
                    height - y_pos,
                    fill=False,
                    hatch="/////",
                )

            axes.add_patch(rect)

    datalist = data["label_idx"].tolist()
    _plot_row(datalist)

    # Create time ticks on x-axis and labels
    if timeticks_interval is None:
        tick_index = (
            [0]
            + [i for i in range(1, len(datalist)) if datalist[i] != datalist[i - 1]]
            + [len(datalist) - 1]
        )
    else:
        tick_index = list(range(0, len(datalist), timeticks_interval))
    if only_start_end_timeticks:
        tick_index = [0, len(datalist) - 1]
    tick_positions = [
        (data["timestamp"].iloc[i] - data["timestamp"].iloc[0]) * scaling_factor * width
        for i in tick_index
    ]

    # Modify figure properties to leave wide rectangle only
    axes.set_ylim(0, height)
    axes.set_xlim(0, len(datalist) * width)
    axes.tick_params(
        axis="y",  # changes apply to the y-axis
        which="both",  # both major and minor ticks are affected
        left=False,  # ticks along the bottom edge are off
        right=False,  # ticks along the top edge are off
        labelleft=False,
    )  # labels along the bottom edge are off
    axes.set_xticks(tick_positions)

    # Modify ticks position and create legend
    df_changes = data.iloc[tick_index]
    if time_format is None:
        tick_x_labels = df_changes["Date"].apply(lambda x: x.date())
    else:
        tick_x_labels = df_changes["Date"].apply(lambda x: x.strftime(time_format))

    axes.set_xticklabels(tick_x_labels, rotation=timetick_angle)
    legend_labels = [
        patches.Patch(
            facecolor=colors[i], edgecolor="black", hatch="/////", label="No data"
        )
        if i == -1
        else patches.Patch(
            color=colors[i], label=f"{data[data['label_idx'] == i].iloc[0]['label']}"
        )
        for i in set(datalist)
    ]

    axes.legend(handles=legend_labels, bbox_to_anchor=(1.05, 1), loc="upper left")
    axes.set_title("Labels over time for {}".format(source_id))
    plt.tight_layout()

    return image
