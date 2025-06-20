# python-observabilityclient

observabilityclient is an OpenStackClient (OSC) plugin implementation that
implements commands for management of Prometheus.

## Development

Install your OpenStack environment and patch your `openstack` client application using python.

```
# if using standalone, the following commands come after 'sudo dnf install -y python3-tripleoclient'

su - stack

# clone and install observability client plugin
git clone https://opendev.org/openstack/python-observabilityclient.git
cd python-observabilityclient
sudo python setup.py install --prefix=/usr
```

## Usage

Use `openstack metric query somequery` to query for metrics in prometheus.

To use the python api do the following:
```
from observabilityclient import client

c = client.Client(
            '1', keystone_client.get_session(conf),
            adapter_options={
                'interface': conf.service_credentials.interface,
                'region_name': conf.service_credentials.region_name})
c.query.query("somequery")
```

## List of commands

openstack metric list - lists all metrics
openstack metric show - shows current values of a metric
openstack metric query - queries prometheus and outputs the result
openstack metric delete - deletes some metrics
openstack metric snapshot - takes a snapshot of the current data
openstack metric clean-tombstones - cleans the tsdb tombstones

## List of functions provided by the python library
c.query.list - lists all metrics
c.query.show - shows current values of a metric
c.query.query - queries prometheus and outputs the result
c.query.delete - deletes some metrics
c.query.snapshot - takes a snapshot of the current data
c.query.clean-tombstones - cleans the tsdb tombstones
