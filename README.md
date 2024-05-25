
The purpose of this project is to generate a report containing invocation and usage details of the Amazon Bedrock models in a specific AWS region within the last 24 hours. The report will be generated automatically by an AWS Lambda function, triggered by an Amazon EventBridge rule. The report will be in CSV format and will include columns such as Account Id, Identity ARN, Model Id, Region Name, Number of Input token, Number of output token, Charges incurred. The generated CSV file will be stored in an S3 bucket, and an email attachment with the CSV file will be sent to the user using Amazon SES. This helps in automating the daily tracking and monitoring of the usage and charges incurred on all the Amazon Bedrock models by every user.

CSV columns :
Account Id, Identity ARN, Model Id, Region Name, Number of Input tokens, Number of output tokens, Charges incurred. 

Architecture Diagram:
 <img width="459" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/e6abf340-8f02-4f63-9b68-c02803588ca2">

Step 1: Create a Log group in Amazon CloudWatch.

•	Navigate to cloudwatch console and click ‘Log groups’ from the left panel and then Click “Create log group” button in right top corner.

•	Enter any name in the “Log group name” field and click create button at the right bottom corner of the page.

<img width="425" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/e5021b93-183e-4bcf-8aab-718d7ead816b">

Step 2:  Enable model invocation logging in Amazon Bedrock console and configure it with the previously created Log group name in step 1.

•	Navigate to Amazon Bedrock console and click ‘Settings’ button from the left panel at the bottom of the page. click “Model invocation logging” to enable it , select the logging destinations , enter the log group name and Click “Save settings” button in right bottom corner.
 
 <img width="428" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/84e3e358-d435-4bf9-8aad-d7c3a2f64c8a">

Step 3:  Create an AWS lambda function with the attached sample code from the python file automated-amazonbedrock-modelusage-reporting-system.py

•	Navigate to AWS Lambda dashboard and click create function button.

•	Enter the function name and choose python as runtime and click create function button.

<img width="430" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/0230bd0e-5bdc-4cc3-9796-83d89163a94b">

•	Click “Layers” from the function overview section and then click “Add a layer” button.

•	Choose “AWSSDKPandas-Python312” as AWS layers and choose latest version from version drop down and then click “Add” button.

<img width="452" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/9111dab7-fabf-4e75-93d9-f6727bfd2715">

•	Click “configuration” tab and then click “permissions” tab. Click on the Role name and it will take us to IAM and then attach policies for this Lambda function to have access to Amazon Cloudwatch, S3 bucket and Amazon SES service.

•	Click “configuration” tab and then click “general configuration” tab. Click Edit button to update the Timeout and then click save button.

•	Copy the sample code from “automated-amazonbedrock-modelusage-reporting-system.py” file and paste it in “code” section into lambda_funtion.py file and then click Deploy button.

Step 4: Create a Amazon Event Bridge rule to trigger the AWS Lambda function created in step:2, everyday at a specific time of a day.

•	https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html?icmpid=docs_console_unmapped#cron-based

•	Navigate to Amazon Event bridge console and click ‘Create rule’ button in the Amazon Event bridge home page or from the left panel click “Rules” and then Click “Create rule” button in right top corner.

•	Choose Rule type as Schedule and click Continue in EventBridge Scheduler button.

<img width="393" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/ffe468d7-7c94-4819-be96-6d1c60145b42">

•	Enter the schedule name, description and choose radio button Recurring Schedule.

<img width="452" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/58c40a2c-4ff3-483d-aca3-b0b7bef1055d">

•	Under Schedule type, choose Cron-based schedule. Enter the Cron expression, The below screenshot shows cron expression to run this schedule at everyday 2.30 a.m. Choose Flexible time window as 5 minutes and click Next.

<img width="452" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/e87508e5-760d-4784-b3b4-ca750d7320e5">

•	Choose AWS Lambda radio button and select the lambda function which we created in step 3 and click next.

•	Choose NONE from Action after schedule completion dropdown and click Next and in Review and create schedule page click the review and create.

<img width="346" alt="image" src="https://github.com/aws-samples/automated-genai-foundation-models-usage-tracking-and-reporting-system/assets/33568504/a0e5da77-3964-40e9-83db-744c8c0d4de5">

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

