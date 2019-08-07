# ggrman
Selenoid manager
1) Create lambda function, use sgChanger
2) Create IAM role and policy and associate with lambda fucntion. Specify which sg will changed thru this lambda:
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
3) 
