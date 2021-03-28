from scientific import TimeseriesAnalyser
import datetime

import pandas
import numpy
import operator

from pandas import DataFrame

now = datetime.datetime.now()

ISO8601 = '%Y-%m-%dT%H:%M:%S.%f'

USERNAME = 'hans'
PASSWORD = '???'

# Create the TimeseriesAnalyser object, this will connect to Byteport
analyser = TimeseriesAnalyser(USERNAME, PASSWORD)

# Define the timespan
#from_time = now - datetime.timedelta(days=30)
#to_time = now


def bfdb_timeseries_to_pandas_series(bfdb_timeseries, to_dataframe=False, name=None):
    '''
    Takes a BFDB time series frame and return a Pandas Series
    that can be used for further processing tasks.

    :param ts:
    :return:
    '''

    timestamps = []
    values = []

    # Prepare by splitting the time series data into two arrays
    for row in bfdb_timeseries:
        try:
            timestamps.append(row.dateOf_ts)
            values.append(row.float_value)
        except Exception:
            print "Failed to parse data (%s), ignoring" % row

    series = pandas.Series(values, timestamps, name=name)

    # To data frame li
    if to_dataframe:
        return series.to_frame()
    else:
        return series

def groupby(data_frame, grouping='DAILY'):
    """

    Split the series into sub-sets of _hours_ or _days_ and return one vector with parameters
    describing each subset. The subset can then be clustered etc.

    :param data_frame:
    :param grouping:
    :param subset_analysis:
    :return:
    """

    if grouping == 'DAILY':
        group_definition = [data_frame.index.date]
    elif grouping == 'HOURLY':
        group_definition = [data_frame.index.date, data_frame.index.hour]
    elif grouping == 'WEEKLY':
        group_definition = lambda x: x.isocalendar()[0:2]
    elif grouping == 'MONTHLY':
        group_definition = [data_frame.index.year, data_frame.index.month]
    else:
        raise Exception("Unsupported grouping, '%s'" % grouping)

    # Return a new DataFrame
    grouped_data_frames = []
    for group in data_frame.groupby(group_definition):
        grouped_data_frames.append(group)

    return grouped_data_frames


def group_and_describe(data_frame, grouping='DAILY', subset_analysis='pandas_describe'):
    """

    Split the series into sub-sets of _hours_ or _days_ and return one vector with parameters
    describing each subset. The subset can then be clustered etc.

    :param data_frame:
    :param grouping:
    :param subset_analysis:
    :return:
    """
    grouped_data = groupby(data_frame, grouping)

    print "Data was grouped in %s groups" % len(grouped_data)

    description_dfs = list()

    for group_time, grouped_data_frame in grouped_data:

        if subset_analysis == 'pandas_describe':
            # Use the full describe() vector
            subset_description = grouped_data_frame.describe()
        else:
            raise Exception("Unsupported vectorization method")

        if grouping == 'DAILY':
            subset_description.columns = [u'%s' % group_time]
        elif grouping == 'HOURLY':
            subset_description.columns = [u'%s %s' % (group_time[0], group_time[1])]
        else:
            raise Exception("Unsupported grouping, '%s'" % grouping)

        # Extract values
        description_dfs.append(subset_description)

    concatenated = pandas.concat(description_dfs, axis=1)

    return concatenated

COV_LIMIT = 0.2
def arrange_by_distance(descriptions, averaging_strategy='median', judge_strategy='euclidian'):
    '''
    Given a DataFrame with descriptions, establish a mean

    Input looks like this for example, grouped by hours

           2014-04-09 20  2014-04-09 21  2014-04-09 22  2014-04-09 23
    count       5.000000       6.000000       6.000000            1.0
    mean        2.800000      16.166667       1.500000           12.0   <---- FIND mean and std for each row. ie creating "mean-mean"
    std        71.461178      75.369534      58.353235            NaN
    min       -76.000000     -76.000000     -80.000000           12.0
    25%       -58.000000     -45.000000     -25.750000           12.0
    50%        -2.000000      24.500000      -8.500000           12.0
    75%        69.000000      79.000000      38.750000           12.0
    max        81.000000      95.000000      83.000000           12.0

    :param descriptions:
    :return:
    '''

    kv_vector_descriptions = []

    # Iterate over rows which we assume contain a certain type of descriptor
    # for example the mean for each group, depending on what kind of description algorithm was used
    average_descriptor = {}
    for descriptor_row in descriptions.iterrows():
        # descriptor_row is a tuple
        #   [0] is the index (ie 'count' or 'mean')
        #   [1] is a vector with all mean, count, std etc... for each group
        #
        # Now describe them!, we only need mean and std

        # Keep this for ref
        descriptor_kind = descriptor_row[0]

        if averaging_strategy == 'cov':
            # Make use of pandas describe to obtain mean and std so we can calculate COV
            row_description = pandas.Series(descriptor_row[1].values).describe()

            # Strategy 1 - Discard by COV
            #  If the variation of the descriptor is too large over the data-set: discard it.
            #
            # Calculate coefficient of variation
            #
            # Cv = std / mean
            #
            std = row_description[2]
            mean = row_description[1]

            cov = std / mean

            abs_cov = abs(cov)

            if abs_cov < COV_LIMIT:
                print "*** Usable descriptor (%s), COV=%s" % (descriptor_kind, abs_cov)
                average_descriptor[descriptor_kind] = mean
            else:
                print "Unusable descriptor (%s), COV=%s" % (descriptor_kind, abs_cov)
        elif averaging_strategy == 'median':
            median = numpy.median(descriptor_row[1].values)

            average_descriptor[descriptor_kind] = median
        else:
            raise Exception("Unsupported averaging strategy!")

    # The size of average_descriptor points to how good our classification is, higher is better
    print "Length of average_descriptor = %s" % len(average_descriptor)

    print average_descriptor

    # Now we have establised what descriptor is useful to compare against
    av_df = DataFrame.from_dict(average_descriptor, orient='index')
    av_v = av_df.ix[:,0]

    groups_by_distance_to_average = []

    # Now create a set of vectors that can be compared vs the average vector
    for descriptor_column in descriptions:

        #print "\n%s\n" % descriptor_column
        # Extract the usable descriptor kinds
        v = descriptions[descriptor_column][average_descriptor.keys()].values

        if judge_strategy == 'euclidian':
            distances = (v-av_v)**2
            distances = distances.sum()
            dist = numpy.sqrt(distances)

            groups_by_distance_to_average.append((descriptor_column, dist, descriptions[descriptor_column]))

        elif judge_strategy == 'relative':
            pass
            #v_by_m = numpy.divide(v, av_v)
            #dist = numpy.linalg.norm()
            #groups_by_distance_to_average.append((descriptor_column, dist, descriptions[descriptor_column]))
        else:
            raise Exception("Unsupported judge strategy!")

    groups_by_distance_to_average.sort(key=operator.itemgetter(1), reverse=False)

    print groups_by_distance_to_average

    print "av_v = \n%s" % av_v


# Define what data to load
NAMESPACE = 'geveko_de'
DEVICE_UID = 'ghost131'
FIELD_NAME = 'bat_mvolt'

# Or for an absolute date, you could do this:
from_time = datetime.datetime.strptime('2014-09-01T00:00:00.0', ISO8601)
to_time = datetime.datetime.strptime('2014-11-01T00:00:00.0', ISO8601)

# Load the data
pandas_series = analyser.load_to_series(NAMESPACE, DEVICE_UID, FIELD_NAME, from_time, to_time)

descriptions = group_and_describe(pandas_series.to_frame(), grouping='DAILY')

result = arrange_by_distance(descriptions)

print result
