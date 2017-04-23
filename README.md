# **spot-donation-service**

This is an entry for the [Cloudreach](https://www.cloudreach.com/) **.create(v=2.0) hackathon**, April 2017 from Team Victory - [rdkr](https://github.com/rdkr), [jmuldoon](https://github.com/jmuldoon), [danieljsmythe](https://github.com/danieljsmythe).

Note that this repo is provided primarily for judging, and so some of the links are internal to Cloudreach only.

## Abstract

To take excess spendng in AWS and give back to charities. Excess in this case can be the inefficient, unrequired, over uitlized, or space capacity. This can be leveraged in many ways, but for the initial PoC/MVP we focused specifially with AWS Spot EC2 Instances. The goal being to create a *Charity Price* in addition to the normal *AWS Max Bid Price*, which determiens how much a company is willing to pay. The concept of charity pricing is that the company/owner will always pay this amount for a spot instance. This *Charity Price* is less than the *On Demand Price* (normal price a company/owner pays for EC2), thus the company/owner would still save money. However, the differential between the live *Strike Price* of the instance and the *Charity Price* will be given to a charity of the company/owner's choosing.

Links:

  1. Wiki: [Simple Donation Service](https://cloudreach.jira.com/wiki/x/T-1TCg)
  1. Roadmap: [Trello](https://trello.com/b/GcOj7RRe/spot-donation-service)

## Deployment - Setup

In order for a quick deployment of the system please use utilize AWS's Cloudformation Service to create a new stack using the below supported template.

`./template/simple_donation_service.json`

There are some manual steps still necessary as the cross region support for some of the new services were unavailable at the time of making this PoC/MVP. This includes the initial AWS S3 Bucket creation for the importing of the [Spot Instance Data Feed](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-data-feeds.html). Additional setup was performed to add versioning to both this *Spot Instance Data Feed* bucket and the *Lambda Processing* Bucket (which is created in the cloud formation template provided) so that the former could replicate to the latter. The reasoning for using both buckets was for prototyping, and avoiding destroying our obtained data while we were working, which wouldn't be necessary for a production system.

Additionally, packaging of the lambda was done through *Zappa*, and manually deployed (with future intent on making this all part of the CloudFormation template). Thus, the setup of the event trigger for a newly added report to the *Lambda Processing* bucket would kick this lambda off (see *Lambda Section* for more information).

Installation of *InfluxDB* and *Grafana* should be done on the data instance that is created via the template.

1. [InfluxDB](https://docs.influxdata.com/influxdb/v1.2/introduction/installation/)
1. [Grafana](http://docs.grafana.org/installation/)
1. [NGINX](https://www.nginx.com/resources/wiki/start/topics/tutorials/install/) - nginx.conf in this repo
1. [ACME Cert](https://github.com/Neilpang/acme.sh) - for ssh cert

Finally, in order to allow for the lamda to run appropriately, a NAT needs to be opened up for the lambda to reach out the public API.

AMI `ami-b24e4fd4` in `cr-create` is a snapshot of the server running these services at the time of submission.

## **Lambda**
The lambda will ingest the *.gz file that is directed via the bucket event trigger. The ingestion will parse out the relevant data and format it so that it can be received in a readable format by InfluxDB. Additionally, the *On Demand* pricing will be retrieved and associated by instance type along with the aforementioned data export to the db.

## **Grafana**
This is our frontend and will display the relevant queries that are setup, and is available to create new queries based on the data that is present now in influxDB.

## **Automation**
Currently *Master* branch has a few hardcoded values due to time constraints, but the logic is sitting on the *Develop* branch ready for merge. The NAT isn't fully setup, so for the essence of the PoC to be fully functional for testing, it will be required at a later time for merge.
