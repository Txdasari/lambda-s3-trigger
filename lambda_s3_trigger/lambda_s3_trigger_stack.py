from aws_cdk import (
    # Duration,
    Stack,
    Tags,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications,
    # aws_sqs as sqs,
)
from constructs import Construct

class LambdaS3TriggerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

          # create lambda function
        function = _lambda.Function(self, "lambda_function",
                                    runtime=_lambda.Runtime.PYTHON_3_9,
                                    handler="lambda-handler.main",
                                    code=_lambda.Code.from_asset("./lambda"))


        # create s3 bucket
        bucket = s3.Bucket(self, "mylambdas3")
     
        Tags.of(self).add('Application', 'Test')
        Tags.of(self).add('Environment', 'Dev')
        Tags.of(self).add('Name', 'lambdawiths3')
        Tags.of(self).add('Team', 'CloudOpsDev')

        # create s3 notification for lambda function
        notification = aws_s3_notifications.LambdaDestination(function)

        # assign notification for the s3 event type (ex: OBJECT_CREATED)
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification)
    

       
