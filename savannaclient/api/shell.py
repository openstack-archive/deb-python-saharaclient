# Copyright 2013 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import datetime
import inspect
import json
from savannaclient.nova import utils
import sys


def _print_list_field(field):
    return lambda obj: ', '.join(getattr(obj, field))


def _print_node_group_field(cluster):
    return ', '.join(map(lambda x: ': '.join(x),
                         [(node_group['name'],
                           str(node_group['count']))
                          for node_group in cluster.node_groups]))


def _show_node_group_template(template):
    template._info['node_processes'] = (
        ', '.join(template._info['node_processes'])
    )
    utils.print_dict(template._info)


def _show_cluster_template(template):
    template._info['node_groups'] = _print_node_group_field(template)
    utils.print_dict(template._info)


def _show_cluster(cluster):
    # TODO(mattf): Make this pretty, e.g format node_groups and info urls
    # Forcing wrap=47 allows for clean display on a terminal of width 80
    utils.print_dict(cluster._info, wrap=47)


def _show_job_binary_data(data):
    columns = ('id', 'name')
    utils.print_list(data, columns)


def _show_data_source(source):
    # TODO(mattf): why are we passing credentials around like this?
    del source._info['credentials']
    utils.print_dict(source._info)


def _show_job_binary(binary):
    # TODO(mattf): why are we passing credentials around like this?
    del binary._info['extra']
    utils.print_dict(binary._info)


#
# Plugins
# ~~~~~~~
# plugin-list
#
# plugin-show --name <plugin> [--version <version>]
#

def do_plugin_list(cs, args):
    """Print a list of available plugins."""
    plugins = cs.plugins.list()
    columns = ('name', 'versions', 'title')
    utils.print_list(plugins, columns,
                     {'versions': _print_list_field('versions')})


@utils.arg('--name',
           metavar='<plugin>',
           required=True,
           help='Name of plugin')
# TODO(mattf) - savannaclient does not support query w/ version
#@utils.arg('--version',
#           metavar='<version>',
#           help='Optional version')
def do_plugin_show(cs, args):
    """Show details of a plugin."""
    plugin = cs.plugins.get(args.name)
    plugin._info['versions'] = ', '.join(plugin._info['versions'])
    utils.print_dict(plugin._info)


#
# Image Registry
# ~~~~~~~~~~~~~~
# image-list [--tag <tag>]*
#
# image-show --name <image>|--id <image_id>
#
# image-register --name <image>|--id <image_id>
#                [--username <name>] [--description <desc>]
#
# image-unregister --name <image>|--id <image_id>
#
# image-add-tag --name <image>|--id <image_id> --tag <tag>+
#
# image-remove-tag --name <image>|--id <image_id> --tag <tag>+
#

# TODO(mattf): [--tag <tag>]*
def do_image_list(cs, args):
    """Print a list of available plugins."""
    images = cs.images.list()
    columns = ('name', 'id', 'username', 'tags', 'description')
    utils.print_list(images, columns, {'tags': _print_list_field('tags')})


@utils.arg('--id',
           metavar='<image_id>',
           required=True,
           help='Id of image')
# TODO(mattf): --name <image>
def do_image_show(cs, args):
    """Show details of an image."""
    image = cs.images.get(args.id)
    del image._info['metadata']
    image._info['tags'] = ', '.join(image._info['tags'])
    utils.print_dict(image._info)


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<image>',
#           required=True,
#           help='Name from Image index (e.g. glance index)')
@utils.arg('--id',
           metavar='<image_id>',
           required=True,
           help='Id from Image index (e.g. glance index)')
@utils.arg('--username',
           default='root',
           metavar='<name>',
           help='Username of privileged user in the image')
@utils.arg('--description',
           default='',
           metavar='<desc>',
           help='Description of image')
def do_image_register(cs, args):
    """Register an image from the Image index."""
    # TODO(mattf): image register should not be through update
    cs.images.update_image(args.id, args.username, args.description)
    # TODO(mattf): No indication of result, expect image details


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<image>',
#           required=True,
#           help='Name from Image index (e.g. glance index)')
@utils.arg('--id',
           metavar='<image_id>',
           required=True,
           help='Image to unregister')
def do_image_unregister(cs, args):
    """Unregister an image."""
    cs.images.unregister_image(args.id)
    # TODO(mattf): No indication of result, expect result to display


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<image>',
#           required=True,
#           help='Name from Image index (e.g. glance index)')
@utils.arg('--id',
           metavar='<image_id>',
           required=True,
           help='Image to tag')
# TODO(mattf): Change --tag to --tag+
@utils.arg('--tag',
           metavar='<tag>',
           required=True,
           help='Tag to add')
