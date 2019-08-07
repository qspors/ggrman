#cloud-boothook
#!/bin/bash
#Please put this file to appropriate s3 bucket <BUCKETNAME>
mkdir -p /etc/ggrman
mkdir -p /opt/ggrman
htpasswd -bc /etc/grid-router/users.htpasswd test PASSWORD
aws s3 cp s3://<BUCKETNAME>/handler.py /opt/ggrman/handler.py
aws s3 cp s3://<BUCKETNAME>/fwmodule.py /opt/ggrman/fwmodule.py
aws s3 cp s3://<BUCKETNAME>/config.json /etc/ggrman/config.json
systemctl daemon-reload
systemctl enable ggrman.service
systemctl start ggrman.service
