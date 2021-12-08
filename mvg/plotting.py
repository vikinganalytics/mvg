"""
MVG Plotting library
-----------
Plotting library to visualize analysis results.
For more information see README.md.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

logger = logging.getLogger(__name__)


# Dictionary the defines color coding for modes
# where code -1 represents "No Data"
MODE_COLOR_CODES = dict(
    (
        [-2, "gray"],
        [-1, "white"],
        [0, "blue"],
        [1, "fuchsia"],
        [2, "orange"],
        [3, "aqua"],
        [4, "pink"],
        [5, "steelblue"],
        [6, "olive"],
        [7, "lavender"],
        [8, "beige"],
        [9, "mediumseagreen"],
        [10, "indigo"],
        [11, "lightcoral"],
        [12, "black"],
    )
)


def modes_boxplot(data, feature, request_id, total_modes=None, axes=None):
    """Creates a box plot for a source.

    The box plot describes the distribution of the requested variable
    for each of the discovered modes.

    Parameters
    ----------
    data: dataframe
        data from labels table.

    feature: string
        requested variable to be displayed.

    request_id: string
        string with request_id (or source_id). Can be replaced by other name
        to represent the request_id.

    total_modes: int, optional
        number of modes to be considered. If None displays unique
        modes in dataframe.

    axes: object of class matplotlib.axes, optional
        the axes to be used by boxplot.

    Returns
    ----------
    image: object of class matplotlib.axes

    """
    # Create figure
    if axes is None:
        _, axes = plt.subplots(nrows=1, ncols=1, figsize=(8, 3), tight_layout=True)

    # Define number of modes in boxplot
    if total_modes is None:
        modes = pd.Series(list(sorted(data["labels"].unique())))
    else:
        modes = pd.Series(list(range(int(total_modes) + 1)))
    logger.info("The number of modes considered as Boxplot categories is %s", modes)

    # Set modes as categories
    modes = modes.astype("category")
    data["Modes"] = data["labels"].copy()
    data["Modes"] = data["Modes"].astype("category")
    data["Modes"].cat.set_categories(modes.tolist(), inplace=True)

    # Plot and format figure
    image = data.boxplot(column=feature, by="Modes", ax=axes)
    image.get_figure().suptitle("")
    image.get_figure().gca().set_title("Boxplot for {}".format(request_id))
    image.get_figure().gca().set_ylabel(feature)

    return image


def modes_group_boxplot(dfs, feature, request_ids):
    """Creates a box plot for a set of sources.

    The figure display a boxplot for a list of sources
    where each box plot describes the distribution of the
    requested variable for each of the discovered modes.

    Parameters
    ----------
    dfs: list of dataframes
        list with data from labels table.

    feature: string
        requested variable to be displayed.

    request_ids: List of strings
        list of strings with request_ids (or sources_ids). Can be replaced by other name
        to represent each request_id.
    """
    # Create figure
    fig, axes = plt.subplots(nrows=len(dfs), ncols=1, figsize=(6, 6))
    logger.info("The number of request_ids to be plotted is %s", len(dfs))

    # Identify maximum number of modes across set of sources
    max_no_modes = 1
    for i in dfs:
        if max_no_modes <= i["labels"].max():
            max_no_modes = i["labels"].max()

    # Iterate over set of sources to create boxplots
    for count, value in enumerate(dfs):
        axp = modes_boxplot(
            value,
            feature,
            request_ids[count],
            total_modes=max_no_modes,
            axes=axes[count],
        )
        axp.set_title("Boxplot for {}".format(request_ids[count]))
        axp.set_ylabel(feature)
        if count + 1 != len(dfs):
            axp.set_xlabel("")

    fig.tight_layout(rect=[0, 0.03, 1, 0.98])


# pylint: disable=too-many-locals
def modes_over_time(
    data,
    request_id,
    colors=None,
    height=100,
    width=5,
    timeticks_interval=None,
    timeunit="ms",
    axes=None,
    show_uncertain=True,
    only_start_end_timeticks=False,
    timetick_angle=85,
    time_format=None,
):
    """Creates a rectangular timeline of modes.

    The rectangle presents the timeline of the modes for a source.

    Parameters
    ----------
    data: dataframe
        data from labels table.

    request_id: string
        string with request_id (or source_Id). Can be replaced by other name
        to represent the request_id.

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

    show_uncertain: bool, optional
        highlight uncertain areas

    only_start_end_timeticks: bool, optional
        If True, only print the time stamps for the first and last element of data.

    timetick_angle: float, optional
        the angle of time tick texts.

    time_format: str, optional
        strftime format specifier for tick_x_labels. If not given
        only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

    Returns
    ----------
    image: object of class matplotlib.axes

    """

    if "datetime" in data.columns:
        # analysis classes have correct t_zone handling
        # so use those timestamps if they exist
        data = data.rename(columns={"datetime": "Date"})
    else:
        data["Date"] = pd.to_datetime(data["timestamps"], unit=timeunit)

    colors = colors or MODE_COLOR_CODES

    # Create figure with blank plot
    if axes is None:
        fig = plt.figure(figsize=(10, 3))
        axes = fig.add_subplot(111)
    image = axes.plot()

    # Create rectangular patch for timestamp

    ts_range = data["timestamps"].iloc[-1] - data["timestamps"].iloc[0]
    scaling_factor = len(data) / ts_range

    def _plot_row(row_data, is_uncert_data, y_pos=0):
        # Collect the indices of data where modes change plus start and end points
        interval_list = (
            [0]
            + [i for i in range(1, len(row_data)) if row_data[i] != row_data[i - 1]]
            + [len(row_data) - 1]
        )

        for idx in range(len(interval_list) - 1):
            # gray border around uncertains
            i = interval_list[idx]
            if is_uncert_data:
                col = -2 if row_data[i] else -1
            else:
                col = row_data[i]
            i_next = interval_list[idx + 1]
            block_len = (
                data["timestamps"].iloc[i_next] - data["timestamps"].iloc[i]
            ) * scaling_factor
            start_pos = (
                data["timestamps"].iloc[i] - data["timestamps"].iloc[0]
            ) * scaling_factor
            rect = patches.Rectangle(
                (width * start_pos, y_pos),
                width * block_len,
                height - y_pos,
                edgecolor=colors[col],
                facecolor=colors[col],
                fill=True,
            )
            axes.add_patch(rect)

    datalist = data["labels"].tolist()
    _plot_row(datalist, is_uncert_data=False)

    if show_uncertain:
        uncertlist = data["uncertain"].tolist()
        _plot_row(uncertlist, is_uncert_data=True, y_pos=4 / 5 * height)

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
        (data["timestamps"].iloc[i] - data["timestamps"].iloc[0])
        * scaling_factor
        * width
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
        patches.Patch(facecolor=colors[i], edgecolor="black", label="No data")
        if i == -1
        else patches.Patch(color=colors[i], label="Mode {}".format(int(i)))
        for i in list(data["labels"].unique())
    ]

    axes.legend(handles=legend_labels, bbox_to_anchor=(1.05, 1), loc="upper left")
    axes.set_title("Modes over time for {}".format(request_id))
    plt.tight_layout()

    return image


def modes_probabilities_over_time(
    data,
    title,
    colors=None,
    height=12,
    width=4,
    timeticks_interval=None,
    timeunit="ms",
    axes=None,
    timetick_angle=45,
    time_format=None,
):
    """Creates a line chart depecting the change of mode probability over time.

    Parameters
    ----------
    data: dataframe
        a dataframe with timestamps as the index column and an
        additional column (named as "mode {mode number}") for every mode.

    title: string
        plot title

    colors: dictionary, optional
        color code for each mode.
        the dictionary keys should be of the form "mode {mode number}".

    height: int, optional
        height of plot used in figsize.

    width: int, optional
        width of plot used in figsize.

    timeticks_interval: int, optional
        time interval (in days) to separate the X-ticks.

    timeunit: str, optional
        unit of time corresponding to the timestamp epoch

    axes: object of class matplotlib.axes, optional
        the axes to be used by plot.

    timetick_angle: float, optional
        the angle of time tick texts.

    time_format: str, optional
        strftime format specifier for tick_x_labels. If not given, dates will be shown
        in locale format. To show dates and time use %y%m%d-%H:%M:%S

    Returns
    ----------
    image: object of class matplotlib.axes

    """

    # Colors for the line chart
    colors = colors or {
        f"mode {x}": MODE_COLOR_CODES[x] for x in MODE_COLOR_CODES.keys()
    }

    # Create figure with blank plot
    if axes is None:
        fig = plt.figure(figsize=(height, width))
        axes = fig.add_subplot(111)
    image = axes.plot()

    # Set timetick interval
    if not timeticks_interval:
        timeticks_interval = round(len(data) / 10)

    # Format the timestamps based on timeunit and time_format
    if time_format:
        data_index_formatted = [
            pd.to_datetime(dt, unit=timeunit).strftime(time_format) for dt in data.index
        ]
    else:
        data_index_formatted = [
            str(pd.to_datetime(dt, unit=timeunit)) for dt in data.index
        ]

    # Form and set the tick positions and the tick labels
    tick_positions = list(range(0, len(data), timeticks_interval))
    tick_x_labels = [data_index_formatted[t] for t in tick_positions]
    axes.set_xticks(tick_positions)
    axes.set_xticklabels(tick_x_labels, rotation=timetick_angle, ha="right")

    # Plot line chart for each mode
    for col in data.columns:
        axes.scatter(data_index_formatted, data[col], label=col, c=colors[col], s=10)

    axes.legend(bbox_to_anchor=(1.05, 1), loc="upper left", markerscale=3)
    axes.set_title(title)
    plt.tight_layout()

    return image


def modes_over_time_group(dfs, request_ids, days=1, tol=2, timeunit="ms"):
    """Creates a rectangular timeline of modes for a set of sources.

    The figure display the rectangular timeline of modes
    for a list of sources with X-ticks at regular intervals.

    Parameters
    ----------
    dfs: list of dataframes
        list with data from labels table.

    request_ids: List of strings
        list of strings with request_ids (or source_Ids). Can be replaced by other name
        to represent each request_id.

    days: int, optional
        interval to be considered for each measurement.

    tol: int, optional
        tolerance (in hours) to consider when merging timestamps.

    timeunit: str, optional
        unit of time corresponding to the timestamp epoch
    """
    # Create figure
    _, axes = plt.subplots(
        nrows=len(dfs), ncols=1, figsize=(9, 6), sharex=True, tight_layout=True
    )
    logger.info("The number of request_ids to be plotted is %s", len(dfs))

    # Identify x-axis (epochs) limits
    min_epoch = 0
    max_epoch = 0
    for i in dfs:
        # Conversion Timestamp to Epoch
        if (min_epoch >= i["timestamps"].min()) or (min_epoch == 0):
            min_epoch = i["timestamps"].min()
        if max_epoch <= i["timestamps"].max():
            max_epoch = i["timestamps"].max()

    # Create reference dataframe (in seconds) covering timestamps of all dataframes
    epoch_multiplier = 24 * 60 * 60  # * 1000
    steps = days * epoch_multiplier
    df_ref = pd.DataFrame(
        range(min_epoch, max_epoch + steps, steps), columns=["timestamps"]
    )

    # Iterate over set of sources to create rectangular timeframes
    # with a tolerance in milliseconds
    for count, value in enumerate(dfs):
        dfexp = pd.merge_asof(
            df_ref, value, on="timestamps", tolerance=int(tol * 60 * 60 * 1000)
        )
        dfexp["labels"] = dfexp["labels"].fillna(value=-1)
        # X-ticks (time) interval is 7 days (one week)
        modes_over_time(
            dfexp,
            request_ids[count],
            timeticks_interval=7,
            timeunit=timeunit,
            axes=axes[count],
        )


# Dictionary the defines color coding for labels
# where code -1 represents "No Data"
LABEL_COLOR_CODES = dict(
    (
        [-1, "white"],
        [0, "orangered"],
        [1, "coral"],
        [2, "darksalmon"],
        [3, "darkviolet"],
        [4, "mediumorchid"],
        [5, "mediumpurple"],
        [6, "thistle"],
        [7, "slategrey"],
        [8, "silver"],
        [9, "sienna"],
        [10, "tan"],
        [11, "moccasin"],
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
    data: dataframe or list of dicts
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
        strftime format specifier for tick_x_labels. If not given
        only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

    Returns
    ----------
    image: object of class matplotlib.axes

    """

    data = pd.DataFrame(data)

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
