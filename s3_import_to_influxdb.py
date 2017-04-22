import gzip

import boto3
import influxdb


def lambda_handler(event, context):

    s3_client = boto3.client('s3')

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    s3_client.download_file(bucket, key, "/tmp/" + key)

    json_data = []

    total_bid = 0
    total_spot = 0

    keys = ['Timestamp', 'UsageType', 'Operation', 'InstanceID',
            'MyBidID', 'MyMaxPrice', 'MarketPrice', 'Charge', 'Version']

    with gzip.open("/tmp/" + key) as _file:
    # with gzip.open("data/063261902513.2017-04-21-23.001.GkNgzTrh.gz") as _file:
        for line in _file:

            dline = line.decode("utf-8")

            if '#' in dline:
                continue

            data = dict(zip(keys, dline.replace(" USD", "").replace('\n', '').split('\t')))
            data['Charge'] = float(data['Charge'])
            data['MyMaxPrice'] = float(data['MyMaxPrice'])
            data['MarketPrice'] = float(data['MarketPrice'])
            data['difference'] = data['MyMaxPrice'] - data['MarketPrice']

            instance_type = data['UsageType'].split(":")[1]

            # hardcodeded data for now:
            data['OnDemand'] = 0.702 if instance_type == "g2.2xlarge" else 0.741
            time = data['Timestamp'].replace(" UTC", "Z").replace(" ", "T")

            json = {
                "measurement": "spot_data",
                "tags": {
                    "region": "eu-west-1",
                    "id": instance_type
                },
                "time": time,
                "fields": data
            }

            json_data.append(json)

            total_bid = total_bid + data['MyMaxPrice']
            total_spot = total_spot + data['MarketPrice']

        json = {
            "measurement": "spot_totals",
            "tags": {
                "region": "eu-west-1"
            },
            "time": time,
            "fields": {
                "total_bid": total_bid,
                "total_spot": total_spot,
                "difference": 0 if total_bid - total_spot < 0 else total_bid - total_spot
            }
        }

        json_data.append(json)

    import pprint
    pprint.pprint(json_data)

    host = '172.31.23.241'
    # host = '54.246.255.79'
    port = 8086
    user = ''
    password = ''
    dbname = 'spotty'

    client = influxdb.InfluxDBClient(host, port, user, password, dbname)
    print(client.create_database(dbname))
    print(client.write_points(json_data))

# lambda_handler(None, None)
