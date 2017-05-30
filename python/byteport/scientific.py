
"""
Support-package that will leverage stored Byteport data for scientific usage, typically in
some kind of analytics case.

Main functions of this package are:

 - Show how to integrate with Byteports Web-service APIs.
 - Basic analytics and visualization using Pandas

You can use this package in your python scientific tool of choice, such as SciPy or Anaconda


INSTALLATION
============

# If not run from pandas_examples.py, install Byteport API to your Python env:
#
git clone https://github.com/iGW/byteport-api
cd byteport-api/python
python setup.py install
pip install pandas

# Pandas
#
pip install pandas

# Pandas profiling ( will install matplotlib and pandas )
#
cd /tmp
git clone https://github.com/JosPolfliet/pandas-profiling
cd pandas-profiling
python setup.py install

"""
from byteport.http_clients import ByteportHttpClient
import datetime
import pandas

ISO8601 = '%Y-%m-%dT%H:%M:%S.%f'

class ByteportPandas:
    """
    Provides base functionality for connecting and loading data into Pandas data formats

    Extend at will!
    """

    def __init__(self, username, password):
        self.client = ByteportHttpClient()
        self.client.login(username, password)
        print "Successfully logged in to Byteport!"

    def load_to_series(self, namespace, device_uid, field_name, from_time, to_time):
        timeseries_data = self.client.load_timeseries_data_range(namespace, device_uid, field_name, from_time, to_time)

        # create pandas data-frame
        timestamps = list()
        values = list()

        # Prepare by splitting the time series data into two arrays
        for row in timeseries_data['data']['ts_data']:
            try:
                dt = datetime.datetime.strptime(row['t'], ISO8601)
                fv = float(row['v'])

                timestamps.append(dt)
                values.append(fv)
            except Exception:
                print "Failed to parse data (%s), ignoring" % row

        return pandas.Series(values, timestamps)


class TimeseriesAnalyser(ByteportPandas):

    def groupby(self, data_frame, grouping='DAILY'):
        """

        Split the series into sub-sets of _hours_ or _days_ and return one vector with parameters
        describing each subset. The subset can then be clustered etc.

        :param data_frame:
        :param grouping:
        :param subset_analysis:
        :return:
        """

        if grouping == 'DAILY':
            groups = [data_frame.index.date]
        elif grouping == 'HOURLY':
            groups = [data_frame.index.date, data_frame.index.hour]
        elif grouping == 'WEEKLY':
            groups = [lambda x: x.isocalendar()[0:1]]
        else:
            raise Exception("Unsupported grouping, '%s'" % grouping)

        # Return a new DataFrame
        groups = []
        for group in data_frame.groupby(groups):
            groups.append(group)

        return groups

    def group_and_describe(self, data_frame, grouping='DAILY', subset_analysis='pandas_describe'):
        """

        Split the series into sub-sets of _hours_ or _days_ and return one vector with parameters
        describing each subset. The subset can then be clustered etc.

        :param data_frame:
        :param grouping:
        :param subset_analysis:
        :return:
        """
        grouped_data = self.groupby(data_frame, grouping)

        description_dfs = list()

        for group_time, grouped_data_frame in grouped_data:
            
            if subset_analysis == 'pandas_describe':
                # Use the full describe() vector
                subset_description = grouped_data_frame.describe()
            elif subset_analysis == 'pandas_mean_std':
                # Use only mean and std of the describe() vector
                subset_description = grouped_data_frame.describe()
            else:
                raise Exception("Unsupported vectorization method")

            if grouping == 'DAILY':
                subset_description.columns = [u'%s' % group_time[0]]
            elif grouping == 'HOURLY':
                subset_description.columns = [u'%s %s' % (group_time[0], group_time[1])]
            else:
                raise Exception("Unsupported grouping, '%s'" % grouping)

            # Extract values
            description_dfs.append(subset_description)

        concatenated = pandas.concat(description_dfs, axis=1)

        return concatenated


