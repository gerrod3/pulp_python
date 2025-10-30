import logging
from gettext import gettext as _

from rest_framework import serializers
from pulp_python.app.utils import DIST_EXTENSIONS, SUPPORTED_METADATA_VERSIONS
from pulpcore.plugin.models import Artifact
from pulpcore.plugin.util import get_domain
from django.db.utils import IntegrityError
from packaging.version import Version, InvalidVersion

log = logging.getLogger(__name__)


class SummarySerializer(serializers.Serializer):
    """
    A Serializer for summary information of an index.
    """

    projects = serializers.IntegerField(help_text=_("Number of Python projects in index"))
    releases = serializers.IntegerField(
        help_text=_("Number of Python distribution releases in index")
    )
    files = serializers.IntegerField(help_text=_("Number of files for all distributions in index"))


class PackageMetadataSerializer(serializers.Serializer):
    """
    A Serializer for a package's metadata.
    """

    last_serial = serializers.IntegerField(help_text=_("Cache value from last PyPI sync"))
    info = serializers.JSONField(help_text=_("Core metadata of the package"))
    releases = serializers.JSONField(help_text=_("List of all the releases of the package"))
    urls = serializers.JSONField()


class PackageUploadSerializer(serializers.Serializer):
    """
    A Serializer for Python packages being uploaded to the index.
    """

    content = serializers.FileField(
        help_text=_("A Python package release file to upload to the index."),
        required=True,
        write_only=True,
    )
    action = serializers.CharField(
        help_text=_("Defaults to `file_upload`, don't change it or request will fail!"),
        default="file_upload",
        source=":action",
    )
    sha256_digest = serializers.CharField(
        help_text=_("SHA256 of package to validate upload integrity."),
        required=True,
        min_length=64,
        max_length=64,
    )
    protocol_version = serializers.IntegerField(
        help_text=_("Protocol version to use for the upload. Only version 1 is supported."),
        required=False,
        default=1,
        min_value=1,
        max_value=1,
    )
    filetype = serializers.ChoiceField(
        help_text=_("Type of artifact to upload."),
        required=False,
        choices=("bdist_wheel", "sdist"),
    )
    pyversion = serializers.CharField(
        help_text=_("Python tag for bdist_wheel uploads, source for sdist uploads."),
        required=False,
    )
    metadata_version = serializers.CharField(
        help_text=_("Metadata version of the uploaded package."),
        required=False,
    )
    name = serializers.CharField(
        help_text=_("Name of the package."),
        required=False,
    )
    version = serializers.CharField(
        help_text=_("Version of the package."),
        required=False,
    )

    def validate(self, data):
        """Validates the request."""
        action = data.get(":action")
        if action != "file_upload":
            raise serializers.ValidationError(_("We do not support the :action {}").format(action))
        file = data.get("content")
        for ext, packagetype in DIST_EXTENSIONS.items():
            if file.name.endswith(ext):
                if filetype := data.get("filetype"):
                    if filetype != packagetype:
                        raise serializers.ValidationError(
                            {
                                "filetype": _(
                                    "filetype {} does not match found filetype {} for file {}"
                                ).format(filetype, packagetype, file.name)
                            }
                        )
                break
        else:
            raise serializers.ValidationError(
                {
                    "content": _(
                        "Extension on {} is not a valid python extension "
                        "(.whl, .exe, .egg, .tar.gz, .tar.bz2, .zip)"
                    ).format(file.name)
                }
            )
        if metadata_version := data.get("metadata_version"):
            try:
                md_version = Version(metadata_version)
            except InvalidVersion:
                raise serializers.ValidationError(
                    {
                        "metadata_version": _("metadata_version {} is not a valid version").format(
                            metadata_version
                        )
                    }
                )
            else:
                if md_version not in SUPPORTED_METADATA_VERSIONS:
                    raise serializers.ValidationError(
                        {
                            "metadata_version": _("metadata_version {} is not supported").format(
                                metadata_version
                            )
                        }
                    )
        sha256 = data.get("sha256_digest")
        digests = {"sha256": sha256} if sha256 else None
        artifact = Artifact.init_and_validate(file, expected_digests=digests)
        try:
            artifact.save()
        except IntegrityError:
            artifact = Artifact.objects.get(sha256=artifact.sha256, pulp_domain=get_domain())
            artifact.touch()
            log.info(f"Artifact for {file.name} already existed in database")
        data["content"] = (artifact, file.name)
        return data


class PackageUploadTaskSerializer(serializers.Serializer):
    """
    A Serializer for responding to a package upload task.
    """

    session = serializers.CharField(allow_null=True)
    task = serializers.CharField()
    task_start_time = serializers.DateTimeField(allow_null=True)
