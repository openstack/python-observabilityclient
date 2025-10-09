The :program:`observabilityclient` openstack client extension
=============================================================

.. program:: observabilityclient
.. highlight:: bash

The :program:`observabilityclient` openstack client extension interacts with Prometheus API
from the command line. It supports the same subset of Prometheus API as the
observabilityclient python API.

.. warning::

   This client commands conflict with the gnocchiclient commands.
   Make sure to have only one of these clients installed at a time

All shell commands take the form::

    openstack metric <command> [arguments...]

Run :program:`openstack metric --help` to get a full list of all possible commands,
and run :program:`openstack metric <command> --help` to get detailed help for that
command.

Examples
--------

List all accessible metrics::

    openstack metric list

Show details of the ceilometer_cpu metric::

    openstack metric show ceilometer_cpu

Send any PromQL query::

    openstack metric query 'ceilometer_cpu{counter="cpu",job="ceilometer"} + on (counter, job) sum by (counter) (ceilometer_memory{label="baz",counter="NS",pod="POD"})'