def do_image_add_tag(cs, args):
    """Add a tag to an image."""
    # TODO(mattf): Need proper add_tag API call
    cs.images.update_tags(args.id, cs.images.get(args.id).tags + [args.tag, ])
    # TODO(mattf): No indication of result, expect image details


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<image>',
#           required=True,
#           help='Name from Image index (e.g. glance index)')
@utils.arg('--id',
           metavar='<image_id>',
           required=True,
           help='Image to tag')
# TODO(mattf): Change --tag to --tag+
@utils.arg('--tag',
           metavar='<tag>',
           required=True,
           help='Tag to add')
def do_image_remove_tag(cs, args):
    """Remove a tag from an image."""
    # TODO(mattf): Need proper remove_tag API call
    cs.images.update_tags(args.id,
                          filter(lambda x: x != args.tag,
                                 cs.images.get(args.id).tags))
    # TODO(mattf): No indication of result, expect image details


#
# Clusters
# ~~~~~~~~
# cluster-list
#
# cluster-show --name <cluster>|--id <cluster_id> [--json]
#
# cluster-create [--json <file>]
#
# TODO(mattf): cluster-scale
#
# cluster-delete --name <cluster>|--id <cluster_id>
#

def do_cluster_list(cs, args):
    """Print a list of available clusters."""
    clusters = cs.clusters.list()
    for cluster in clusters:
        cluster.node_count = sum(map(lambda g: g['count'],
                                     cluster.node_groups))
    columns = ('name', 'id', 'status', 'node_count')
    utils.print_list(clusters, columns)


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<cluster>',
#           required=True,
#           help='Cluster name')
@utils.arg('--id',
           metavar='<cluster_id>',
           required=True,
           help='Id of cluster to show')
@utils.arg('--json',
           action='store_true',
           default=False,
           help='Print JSON representation of cluster')
def do_cluster_show(cs, args):
    """Show details of a cluster."""
    cluster = cs.clusters.get(args.id)
    if args.json:
        print(json.dumps(cluster._info))
    else:
        _show_cluster(cluster)


@utils.arg('--json',
           default=sys.stdin,
           type=argparse.FileType('r'),
           help='JSON representation of cluster')
def do_cluster_create(cs, args):
    """Create a cluster."""
     # TODO(mattf): improve template validation, e.g. template w/o name key
    template = json.loads(args.json.read())
    valid_args = inspect.getargspec(cs.clusters.create).args
    for name in template.keys():
        if name not in valid_args:
            # TODO(mattf): make this verbose - bug/1271147
            del template[name]
    _show_cluster(cs.clusters.create(**template))


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<cluster>',
#           required=True,
#           help='Cluster name')
@utils.arg('--id',
           metavar='<cluster_id>',
           required=True,
           help='Id of cluster to delete')
def do_cluster_delete(cs, args):
    """Delete a cluster."""
    cs.clusters.delete(args.id)
    # TODO(mattf): No indication of result


#
# Node Group Templates
# ~~~~~~~~~~~~~~~~~~~~
# node-group-template-list
#
# node-group-template-show --name <template>|--id <template_id> [--json]
#
# node-group-template-create [--json <file>]
#
# node-group-template-delete --name <template>|--id <template_id>
#

def do_node_group_template_list(cs, args):
    """Print a list of available node group templates."""
    templates = cs.node_group_templates.list()
    columns = ('name', 'id', 'plugin_name', 'node_processes', 'description')
    utils.print_list(templates, columns,
                     {'node_processes': _print_list_field('node_processes')})


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<template>',
#           required=True,
#           help='Template name')
@utils.arg('--id',
           metavar='<template_id>',
           required=True,
           help='Id of node group template to show')
@utils.arg('--json',
           action='store_true',
           default=False,
           help='Print JSON representation of node group template')
def do_node_group_template_show(cs, args):
    """Show details of a node group template."""
    template = cs.node_group_templates.get(args.id)
    if args.json:
        print(json.dumps(template._info))
    else:
        _show_node_group_template(template)


@utils.arg('--json',
           default=sys.stdin,
           type=argparse.FileType('r'),
           help='JSON representation of node group template')
def do_node_group_template_create(cs, args):
    """Create a node group template."""
     # TODO(mattf): improve template validation, e.g. template w/o name key
    template = json.loads(args.json.read())
    valid_args = inspect.getargspec(cs.node_group_templates.create).args
    for name in template.keys():
        if name not in valid_args:
            # TODO(mattf): make this verbose - bug/1271147
            del template[name]
    _show_node_group_template(cs.node_group_templates.create(**template))


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<template>',
#           required=True,
#           help='Template name')
@utils.arg('--id',
           metavar='<template_id>',
           required=True,
           help='Id of node group template to delete')
