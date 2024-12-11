# Generated by Django 4.2.16 on 2024-12-11 16:42

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0091_systemid'),
    ]

    operations = [
        migrations.CreateModel(
            name='PythonPublication',
            fields=[
                ('publication_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='python_pythonpublication', serialize=False, to='core.publication')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.publication',),
        ),
        migrations.CreateModel(
            name='PythonRemote',
            fields=[
                ('remote_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='python_pythonremote', serialize=False, to='core.remote')),
                ('prereleases', models.BooleanField(default=False)),
                ('includes', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('excludes', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.remote',),
        ),
        migrations.CreateModel(
            name='PythonRepository',
            fields=[
                ('repository_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='python_pythonrepository', serialize=False, to='core.repository')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.repository',),
        ),
        migrations.CreateModel(
            name='PythonPackageContent',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='python_pythonpackagecontent', serialize=False, to='core.content')),
                ('filename', models.TextField(db_index=True, unique=True)),
                ('packagetype', models.TextField(choices=[('bdist_dmg', 'bdist_dmg'), ('bdist_dumb', 'bdist_dumb'), ('bdist_egg', 'bdist_egg'), ('bdist_msi', 'bdist_msi'), ('bdist_rpm', 'bdist_rpm'), ('bdist_wheel', 'bdist_wheel'), ('bdist_wininst', 'bdist_wininst'), ('sdist', 'sdist')])),
                ('name', models.TextField()),
                ('version', models.TextField()),
                ('metadata_version', models.TextField()),
                ('summary', models.TextField()),
                ('description', models.TextField()),
                ('keywords', models.TextField()),
                ('home_page', models.TextField()),
                ('download_url', models.TextField()),
                ('author', models.TextField()),
                ('author_email', models.TextField()),
                ('maintainer', models.TextField()),
                ('maintainer_email', models.TextField()),
                ('license', models.TextField()),
                ('requires_python', models.TextField()),
                ('project_url', models.TextField()),
                ('platform', models.TextField()),
                ('supported_platform', models.TextField()),
                ('requires_dist', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('provides_dist', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('obsoletes_dist', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('requires_external', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('classifiers', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
                'unique_together': {('filename',)},
            },
            bases=('core.content',),
        ),
        migrations.CreateModel(
            name='PythonDistribution',
            fields=[
                ('basedistribution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='python_pythondistribution', serialize=False, to='core.basedistribution')),
                ('publication', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='python_pythondistribution', to='core.publication')),
            ],
            options={
                'default_related_name': '%(app_label)s_%(model_name)s',
            },
            bases=('core.basedistribution',),
        ),
    ]
