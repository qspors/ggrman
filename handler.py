#!/usr/bin/python3
import boto3
import os
import time
from botocore.exceptions import UnknownServiceError, BotoCoreError
import logging
import datetime
import json
import hashlib
import fwmodule
import re


def config(req):
    try:
        log.info('Load options for: {}'.format(req))
        return js_config[req]
    except FileNotFoundError as e:
        log.error(e)


log = logging.getLogger('GGRMAN')
fh = logging.FileHandler('/var/log/ggrman.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(
    logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S'))
log.addHandler(fh)
log.setLevel(logging.DEBUG)
do_pull = False
path = '/etc/ggrman/config.json'

with open(path, 'r') as file:
    str_conf = file.read()
    js_config = json.loads(str_conf)


def get_ip_address():
    log.info('Get IP')
    try:
        namespace_id = ''
        namespace_list_filter = [
            {
                "Name": "TYPE",
                "Values": [
                    "DNS_PRIVATE"
                ]
            }
        ]
        service_ids = {}
        ip_address = []
        service_discovery_client = boto3.client('servicediscovery', region_name=config('REGION_NAME'))
        get_namespace_id = service_discovery_client.list_namespaces(Filters=namespace_list_filter)
        for item in get_namespace_id['Namespaces']:
            if item['Name'] == config('NAMESPACE'):
                log.info('Namespace name is: {}'.format(item['Name']))
                namespace_id = item['Id']
        namespace_filter = [
            {
                "Name": "NAMESPACE_ID",
                "Values": [
                    namespace_id
                ]
            }
        ]
        services = service_discovery_client.list_services(Filters=namespace_filter)
        for item in services['Services']:
            service_ids[item['Name']] = item['Id']
        for item in service_ids.values():
            instances_get = service_discovery_client.list_instances(ServiceId=item)
            for item_in_instance in instances_get['Instances']:
                ip_address.append(item_in_instance['Attributes']['AWS_INSTANCE_IPV4'])
        log.info('IPs is: {}'.format(ip_address))
        return ip_address
    except UnknownServiceError as e:
        log.error("get_ip_address: UnknownServiceError Error Exception: {}".format(e))


def create_xml_paths():
    log.info('Check XML path if exist')
    try:
        if os.path.isdir(config('CONFIG_PATH')) is True:
            log.info('XML path is exist')
            return True
        else:
            log.info('XML path is not exist....create new XML')
            os.makedirs(config('CONFIG_PATH'))
            create_xml_paths()
    except OSError as e:
        log.error("create_xml_path: OS Error Exception: {}".format(e))
        return False


def make_xml_template():
    log.info('Create XML template')
    try:
        host_name_tmp = ''
        for item in get_ip_address():
            host_tmp = '<host name="{}" port="{}" count="{}"/>'.format(item, config('SELENOID_PORT'),
                                                                       config('TASKS_COUNT'))
            host_name_tmp = host_name_tmp + ''.join(host_tmp)
        xml_temp = '<qa:browsers xmlns:qa="urn:config.gridrouter.qatools.ru">' \
                   '<browser name="{}" defaultVersion="{}">' \
                   '<version number="{}">' \
                   '<region name="us-east-1">' \
                   '{}' \
                   '</region>' \
                   '</version>' \
                   '</browser>' \
                   '</qa:browsers>'.format(config('BROWSER_NAME'), config('BROWSER_VER'), config('BROWSER_VER'),
                                           host_name_tmp)
        log.info('XML template is created')                                   
        return xml_temp
    except IOError as e:
        log.error("make_xml_template: IO Error Exception: {}".format(e))


def hash_function(filepath):
    block_size = 65536
    hasher = hashlib.md5()
    with open(filepath, 'rb') as xml_file:
        buffer = xml_file.read(block_size)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = xml_file.read(block_size)
    tmp_hash = hasher.hexdigest()
    return tmp_hash


def reload_ggr_container():
    try:
        ecs_client = boto3.client('ecs', region_name=config('REGION_NAME'))
        regex = ('arn')
        log.info('Get service ARNs')
        ggr_arn = \
            (ecs_client.list_tasks(cluster=config('CLUSTER_NAME'), serviceName=config('GGR_SERVICE_NAME'))).get(
                'taskArns').pop()
        ggr_ui_arn = (ecs_client.list_tasks(cluster=config('CLUSTER_NAME'),
                                            serviceName=config('GGRUI_SERVICE_NAME'))).get('taskArns').pop()
        if re.match(regex, ggr_arn) and re.match(regex, ggr_ui_arn):
            log.info('Reload containers:')
            log.info(ggr_arn)
            log.info(ggr_ui_arn)
            ecs_client.stop_task(cluster=config('CLUSTER_NAME'), task=ggr_arn)
            ecs_client.stop_task(cluster=config('CLUSTER_NAME'), task=ggr_ui_arn)
            time.sleep(10)
            log.info('Containers is reloaded , invoke firewall module')
            firewall()
    except (IndexError, BotoCoreError) as e:
        log.warning(e)
        log.warning('Sleep 10 sec')
        time.sleep(10)
        reload_ggr_container()


def firewall():
    try:
        log.info('Invoke firewall module')
        fw_changes = fwmodule.FwMod(tag_name=config('TAG_NAME'),
                                    sg_conf=config('SECURITY_GROUPS'),
                                    region=config('REGION_NAME'),
                                    envs=config('ENVS'), main_ips=config('JENKINS_IP'))
        fw_changes.run()
    except Exception as error:
        log.error(error)


def xml_config_generate():
    log.info('Generate XML')
    try:
        if create_xml_paths() is True:
            pass
        else:
            exit()
    except OSError as e:
        log.error(e)
        return False

    try:
        filepath = config('CONFIG_PATH') + config('CONFIG_NAME')
        if os.path.isfile(filepath) is True:
            log.info('XML file is exist....')
            tmp_hash = hash_function(filepath)
            log.info('Hash is: {}'.format(tmp_hash))
            with open(filepath, 'w') as xml_file:
                xml_file.write(make_xml_template())
                xml_file.close()
                new_hash = hash_function(filepath)
                log.info('New hash is: {}'.format(new_hash))
                if tmp_hash == new_hash:
                    log.info('{} = {}, PASS'.format(tmp_hash, new_hash))
                    pass
                else:
                    log.info('{} != {}, Reload container'.format(tmp_hash, new_hash))
                    reload_ggr_container()
        else:
            log.info('XML file is not exist....')
            with open(filepath, 'w') as xml_file:
                xml_file.write(make_xml_template())
                reload_ggr_container()
    except IOError as e:
        log.error("xml_config_generate: IO Error Exception: {}".format(e))


def selenoid_config_init():
    if os.path.isdir('/tmp/browsers.json') is True:
        os.rmdir('/tmp/browsers.json')
        selenoid_config_init()
    if os.path.isfile('/tmp/browsers.json') is True:
        log.info('`/tmp/browsers.json` is exist')
        log.info('Re-write this file')
        write_selenoid_config(make_selenoid_config())
    else:
        log.info('`/tmp/browsers.json` Is not exist')
        log.info('`/tmp/browsers.json` Create new selenoid config file')
        write_selenoid_config(make_selenoid_config())


def make_selenoid_config():
    log.info('Create selenoid template')
    try:
        image = "selenoid/{}:{}".format(config('BROWSER_NAME'), config('BROWSER_VER'))
        port = "{}".format(config('SELENOID_PORT'))
        selenoid_temp = json.dumps(
            {
                config('BROWSER_NAME'): {
                    "default": config('BROWSER_VER'),
                    "versions": {
                        config('BROWSER_VER'): {
                            "image": image,
                            "port": port,
                            "tmpfs": {"/tmp": "size=512m"},
                            "path": "/"
                        }
                    }
                }
            }
        )
        log.info('Selenoid config created')
        return selenoid_temp
    except IOError as e:
        log.error("make_xml_template: IO Error Exception: {}".format(e))


def write_selenoid_config(payload):
    log.info('Write selenoid files')
    try:
        log.info('Write data to bworsers.json file')
        with open('/tmp/browsers.json', 'w') as file:
            file.write(payload)
            log.info('Data is written')
            file.close()
            log.info(datetime.datetime.now().strftime("%m%d%y%H%M%S"))
    except BaseException as e:
        log.error(e)


def docker_container_pull():
    global do_pull
    try:
        log.info('Check docker service')
        status = os.system('systemctl is-active --quiet docker.service')
        log.info('Docker status: {}'.format(status))
        if status == 0:
            log.info('Docker is active, pull images')
            if do_pull is True:
                log.info(
                    'Docker container selenoid/{}:{} has been pulled'.format(config('BROWSER_NAME'),
                                                                             config('BROWSER_VER')))
            else:
                log.info('Pull docker container')
                cmd = 'docker pull selenoid/{}:{}'.format(config('BROWSER_NAME'), config('BROWSER_VER'))
                os.system(cmd)
                log.info('Container is pulled')
                do_pull = True
        if status == 768:
            log.warning('Docker is not active, please wait 30 sec')
            time.sleep(30)
            docker_container_pull()
    except OSError as e:
        log.error(e)


def run():
    try:
        start_time = time.time()
        docker_container_pull()
        log.info('Daemon start')
        while True:
            xml_config_generate()
            selenoid_config_init()
            time.sleep(55 - ((time.time() - start_time) % 55))
    except RuntimeError as e:
        log.error("RUN : Runtime error: {}".format(e))


if __name__ == "__main__":
    run()
