import boto3
from botocore.exceptions import CredentialRetrievalError, BotoCoreError
import json
import logging
import os
import datetime
import requests


class FwMod:
    log = logging.getLogger('FWMODULE')
    fh = logging.FileHandler('/var/log/ggrman.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)

    def __init__(self, region, sg_conf, tag_name, envs, main_ips):
        self.region = region
        self.tag_name = tag_name
        self.sg_conf = sg_conf
        self.envs = envs
        self.main_ips = main_ips

    def run(self):
        try:
            self.log.info('START CHANGE Security Group')
            aws_session = boto3.session.Session(region_name=self.region)
            self.log.info('Getting ip list')
            ip_list = self.get_public_ip_list(aws_session=aws_session, main_ips=self.main_ips)
            self.log.info('IP list is: {}'.format(ip_list))
            if len(ip_list) != 0:
                self.modify_sg(ip_list=ip_list, config=self.sg_conf, envs=self.envs)
            else:
                exit(0x1)
        except CredentialRetrievalError as e:
            self.log.error(e)
            print(e)

    def get_public_ip_list(self, aws_session, main_ips):
        try:
            self.log.info('Get public ips for SG')
            ip_list = []
            instances = aws_session.client('ec2')
            instance = instances.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [self.tag_name]}])
            data = json.dumps(instance, indent=4, sort_keys=True, default=str)
            dicts = json.loads(data)
            for items in dicts['Reservations']:
                for instances in items['Instances']:
                    for data in instances['NetworkInterfaces']:
                        r = data.get('Association', None)
                        if r is None:
                            pass
                        else:
                            ip_list.append(r.get('PublicIp') + '/32')
            self.log.info('Public IP is: {}'.format(ip_list))
            self.log.info('Jenkins IP is: {}'.format(main_ips))
            ip_list.append(main_ips + '/32')
            self.log.info('ip_list is: {}'.format(ip_list))
            return ip_list
        except BotoCoreError as e:
            self.log.error(e)
            print(e)

    def modify_sg(self, ip_list, config, envs):
        self.log.info('Modify SG, ENVS List: {}, IP List: {}'.format(envs, ip_list))
        response = ''
        for env in envs:
            try:
                self.log.info('Modify SG for ENV: {}'.format(env))
                dict_payload = {
                    "port_from": config[env]['port_from'],
                    "port_to": config[env]['port_to'],
                    "sgid_list": config[env]['sg_ids'],
                    "ip_list": ip_list,
                    "ip_proto": config[env]['proto']
                }
                self.log.info('modify {}'.format(config[env]['sg_ids']))
                self.log.info('Modify SG')
                url = config[env]['api_url']
                payload = json.dumps(dict_payload)
                headers = {
                    'Content-Type': "application/json",
                    'x-api-key': config[env]['api_x_key'],
                    'Accept': "*/*",
                    'Cache-Control': "no-cache",
                    'Host': config[env]['host'],
                    'accept-encoding': "gzip, deflate",
                    'content-length': "198",
                    'Connection': "keep-alive",
                    'cache-control': "no-cache"
                }
                self.log.info(payload)
                response = requests.request("POST", url, data=payload, headers=headers)
                self.log.info('Change SG success')
            except Exception as error:
                self.log.error(error)
                continue
        return response.text
