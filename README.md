# ggrman
Selenoid manager
## Description.
This scripts updating selenoid config and propogate this config for grid control and gridcontrol ui.
Optionally fwmodule changing your SG for access from AWS EC2 instances where working your docker containers to WEB resourse which you testing.
You can use CloudFormation template for spin-up new envinroment based on AWS ECS, for keeping Docker images please use AWS ECR.
For update SG need to use AWS API Gateway and Lambda function. This lambda function let you change SG even if this SG in another AWS Account or region.
## Installation
1) Create lambda function, use sgChanger like source.
2) Create IAM role and policy, associate this with lambda fucntion. Specify which sg will be changed thru this lambda:
```
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "VisualEditor0",
#             "Effect": "Allow",
#             "Action": [   
#                 "ec2:AuthorizeSecurityGroupIngress",
#                 "ec2:UpdateSecurityGroupRuleDescriptionsIngress"
#             ],
#             "Resource": [
#                 "arn:aws:ec2:*:*:security-group/sg-xxxxxxxxxxxxxx",
#                 "arn:aws:ec2:*:*:security-group/sg-xxxxxxxxxxxxxx",
#                 "arn:aws:ec2:*:*:security-group/sg-xxxxxxxxxxxxxx"
#             ]
#         },
#         {
#             "Sid": "VisualEditor1",
#             "Effect": "Allow",
#             "Action": [
#                 "ec2:DescribeSecurityGroupReferences",
#                 "ec2:DescribeSecurityGroups"
#             ],
#             "Resource": "*"
#         }
#     ]
# }
```
3) Create API, associate this with sgChanger Lambda, create route(optional), create POST method, apply API-Key to Usage plan,        associate usage plan with deployment. Put API-key and url to config.json
4) Create SG and associate this SG with web resourses which will be on tests like your web site. put IDs of this SG to          config.json
5) Create S3 bucket and put to this bucket handler.py , fwmodule.py , config.json and s3_userconfig.sh, change config.json      and s3_userconfig.sh if needed, deactivate firewall() method inside handler.py if not need to change SG.
6) Prepare ECR repository for docker images. Put "selenoid", "grid control", "selenoidui" and "grid control-ui" images to ECR.
   Replace ECR urls for containers inside CF template if needed.
7) Examine cloudformation template and replace options and env variables if needed.
8) Build new envinronment thru CF.

### This is alpha version, py modules is not optimized and under revision.
### You use this solution at one's own risk.
#### All questions thru email: qspors@gmail.com
    
