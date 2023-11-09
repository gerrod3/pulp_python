.. _sync-workflow:

Synchronize a Repository
========================

Users can populate their repositories with content from an external source like PyPI by syncing
their repository.

.. _versioned-repo-created:

Create a Repository
-------------------

.. literalinclude:: ../_scripts/repo.sh
   :language: bash

Repository Create Response::

   {
      "pulp_href": "/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/",
      "pulp_created": "2021-03-09T04:11:54.347921Z",
      "versions_href": "/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/versions/",
      "pulp_labels": {},
      "latest_version_href": "/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/versions/0/",
      "name": "foo",
      "description": null,
      "remote": null
    }

Reference (pulpcore): `Repository API Usage
<https://docs.pulpproject.org/pulpcore/restapi.html#tag/Repositories>`_

.. _create-remote:

Create a Remote
---------------

Creating a remote object informs Pulp about an external content source. In this case, we will be
using a fixture, but Python remotes can be anything that implements the PyPI API. This can be PyPI
itself, a fixture, or even an instance of Pulp 2.

.. literalinclude:: ../_scripts/remote.sh
   :language: bash

Remote Create Response::

    {
      "pulp_href": "/pulp/api/v3/remotes/python/python/a9bb3a02-c7d2-4b2e-9b66-050a6c9b7cb3/",
      "pulp_created": "2021-03-09T04:14:02.646835Z",
      "name": "bar",
      "url": "https://pypi.org/",
      "ca_cert": null,
      "client_cert": null,
      "tls_validation": true,
      "proxy_url": null,
      "pulp_labels": {},
      "pulp_last_updated": "2021-03-09T04:14:02.646845Z",
      "download_concurrency": 10,
      "policy": "on_demand",
      "total_timeout": null,
      "connect_timeout": null,
      "sock_connect_timeout": null,
      "sock_read_timeout": null,
      "headers": null,
      "rate_limit": null,
      "includes": [
        "shelf-reader"
      ],
      "excludes": [],
      "prereleases": true,
      "package_types": [],
      "keep_latest_packages": 0,
      "exclude_platforms": [],
      "sync_dependencies": false

    }


Reference: `Python Remote Usage <../restapi.html#tag/Remotes:-Python>`_

A More Complex Remote
---------------------

If only the name of a project is specified, every distribution of every version of that project
will be synced. You can use the version_specifier field to ensure only distributions you care
about will be synced::

    $ pulp python remote create \
        --name 'complex-remote' \
        --url 'https://pypi.org/' \
        --includes '[
            "django~=2.0,!=2.0.1",
            "pip-tools>=1.12,<=2.0",
            "scipy",
            "shelf-reader"
        ]'

You can also use version specifiers to "exclude" certain versions of a project, like so::

    $ pulp python remote create \
        --name 'complex-remote' \
        --url 'https://pypi.org/' \
        --includes '[
            "django",
            "scipy"
        ]' \
        --excludes '[
            "django~=1.0",
            "scipy"
        ]'

You can also filter packages by their type, platform and amount synced through the "package_types",
"exclude_platforms", and "keep_latest_packages" fields respectively, like so::

    $ pulp python remote create \
        --name 'complex-filters' \
        --url 'https://pypi.org/' \
        --includes '["django"]' \
        --package-types '["sdist", "bdist-wheel"]' # only sync sdist and bdist-wheel package types \
        --exclude-platforms '["windows"]' # exclude any packages built for windows \
        --keep-latest-packages 5 # keep the five latest versions

Reference: `Python Remote Usage <../restapi.html#tag/Remotes:-Python>`_

.. _mirror-workflow:

Syncing Dependencies
--------------------

When specifying included packages to sync, Pulp can also sync the dependencies of those packages::

    $ pulp python remote create \
        --name 'packages-with-dependencies' \
        --url 'https://pypi.org/' \
        --sync-dependencies # Enable syncing dependencies for included packages \
        --includes '[
            "django>=4.0", # Sync the dependencies for each django version >=4.0
            "pulpcore[s3]", # Sync the dependencies for all pulpcore versions + extra dependencies for s3
        ]'

Turning on dependency syncing will only sync the necessary dependencies to install the package for the
given versions declared in the includes list. You can sync the extra dependencies of a package by
using the `extras notation <https://peps.python.org/pep-0508/#extras>`_. Synced dependencies are also
filtered through the other filters defined on the remote. Note that many packages have unrestricted
dependencies which can cause syncs to become significantly larger than normal. It is recommended
to use extra filters to trim any unwanted packages.

.. warning:: This feature is provided as a tech preview and could change in backwards incompatible
  ways in the future.

Creating a remote to sync all of PyPI
_____________________________________

A remote can be setup to sync all of PyPI by not specifying any included packages like so::

    $ pulp python remote create \
        --name 'PyPI-mirror' \
        --url 'https://pypi.org/' \
        --excludes '[
            "django~=1.0",
            "scipy"
        ]'

By not setting the "includes" field Pulp will ask PyPI for all of its available packages to sync, minus the ones from
the excludes field. Default Python remotes are created with syncing policy "on_demand" because the most common
Python remotes involve syncing with PyPI which requires terabytes of disk space. This can be changed by
modifying the "policy" field.

Syncing all of PyPI can take a long time depending on your network and disk speeds. Check out
:ref:`pull-through caching <pull-through-cache>` to learn about another way to mirror PyPI.

Sync repository foo with remote
-------------------------------

Use the remote object to kick off a synchronize task by specifying the repository to
sync with. You are telling pulp to fetch content from the remote and add to the repository.

.. literalinclude:: ../_scripts/sync.sh
   :language: bash

Repository Version Show Response (when complete)::

    {
      "pulp_href": "/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/versions/1/",
      "pulp_created": "2021-03-09T04:20:21.896132Z",
      "number": 1,
      "base_version": null,
      "content_summary": {
        "added": {
          "python.python": {
            "count": 2,
            "href": "/pulp/api/v3/content/python/packages/?repository_version_added=/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/versions/1/"
          }
        },
        "removed": {},
        "present": {
          "python.python": {
            "count": 2,
            "href": "/pulp/api/v3/content/python/packages/?repository_version=/pulp/api/v3/repositories/python/python/8fbb24ee-dc91-44f4-a6ee-beec60aa542d/versions/1/"
          }
        }
      }
    }




Reference: `Python Sync Usage <../restapi.html#operation/repositories_python_python_sync>`_

Reference (pulpcore): `Repository Version Creation API Usage
<https://docs.pulpproject.org/pulpcore/restapi.html#operation/repository_versions_list>`_
