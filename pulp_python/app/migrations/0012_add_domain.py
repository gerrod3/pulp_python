# Generated by Django 4.2.10 on 2024-05-30 17:53

from django.db import migrations, models
import django.db.models.deletion
import pulpcore.app.util


class Migration(migrations.Migration):

    dependencies = [
        ("python", "0011_alter_pythondistribution_distribution_ptr_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="pythonpackagecontent",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="pythonpackagecontent",
            name="_pulp_domain",
            field=models.ForeignKey(
                default=pulpcore.app.util.get_domain_pk,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.domain",
            ),
        ),
        migrations.AlterField(
            model_name="pythonpackagecontent",
            name="sha256",
            field=models.CharField(db_index=True, max_length=64),
        ),
        migrations.AlterUniqueTogether(
            name="pythonpackagecontent",
            unique_together={("sha256", "_pulp_domain")},
        ),
    ]