def do_node_group_template_delete(cs, args):
    """Delete a node group template."""
    cs.node_group_templates.delete(args.id)
    # TODO(mattf): No indication of result


#
# Cluster Templates
# ~~~~~~~~~~~~~~~~~
# cluster-template-list
#
# cluster-template-show --name <template>|--id <template_id> [--json]
#
# cluster-template-create [--json <file>]
#
# cluster-template-delete --name <template>|--id <template_id>
#

def do_cluster_template_list(cs, args):
    """Print a list of available cluster templates."""
    templates = cs.cluster_templates.list()
    columns = ('name', 'id', 'plugin_name', 'node_groups', 'description')
    utils.print_list(templates, columns,
                     {'node_groups': _print_node_group_field})


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<template>',
#           required=True,
#           help='Template name')
@utils.arg('--id',
           metavar='<template_id>',
           required=True,
           help='Id of cluster template to show')
@utils.arg('--json',
           action='store_true',
           default=False,
           help='Print JSON representation of cluster template')
def do_cluster_template_show(cs, args):
    """Show details of a cluster template."""
    template = cs.cluster_templates.get(args.id)
    if args.json:
        print(json.dumps(template._info))
    else:
        _show_cluster_template(template)


@utils.arg('--json',
           default=sys.stdin,
           type=argparse.FileType('r'),
           help='JSON representation of cluster template')
def do_cluster_template_create(cs, args):
    """Create a cluster template."""
     # TODO(mattf): improve template validation, e.g. template w/o name key
    template = json.loads(args.json.read())
    valid_args = inspect.getargspec(cs.cluster_templates.create).args
    for name in template.keys():
        if name not in valid_args:
            # TODO(mattf): make this verbose - bug/1271147
            del template[name]
    _show_cluster_template(cs.cluster_templates.create(**template))


# TODO(mattf): Add --name
#@utils.arg('--name',
#           metavar='<template>',
#           required=True,
#           help='Template name')
@utils.arg('--id',
           metavar='<template_id>',
           required=True,
           help='Id of cluster template to delete')
def do_cluster_template_delete(cs, args):
    """Delete a cluster template."""
    cs.cluster_templates.delete(args.id)
    # TODO(mattf): No indication of result


#
# Data Sources
# ~~~~~~~~~~~~
# data-source-list
#
# data-source-show --name <name>|--id <id>
#
# data-source-create --name <name> --type <type>
#                    --url <url>
#                    [--user <user> --password <password>]
#                    [--description <desc>]
# NB: user & password if type is swift
#
# data-source-delete --name <name>|--id <id>
#

def do_data_source_list(cs, args):
    """Print a list of available data sources."""
    sources = cs.data_sources.list()
    columns = ('name', 'id', 'type', 'description')
    utils.print_list(sources, columns)


@utils.arg('--id',
           required=True,
           help='Id of data source')
# TODO(mattf): --name <name>
def do_data_source_show(cs, args):
    """Show details of a data source."""
    _show_data_source(cs.data_sources.get(args.id))


@utils.arg('--name',
           required=True,
           help='Name of the data source')
@utils.arg('--type',
           required=True,
           help='Type of the data source')
@utils.arg('--url',
           required=True,
           help='URL for data source')
@utils.arg('--description',
           default='',
           help='Description of the data source')
@utils.arg('--user',
           default=None,
           help='Username for accessing the data source url')
@utils.arg('--password',
           default=None,
           help='Password for accessing the data source url')
def do_data_source_create(cs, args):
    """Create a data source that provides job input or receives job output."""
    _show_data_source(cs.data_sources.create(args.name, args.description,
                                             args.type, args.url,
                                             args.user, args.password))


@utils.arg('--id',
           required=True,
           help='Id of data source to delete')
# TODO(mattf): Add --name
def do_data_source_delete(cs, args):
    """Delete a data source."""
    cs.data_sources.delete(args.id)
    # TODO(mattf): No indication of result


#
# Job Binary Internals
# ~~~~~~~~~~~~~~~~~~~~
# job-binary-data-list
#
# job-binary-data-create [--file <file>]
#
# job-binary-data-delete --id <id>
#

def do_job_binary_data_list(cs, args):
    """Print a list of internally stored job binary data."""
    _show_job_binary_data(cs.job_binary_internals.list())


@utils.arg('--file',
           default=sys.stdin,
           type=argparse.FileType('r'),
           help='Data to store')
