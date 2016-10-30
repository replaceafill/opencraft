# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Instance app - Activity report management command
"""

# Imports #####################################################################

from configparser import ConfigParser
import csv
from datetime import datetime
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from instance import ansible
from instance.models.openedx_instance import OpenEdXInstance
from instance.utils import poll_streams


# Classes #####################################################################

class Command(BaseCommand):
    """
    Activity_csv management command class
    """
    help = (
        'Generates a CSV containing basic activity information about active app servers'
        ' (numbers for distinct hits, users, and courses).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--out',
            default=None,
            help='Path to the output file of the new CSV. Leave blank to use stdout.'
        )

    def handle(self, *args, **options):  # pylint: disable=too-many-locals
        # Determine the stream to be used for outputting the CSV.
        if options['out'] is None:
            out = self.stdout
        else:
            try:
                out = open(options['out'], 'w')
            except PermissionError:
                self.stderr.write(self.style.ERROR(  # pylint: disable=no-member
                    'Permission denied while attempting to write file: {outfile}'.format(outfile=options['out'])
                ))
                sys.exit(1)

        # Produce a mapping of public IPs (of active app servers) to parent instances.
        active_appservers = {
            instance.active_appserver.server.public_ip: instance for instance in OpenEdXInstance.objects.all()
            if not (instance.active_appserver is None or instance.active_appserver.server.public_ip is None)
        }

        if not active_appservers:
            self.stderr.write(
                self.style.SUCCESS('There are no active app servers! Nothing to do.')  # pylint: disable=no-member
            )
            sys.exit(0)

        self.stderr.write(self.style.SUCCESS('Running playbook...'))  # pylint: disable=no-member

        with ansible.create_temp_dir() as playbook_output_dir:
            inventory = '[apps]\n{servers}'.format(servers='\n'.join(active_appservers.keys()))
            playbook_path = os.path.join(settings.SITE_ROOT, 'playbooks/collect_activity/collect_activity.yml')

            # Launch the collect_activity playbook, which places a set of files into the `playbook_output_dir`
            # on this host.
            with ansible.run_playbook(
                requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
                inventory_str=inventory,
                vars_str=(
                    'local_output_dir: {output_dir}\n'
                    'remote_output_filename: /tmp/activity_report'
                ).format(output_dir=playbook_output_dir),
                playbook_path=os.path.dirname(playbook_path),
                playbook_name=os.path.basename(playbook_path),
                username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
            ) as process:
                log_line_generator = poll_streams(
                    process.stdout,
                    process.stderr,
                )
                for _, line in log_line_generator:
                    line = line.decode('utf-8').rstrip()
                    # Forward all lines from both channels to stderr. stdout is optionally used for the CSV output.
                    self.stderr.write(self.style.SUCCESS(line))  # pylint: disable=no-member
                process.wait()

            csv_writer = csv.writer(out)
            csv_writer.writerow(
                ['Appserver IP', 'Owner Emails', 'Unique Hits', 'Total Users', 'Total Courses', 'Age (Days)']
            )

            filenames = [os.path.join(playbook_output_dir, f) for f in os.listdir(playbook_output_dir)]
            data = ConfigParser()
            data.read(filenames)

            for public_ip in data.sections():
                section = data[public_ip]
                instance = active_appservers[public_ip]

                instance_age = datetime.now(instance.created.tzinfo) - instance.created

                emails = [user.email for user in instance.lms_users.all()]
                csv_writer.writerow([
                    public_ip, emails,
                    section['hits'], section['users'], section['courses'],
                    instance_age.days
                ])

            self.stderr.write(self.style.SUCCESS('Done generating CSV output.'))  # pylint: disable=no-member