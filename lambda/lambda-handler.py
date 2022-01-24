import json
import urllib.parse
import boto3
import botocore
import csv
from datetime import date, datetime
from botocore.config import Config

print('Loading function')

REPORT_REGION = "us-east-1"

sdkConfig = Config(
    region_name = REPORT_REGION,
    retries = {
        'max_attempts': 20,
        'mode': 'standard'
    }
)


#Instantiate boto3 client
securityhub = boto3.client('securityhub')
ouclient = boto3.client('organizations', config=sdkConfig)
s3 = boto3.resource('s3')

# Get all accounts for the Organization
accounts = []

#Apply filters for to get the securiyhubalerts
_filter = Filters={
    'ComplianceStatus': [
        {
            'Value': 'FAILED',
            'Comparison': 'EQUALS'
        }
    ],
    'RecordState': [
        {
            'Value': 'ACTIVE',
            'Comparison': 'EQUALS'
        }
    ],
}
_sort = SortCriteria=[
    {
        'Field': 'ComplianceStatus',
        'SortOrder': 'desc'
    },
    {
        'Field': 'SeverityNormalized',
        'SortOrder': 'desc'
    }
]
MAX_ITEMS=100
BUCKET_NAME='security-hub-bucket'


def main(event, context):
    # cannot seems to pass token = None into the get_findings() 
    result = securityhub.get_findings(
      Filters=_filter,
      SortCriteria=_sort,
      MaxResults=MAX_ITEMS
    )

    # Get the date, to set the sheet name
    today = date.today()
    d1 = today.strftime("%m-%d-%Y")

    KEY= 'SecurityHubReport '+d1+'.csv'


    #print('result', result)
   #write securityhub alerts to the csv file     
    with open("/tmp/data.csv", "w") as file:
        csv_file = csv.writer(file)
        
        keys = []
        count = 0
        while(result != None): 
            
            items = []
            findings = result['Findings']
            
            for finding in findings: 
                count += 1
                item = {}
                item['Description'] = finding['Title']
                item['Severity'] = finding['Severity']['Label']
                item['ResourceType'] = finding['Resources'][0]['Type']
                item['ResourceId'] = finding['Resources'][0]['Id']

                items.append(item)
                if (len(keys) == 0):
                    keys = list(item.keys())
                    csv_file.writerow(keys)
            
            for d in items:
                csv_file.writerow(list(d.values()))
            
            if "NextToken" in list(result.keys()):
                token = result['NextToken']
                result = securityhub.get_findings(Filters=_filter, SortCriteria=_sort, MaxResults=MAX_ITEMS, NextToken=token)
                print("resultsss", result)
            else:
                    result = None
    
    #Uplaod the csv file to the 's3' bucket
    csv_binary = open('/tmp/data.csv', 'rb').read()
    try:
        obj = s3.Object(BUCKET_NAME, KEY)
        obj.put(Body=csv_binary)
        #print("objjjj", obj)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

    s3clientTest = boto3.client('s3')
    try:
        download_url = s3clientTest.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': KEY
                },
            ExpiresIn=3600
        )
        return {
            "csv_link": download_url,
            "total": count
        }
    except Exception as e:
        raise utils_exception.ErrorResponse(400, e, Log)
    
    return {
        'message': 'Error found, please check your logs',
        'total': 0
    }