from logging import getLogger

from aiohttp.web import json_response
from django.contrib.postgres.fields import JSONField
from django.db import models

from pulpcore.plugin.models import (
    BaseModel,
    Content,
    Publication,
    PublicationDistribution,
    Remote,
    Repository
)

from pathlib import PurePath
from .utils import python_content_to_json, PYPI_LAST_SERIAL, PYPI_SERIAL_CONSTANT

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


class PythonDistribution(PublicationDistribution):
    """
    Distribution for 'Python' Content.
    """

    TYPE = 'python'

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


class PythonPackage(BaseModel):
    """
    Holder for Python Package Metadata

    As defined in pep-0426 and pep-0345.

    https://www.python.org/dev/peps/pep-0491/
    https://www.python.org/dev/peps/pep-0345/
    """
    name = models.TextField(editable=False)
    # Info Metadata
    author = models.TextField()
    author_email = models.TextField()
    bugtrack_url = models.TextField()
    classifiers = JSONField(default=list)
    description = models.TextField()
    description_content_type = models.TextField()
    docs_url = models.TextField()
    download_url = models.TextField()
    # downloads - not used
    home_page = models.TextField()
    keywords = models.TextField()
    license = models.TextField()
    maintainer = models.TextField()
    maintainer_email = models.TextField()
    package_url = models.TextField()
    platform = models.TextField()
    project_url = models.TextField()
    project_urls = JSONField(default=dict)
    release_url = models.TextField()
    requires_dist = JSONField(default=list)
    requires_python = models.TextField()
    summary = models.TextField()
    version = models.TextField()  # This is current latest release
    # yanked and yanked reason are no longer used
    # Should I include last_serial here?

    class Meta:
        unique_together = ("name",)


class PythonPackageContent(Content):
    """
    A Content Type representing Python's Distribution Package.
    """

    TYPE = 'python'
    name = models.TextField() # I should lookup how long this can be
    count = models.IntegerField()
    combined_hash = models.CharField(max_length=64)
    package = models.ForeignKey(PythonPackage, on_delete=models.CASCADE, editable=False)


    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ('combined_hash', 'name')


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

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class PythonRepository(Repository):
    """
    Repository for "python" content.
    """

    TYPE = "python"
    CONTENT_TYPES = [PythonPackageContent]
    REMOTE_TYPES = [PythonRemote]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
