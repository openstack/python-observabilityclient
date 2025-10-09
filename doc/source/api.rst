The :mod:`observabilityclient` Python API
=========================================

.. module:: observabilityclient
   :synopsis: A client for the Prometheus API.

.. currentmodule:: observabilityclient

Usage
-----

To use observabilityclient in a project::

    >>> from observabilityclient import client
    >>> obs_client = client.Client('1', session, adapter_options=adapter_opts)
    >>> obs_client.query.list()

To have queries scoped to a single project (for restricting unprivileged
access to metrics from other projects)::

    >>> # Assuming you have client created following previous example
    >>> from observabilityclient import rbac as obsc_rbac
    >>> promQLRbac = obsc_rbac.PromQLRbac(
    >>>    obs_client.prometheus_client,
    >>>    project_id
    >>> )
    >>> scoped_query = promQLRbac.modify_query(query)

Reference
---------

For more information, see the reference:

.. toctree::
   :maxdepth: 2

   ref/v1/index
   ref/index

