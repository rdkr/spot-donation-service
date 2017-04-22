import boto3
import gzip
import os
import urllib.parse
from influxdb import InfluxDBClient
from influxdb import SeriesHelper


BUCKETNAME = 'team-victory-spot-instance-data-feed-lambda'
FILENAME = '063261902513.2017-04-22-05.001.rb6SAEry.gz'

def getEstateData():
    print('Get Estate Data from S3 => InfluxDB')
    _s3 = boto3.resource('s3')

    _bucket = _s3.Bucket(BUCKETNAME)

    for item in _bucket.objects.all():
        pprint.pprint(item)

    _local_file_path = os.path.join('/tmp', FILENAME)
    _bucket.download_file(FILENAME, _local_file_path)

    i = 0
    with gzip.open(_local_file_path) as _file:
        data = [None]*2 #TODO: make this work for the actual number of lines
        for line in _file:
            dline = line.decode("utf-8")
            if '#' in dline:
                continue
            data[i] = dline.replace('\n', '').split('\t')
            i += 1
        return data


client = boto3.client("ec2")

# InfluxDB connections settings
host = '54.246.255.79'
port = 8086
user = ''#'root'
password = ''#'root'
dbname = 'mydb'

myclient = InfluxDBClient(host, port, user, password, dbname)

class MySeriesHelper(SeriesHelper):
    # Meta class stores time series helper configuration.
    class Meta:
        # The client should be an instance of InfluxDBClient.
        client = myclient
        # The series name must be a string. Add dependent fields/tags in curly
        # brackets.
        series_name = 'events.stats.{region}'
        # Defines all the fields in this time series.
        fields = ['Timestamp', 'UsageType', 'Operation', 'InstanceID',
                  'MyBidID', 'MyMaxPrice', 'MarketPrice', 'ChangeVersion']
        # Defines all the tags for the series.
        tags = ['region']
        # Defines the number of data points to store prior to writing on the
        # wire.
        bulk_size = 2
        # autocommit must be set to True when using bulk_size
        autocommit = True


# The following will create *five* (immutable) data points.
# Since bulk_size is set to bulk_size, upon the fifth construction call,
# *all* data points will be written on the wire via MySeriesHelper.Meta.client.
for d in getEstateData():
    MySeriesHelper(region='eu-west-1',
                   Timestamp=d[0],
                   UsageType=d[1],
                   Operation=d[2],
                   InstanceID=d[3],
                   MyBidID=d[4],
                   MyMaxPrice=d[5],
                   MarketPrice=d[6],
                   ChangeVersion=d[7]
                  )
    print(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7])

# To manually submit data points which are not yet written, call commit:
MySeriesHelper.commit()

# To inspect the JSON which will be written, call _json_body_():
MySeriesHelper._json_body_()