
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
import pandas_profiling

ISO8601 = '%Y-%m-%dT%H:%M:%S.%f'

class ByteportPandas:

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

    def split_describe(self, data_frame, grouping='DAILY'):
        """
        Split the series into chunks of _hours_ and describe() them individually

        :param series:
        :param hours:
        :return:
        """

        DFList = []

        if grouping == 'DAILY':
            grouping = [data_frame.index.date]
        elif grouping == 'HOURLY':
            grouping = [data_frame.index.date, data_frame.index.hour]
        else:
            raise Exception("Unsupported grouping, '%s'" % grouping)

        for group in data_frame.groupby(grouping):
            DFList.append(group)

        descriptions = []
        for group_time, grouped_data_frame in DFList:
            descriptions.append((group_time, grouped_data_frame.describe()))

        return descriptions

    def print_pandas_profiling_report(self, pandas_series, series_name):
        pandas_data_frame = pandas_series.to_frame(series_name)

        print "Pandas Profiling for : %s " % series_name
        profile_report = pandas_profiling.describe(pandas_data_frame)
        print profile_report

