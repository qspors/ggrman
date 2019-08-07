import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        ip_list = body['ip_list']
        port_from = body['port_from']
        port_to = body['port_to']
        sgid_list = body['sgid_list']
        ip_proto = body['ip_proto']
        response = authorize_security_group_ingress(sgid_list=sgid_list, ip_list=ip_list,
                                                    compare_ip_list=collector(sgid_list=sgid_list),
                                                    port_from=port_from,
                                                    port_to=port_to, ip_proto=ip_proto)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except BotoCoreError as error:
        return {
            'statusCode': 500,
            'body': json.dumps('{}'.format(error))
        }


def collector(sgid_list):
    try:
        ip_data = {}
        for sg_item in sgid_list:
            ssg = {sg_item: []}
            ip_data.update(ssg)
            for item in \
                    boto3.client('ec2').describe_security_groups(
                        Filters=[{'Name': 'group-id', 'Values': [sg_item]}]).get(
                        'SecurityGroups')[0].get('IpPermissions'):
                ip_data.update(
                    {sg_item: [ips.get('CidrIp') + '{}{}'.format(item.get('FromPort'), item.get('ToPort')) for
                               ips in item.get('IpRanges')]})

        return ip_data
    except BotoCoreError as error:
        return error


def authorize_security_group_ingress(sgid_list, ip_list, port_from, port_to, ip_proto, compare_ip_list):
    ec2 = boto3.client('ec2')
    response = []
    for sg_item in sgid_list:
        try:
            for ip_item in ip_list:
                if ip_item + str(port_from) + str(port_to) in compare_ip_list.get(sg_item):
                    response.append('ip {} exist in group {}'.format(ip_item, sg_item))
                    pass
                else:
                    ec2.authorize_security_group_ingress(CidrIp=ip_item, FromPort=port_from, ToPort=port_to,
                                                         IpProtocol=ip_proto,
                                                         GroupId=sg_item)
                    response.append('ip {} not in group {}'.format(ip_item, sg_item))
        except ClientError:
            continue
    return response
