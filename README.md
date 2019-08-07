# ggrman
Selenoid manager
1) Create lambda function, use sgChanger like source.
2) Create IAM role and policy, associate this with lambda fucntion. Specify which sg will be changed thru this lambda:
{
```
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

    
