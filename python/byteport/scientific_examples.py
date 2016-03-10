from byteport.scientific import TimeseriesAnalyser
import datetime

now = datetime.datetime.now()

USERNAME = 'hans'
PASSWORD = 'h444ns'

# Create the TimeseriesAnalyser object, this will connect to Byteport
analyser = TimeseriesAnalyser(USERNAME, PASSWORD)

# Define what data to load
NAMESPACE = 'system'
DEVICE_UID = 'ferdinand-boss'
FIELD_NAME = 'mfpt'

# Define the timespan
from_time = now - datetime.timedelta(days=7)
to_time = now

# Load the data
pandas_series = analyser.load_to_series(NAMESPACE, DEVICE_UID, FIELD_NAME, from_time, to_time)

# Convert to DataFrame
df = pandas_series.to_frame()

split_descriptions_daily = analyser.split_describe(df, 'DAILY')
split_descriptions_hourly = analyser.split_describe(df, 'HOURLY')

