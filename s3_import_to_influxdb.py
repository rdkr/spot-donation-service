""" Team Victory

Lambda to process Spot Price Data Feed data for InfluxDB.

Build with `zappa package`.

"""

import gzip
import pprint

import boto3
import influxdb


def lambda_handler(event, context):

    """
    Lambda function to parse a Spot Price Data Feed file,
    perform the required calculations for reporting, and
    push the information to InfluxDB
    """

    # get the bucket and key name of the object which triggered the lambda
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_key = event['Records'][0]['s3']['object']['key']

    # create s3 client and download the triggering file
    s3_client = boto3.client('s3')
    s3_client.download_file(s3_bucket, s3_key, "/tmp/" + s3_key)

    # list to contain data to be sent to influx
    json_data = []

    # list of keys in data from AWS
    data_keys = ['Timestamp', 'UsageType', 'Operation', 'InstanceID',
                 'MyBidID', 'MyMaxPrice', 'MarketPrice', 'Charge', 'Version']

    # list of keys we will calculate
    calcuated_keys = ['on_demand', 'bid', 'spot', 'charity',
                      'donated', 'savings', 'paid']

    # dict to contain calculated totals
    total = {}

    # populate totals with 0s so we can increment as we read the data
    for key in calcuated_keys:
        total[key] = 0

    # open the downloaded data file
    with gzip.open("/tmp/" + s3_key) as _file:

        # read each line of the file
        for line in _file:

            # decode the file and ignore it if it is a comment
            dline = line.decode("utf-8")
            if '#' in dline:
                continue

            # create a dictionary with keys from above and values from spliting the data line
            data = dict(zip(data_keys, dline.replace(" USD", "").replace('\n', '').split('\t')))

            # parse the timestamp to required format and parse instance type
            time = data['Timestamp'].replace(" UTC", "Z").replace(" ", "T")
            instance_type = data['UsageType'].split(":")[1]

            # hardcodeded on_demand data for now
            data['on_demand'] = 0.702 if instance_type == "g2.2xlarge" else 0.741

            # cast collected numerial data to floats
            data['bid'] = float(data['MyMaxPrice'])
            data['spot'] = float(data['Charge'])

            # perform calculations and store in data
            data['charity'] = float(data['MyMaxPrice']) * 0.7
            data['donated'] = (data['charity'] - data['spot']
                               if data['spot'] < data['charity'] else 0)
            data['paid'] = data['charity'] if data['charity'] > data['spot'] else data['spot']
            data['savings'] = data['on_demand'] - data['paid']

            # add the data to the total
            for key in calcuated_keys:
                total[key] = total[key] + data[key]

            # construct the json for this data line
            json = {
                "measurement": "spot_data",
                "tags": {
                    "region": "eu-west-1",
                    "id": instance_type
                },
                "time": time,
                "fields": data
            }

            # append the data to the data to send
            json_data.append(json)

        # after reading all lines, construct json with totals
        json = {
            "measurement": "spot_totals",
            "tags": {
                "region": "eu-west-1"
            },
            "time": time,
            "fields": total
        }

        # append data with totals to data to send
        json_data.append(json)

    # print data to send
    pprint.pprint(json_data)

    # set the db name
    dbname = 'spot99'

    # create the influx db connection
    client = influxdb.InfluxDBClient('172.31.23.241', 8086, '', '', dbname)

    # create the db if it doesn't exist
    print(client.create_database(dbname))

    # post the data to the database
    print(client.write_points(json_data))
