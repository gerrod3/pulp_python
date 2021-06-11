import requests
from logging import getLogger

from aiohttp.web import json_response
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models

from pulpcore.plugin.models import (
    Content,
    Publication,
    Distribution,
    Remote,
    Repository
)

from pathlib import PurePath
from pypi_simple import parse_filename
from wheel_filename import parse_wheel_filename
from .utils import python_content_to_json, PYPI_LAST_SERIAL, PYPI_SERIAL_CONSTANT, parse_project_metadata, get_project_metadata_from_artifact
from pulpcore.plugin.repo_version_utils import remove_duplicates, validate_repo_version

log = getLogger(__name__)


PACKAGE_TYPES = (
    ("bdist_dmg", "bdist_dmg"),
    ("bdist_dumb", "bdist_dumb"),
    ("bdist_egg", "bdist_egg"),
    ("bdist_msi", "bdist_msi"),
    ("bdist_rpm", "bdist_rpm"),
    ("bdist_wheel", "bdist_wheel"),
    ("bdist_wininst", "bdist_wininst"),
    ("sdist", "sdist"),
)

PLATFORMS = (("windows", "windows"),
             ("macos", "macos"),
             ("freebsd", "freebsd"),
             ("linux", "linux"))


class PythonDistribution(Distribution):
    """
    Distribution for 'Python' Content.
    """

    TYPE = 'python'

    allow_uploads = models.BooleanField(default=True)

    def content_handler(self, path):
        """
        Handler to serve extra, non-Artifact content for this Distribution

        Args:
            path (str): The path being requested
        Returns:
            None if there is no content to be served at path. Otherwise a
            aiohttp.web_response.Response with the content.
        """
        path = PurePath(path)
        name = None
        version = None
        if path.match("pypi/*/*/json"):
            version = path.parts[2]
            name = path.parts[1]
        elif path.match("pypi/*/json"):
            name = path.parts[1]
        if name:
            package_content = PythonPackageContent.objects.filter(
                pk__in=self.publication.repository_version.content,
                name__iexact=name
            )
            # TODO Change this value to the Repo's serial value when implemented
            headers = {PYPI_LAST_SERIAL: str(PYPI_SERIAL_CONSTANT)}
            json_body = python_content_to_json(self.base_path, package_content, version=version)
            if json_body:
                return json_response(json_body, headers=headers)

        return None

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class PythonPackageContent(Content):
    """
    A Content Type representing Python's Distribution Package.

    As defined in pep-0426 and pep-0345.

    https://www.python.org/dev/peps/pep-0491/
    https://www.python.org/dev/peps/pep-0345/
    """

    TYPE = 'python'
    repo_key_fields = ("filename",)
    # Required metadata
    filename = models.TextField(db_index=True)
    packagetype = models.TextField(choices=PACKAGE_TYPES)
    name = models.TextField()
    version = models.TextField()
    sha256 = models.CharField(unique=True, db_index=True, max_length=64)
    # Optional metadata
    python_version = models.TextField()
    metadata_version = models.TextField()
    summary = models.TextField()
    description = models.TextField()
    keywords = models.TextField()
    home_page = models.TextField()
    download_url = models.TextField()
    author = models.TextField()
    author_email = models.TextField()
    maintainer = models.TextField()
    maintainer_email = models.TextField()
    license = models.TextField()
    requires_python = models.TextField()
    project_url = models.TextField()
    platform = models.TextField()
    supported_platform = models.TextField()
    requires_dist = JSONField(default=list)
    provides_dist = JSONField(default=list)
    obsoletes_dist = JSONField(default=list)
    requires_external = JSONField(default=list)
    classifiers = JSONField(default=list)
    project_urls = JSONField(default=dict)
    description_content_type = models.TextField()

    @staticmethod
    def init_from_artifact_and_relative_path(artifact, relative_path):
        """Used when downloading package from pull-through cache."""
        path = PurePath(relative_path)
        metadata = get_project_metadata_from_artifact(path.name, artifact)
        data = parse_project_metadata(vars(metadata))
        data['packagetype'] = metadata.packagetype
        data['version'] = metadata.version
        data['filename'] = path.name
        data["sha256"] = artifact.sha256
        return PythonPackageContent(**data)

    def __str__(self):
        """
        Provide more useful repr information.

        Overrides Content.str to provide the distribution version and type at
        the end.

        e.g. <PythonPackageContent: shelf-reader [version] (whl)>

        """
        return '<{obj_name}: {name} [{version}] ({type})>'.format(
            obj_name=self._meta.object_name,
            name=self.name,
            version=self.version,
            type=self.packagetype
        )

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("sha256",)


class PythonPublication(Publication):
    """
    A Publication for PythonContent.
    """

    TYPE = 'python'

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class PythonRemote(Remote):
    """
    A Remote for Python Content.

    Fields:

        prereleases (models.BooleanField): Whether to sync pre-release versions of packages.
    """

    TYPE = 'python'
    prereleases = models.BooleanField(default=False)
    includes = JSONField(default=list)
    excludes = JSONField(default=list)
    package_types = ArrayField(models.CharField(max_length=15, blank=True),
                               choices=PACKAGE_TYPES, default=list)
    keep_latest_packages = models.IntegerField(default=0)
    exclude_platforms = ArrayField(models.CharField(max_length=10, blank=True),
                                   choices=PLATFORMS, default=list)

    @staticmethod
    def construct_url(filename):
        """Build the redirect url for package on PyPI."""
        name, _, ptype = parse_filename(filename)
        if not name:
            return None  # Failed to parse filename
        # TODO Support more package types
        if ptype == "wheel":
            pwf = parse_wheel_filename(filename)
            python_version = pwf.python_tags[0] if pwf else "py3"  # default python3 package
            if python_version[1] == "y" and "py2" in python_version:  # Avoid cp, pp, etc..
                python_version = "2.7" if python_version == "py2" else ".".join(python_version[2:])
        elif ptype == "wininst":
            python_version = filename.rsplit("py", 1)[1][:3]
        else:
            python_version = "source"
        return f"packages/{python_version}/{name[0]}/{name}/{filename}"

    def get_remote_artifact_url(self, relative_path=None):
        """Get url for remote_artifact, special case for PyPI."""
        path = PurePath(relative_path)
        if path.parts[0] != "simple":
            if "pypi.org" in self.url:
                # PyPI hosts all of their packages at https://files.pythonhosted.org
                if len(path.parts) == 1:
                    # Construct the url needed from package filename
                    url = self.construct_url(path.name)
                    if url:
                        return requests.head(f"https://files.pythonhosted.org/{url}").url
                return f"https://files.pythonhosted.org/{relative_path}"
        return super().get_remote_artifact_url(relative_path)

    def get_remote_artifact_content_type(self, relative_path=None):
        """Return PythonPackageContent."""
        return PythonPackageContent

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class PythonRepository(Repository):
    """
    Repository for "python" content.
    """

    TYPE = "python"
    CONTENT_TYPES = [PythonPackageContent]
    REMOTE_TYPES = [PythonRemote]

    autopublish = models.BooleanField(default=False)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"

    def on_new_version(self, version):
        """
        Called when new repository versions are created.

        Args:
            version: The new repository version
        """
        super().on_new_version(version)

        # avoid circular import issues
        from pulp_python.app import tasks

        if self.autopublish:
            tasks.publish(repository_version_pk=version.pk)

    def finalize_new_version(self, new_version):
        """
        Remove duplicate packages that have the same filename.
        """
        remove_duplicates(new_version)
        validate_repo_version(new_version)
