import time

from datetime import datetime, timezone
from django.db import transaction
from django.contrib.sessions.models import Session
from pulpcore.plugin.models import Artifact, CreatedResource, ContentArtifact

from pulp_python.app.models import PythonPackageContent, PythonRepository
from pulp_python.app.utils import parse_project_metadata, get_project_metadata_from_artifact


def upload(session_pk, repository_pk=None):
    """
    Uploads a Python Package to Pulp

    Args:
        session_pk: the session that has the artifacts to upload
        repository_pk: optional repository to add Content to
    """
    s_query = Session.objects.select_for_update().filter(pk=session_pk)
    while True:
        with transaction.atomic():
            session_data = s_query.first().get_decoded()
            now = datetime.now(tz=timezone.utc)
            try:
                start_time = datetime.fromisoformat(session_data['start'])
            except AttributeError:
                # TODO: Remove this once Python 3.7+ project
                from dateutil.parser import parse
                start_time = parse(session_data['start'])
            if now >= start_time:
                content_to_add = PythonPackageContent.objects.none()
                for artifact_sha256, filename in session_data['artifacts']:
                    pre_check = PythonPackageContent.objects.filter(sha256=artifact_sha256)
                    content_to_add |= pre_check or create_content(artifact_sha256, filename)

                if repository_pk:
                    repository = PythonRepository.objects.get(pk=repository_pk)
                    with repository.new_version() as new_version:
                        new_version.add_content(content_to_add)
                return
            else:
                sleep_time = start_time - now
        time.sleep(sleep_time.seconds)


def create_content(artifact_sha256, filename):
    """
    Creates PythonPackageContent from artifact.

    Args:
        artifact_sha256: validated artifact
        filename: file name
    Returns:
        queryset of the new created content
    """
    artifact = Artifact.objects.get(sha256=artifact_sha256)
    metadata = get_project_metadata_from_artifact(filename, artifact)

    data = parse_project_metadata(vars(metadata))
    data['packagetype'] = metadata.packagetype
    data['version'] = metadata.version
    data['filename'] = filename
    data['sha256'] = artifact.sha256

    @transaction.atomic()
    def create():
        content = PythonPackageContent.objects.create(**data)
        ContentArtifact.objects.create(
            artifact=artifact, content=content, relative_path=filename
        )
        return content

    new_content = create()
    resource = CreatedResource(content_object=new_content)
    resource.save()

    return PythonPackageContent.objects.filter(pk=new_content.pk)