def do_job_binary_data_create(cs, args):
    """Store data in Savanna's internal DB.
    Use 'swift upload' instead of this command.
    Use this command only if Swift is not available.
    """
    # Should be %F-%T except for type validation errors
    _show_job_binary_data((cs.job_binary_internals.create(
        datetime.datetime.now().strftime('d%Y%m%d%H%M%S'),
        args.file.read()),)
    )


@utils.arg('--id',
           required=True,
           help='Id of internally stored job binary data')
def do_job_binary_data_delete(cs, args):
    """Delete an internally stored job binary data."""
    cs.job_binary_internals.delete(args.id)
    # TODO(mattf): No indication of result
    # TODO(mattf): Appears no DB constraints for removing data used by job


#
# Job Binaries
# ~~~~~~~~~~~~
# job-binary-list
#
# job-binary-show --name <name>|--id <id>
#
# job-binary-create --name <name> --url <url>
#                   [--user <user> --password <password>]
#                   [--description <desc>]
#
# job-binary-delete --name <name>|--id <id>
#

def do_job_binary_list(cs, args):
    """Print a list of job binaries."""
    binaries = cs.job_binaries.list()
    columns = ('id', 'name', 'description')
    utils.print_list(binaries, columns)


@utils.arg('--id',
           required=True,
           help='Id of job binary')
# TODO(mattf): --name <name>
def do_job_binary_show(cs, args):
    """Show details of a job binary."""
    _show_job_binary(cs.job_binaries.get(args.id))


@utils.arg('--name',
           required=True,
           help='Name of the job binary')
@utils.arg('--url',
           required=True,
           help='URL for the job binary')
@utils.arg('--description',
           default='',
           help='Description of the job binary')
@utils.arg('--user',
           default=None,
           help='Username for accessing the job binary url')
@utils.arg('--password',
           default=None,
           help='Password for accessing the job binary url')
def do_job_binary_create(cs, args):
    """Record a job binary."""
    # TODO(mattf): make credentials consistent w/ data source
    extra = {}
    if args.user:
        extra['user'] = args.user
    if args.password:
        extra['password'] = args.password
    _show_job_binary(cs.job_binaries.create(args.name, args.url,
                                            args.description, extra))


@utils.arg('--id',
           required=True,
           help='Id of a job binary')
def do_job_binary_delete(cs, args):
    """Delete a job binary."""
    cs.job_binaries.delete(args.id)
    # TODO(mattf): No indication of result


#
# Jobs
# ~~~~
# job-template-list
#
# job-template-show --name <name>|--id <id>
#
# TODO(mattf): job-template-create --name <name>
#                                  --type <Pig|Hive|Jar>
#                                  --mains <array of string>
#                                  --libs <array of string>
#
# job-template-delete --name <name>|--id <id>
#

def do_job_template_list(cs, args):
    """Print a list of job templates."""
    templates = cs.jobs.list()
    columns = ('id', 'name', 'description')
    utils.print_list(templates, columns)


@utils.arg('--id',
           required=True,
           help='Id of a job template')
# TODO(mattf): --name <name>
def do_job_template_show(cs, args):
    """Show details of a job template."""
    template = cs.jobs.get(args.id)
    # TODO(mattf): Make "mains" property pretty
    utils.print_dict(template._info)


@utils.arg('--id',
           required=True,
           help='Id of a job template')
def do_job_template_delete(cs, args):
    """Delete a job template."""
    cs.jobs.delete(args.id)
    # TODO(mattf): No indication of result


#
# Job Executions
# ~~~~~~~~~~~~~~
# job-list
#
# job-show --name <name>|--id <id>
#
# TODO(mattf): job-create --name <name> --job-template <id>
#                                       --input-data <id>
#                                       --output-data <id>
#                                       --cluster-template <id>
# NB: Optional job_configs
# NB: POST /jobs/{job_template_id}/execute
#
# job-delete --name <name>|--id <id>
#

def do_job_list(cs, args):
    """Print a list of jobs."""
    jobs = cs.job_executions.list()
    for job in jobs:
        # why is status in info.status?
        job.status = job.info['status']
    # TODO(mattf): why can cluster_id be None?
    columns = ('id', 'cluster_id', 'status')
    utils.print_list(jobs, columns)


@utils.arg('--id',
           required=True,
           help='Id of a job')
# TODO(mattf): --name <name>, which is cluster name
def do_job_show(cs, args):
    """Show details of a job."""
    job = cs.job_executions.get(args.id)
    job._info['status'] = job._info['info']['status']
    del job._info['info']
    utils.print_dict(job._info)


@utils.arg('--id',
           required=True,
           help='Id of a job')
# TODO(mattf): --name <name>, which is cluster name
def do_job_delete(cs, args):
    """Delete a job."""
    cs.job_executions.delete(args.id)
    # TODO(mattf): No indication of result
