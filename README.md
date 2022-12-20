# python-observabilityclient

observabilityclient is an OpenStackClient (OSC) plugin implementation that
implements commands for management of OpenStack observability components such
as Prometheus, collectd and Ceilometer.

## Development

Install your OpenStack environment and patch your `openstack` client application using python.

```
# if using standalone, the following commands come after 'sudo dnf install -y python3-tripleoclient'

su - stack

# clone and install observability client plugin
git clone https://github.com/infrawatch/python-observabilityclient
cd python-observabilityclient
sudo python setup.py install --prefix=/usr

# clone and install observability playbooks and roles
git clone https://github.com/infrawatch/osp-observability-ansible
sudo mkdir /usr/share/osp-observability
sudo ln -s `pwd`/osp-observability-ansible/playbooks /usr/share/osp-observability/playbooks
sudo ln -s `pwd`/osp-observability-ansible/roles/spawn_container /usr/share/ansible/roles/spawn_container
sudo ln -s `pwd`/osp-observability-ansible/roles/osp_observability /usr/share/ansible/roles/osp_observability
```

### Enable collectd write_prometheus
Create a THT environment file to enable the write_prometheus plugin for the collectd service. Then redeploy your overcloud and include this new file:

```
mkdir -p ~/templates/observability
cat <EOF >> templates/observability/collectd-write-prometheus.yaml
resource_registry:
  OS::TripleO::Services::Collectd: /usr/share/openstack-tripleo-heat-templates/deployment/metrics/collectd-container-puppet.yaml

# TEST
# parameter_merge_strategies:
#   CollectdExtraPlugins: merge

parameter_defaults:
  CollectdExtraPlugins:
    - write_prometheus
EOF
```

### Discover endpoints
After deployment of your cloud you can discover endpoints available for scraping:

```
source stackrc
openstack observability discover --stack-name=standalone
```

### Deploy prometheus:
Create a config file and run the setup command

```
$ cat test_params.yaml
prometheus_remote_write:
  stf:
    url: https://default-prometheus-proxy-service-telemetry.apps.FAKE.ocp.cluster/api/v1/write
    basic_user: internal
    basic_pass: Pl4iNt3xTp4a55
    ca_cert: |
      -----BEGIN CERTIFICATE-----
      ABCDEFGHIJKLMNOPQRSTUVWXYZ
      -----END CERTIFICATE-----
  not-stf:
    url: http://prometheus-rw.example.com/api/v1/write

$ openstack observability setup prometheus_agent --config ./test_params.yaml
```
