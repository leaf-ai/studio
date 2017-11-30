"""Utilities to track and record file system."""

import os
import uuid
import shutil
import json
import re
import six

STUDIOML_EXPERIMENT = 'STUDIOML_EXPERIMENT'
STUDIOML_HOME = 'STUDIOML_HOME'
STUDIOML_ARTIFACT_MAPPING = 'STUDIOML_ARTIFACT_MAPPING'
STUDIOML_USER = 'STUDIOML_USER'


def get_experiment_key():
    if STUDIOML_EXPERIMENT not in os.environ.keys():
        key = str(uuid.uuid4())
        setup_experiment(os.environ, key)
    return os.environ[STUDIOML_EXPERIMENT]


def get_studio_home():
    if STUDIOML_HOME in os.environ.keys():
        return os.environ[STUDIOML_HOME]
    else:
        return os.path.join(os.path.expanduser('~'), '.studioml')


def setup_experiment(env, experiment, clean=True, userid=None):
    if not isinstance(experiment, str):
        key = experiment.key
        artifacts = experiment.artifacts
    else:
        key = experiment
        artifacts = {}

    env[STUDIOML_EXPERIMENT] = key
    _setup_model_directory(key, clean, userid=userid)

    artifact_mapping_path = _get_artifact_mapping_path(key)
    env[STUDIOML_ARTIFACT_MAPPING] = artifact_mapping_path

    if userid:
        env[STUDIOML_USER] = userid

    amapping = {}
    for tag, art in six.iteritems(artifacts):
        if art.get('local') is not None:
            amapping[tag] = art['local']

        with open(artifact_mapping_path, 'w') as f:
            json.dump(amapping, f)


def get_artifact(tag):
    try:
        mapping_path = os.environ.get(STUDIOML_ARTIFACT_MAPPING)
        if mapping_path:
            with open(mapping_path, 'r') as f:
                a_mapping = json.load(f)
            return a_mapping[tag]
        else:
            return os.path.join(os.getcwd(), '..', tag)
    except BaseException:
        return None


def get_artifacts():
    try:
        mapping_path = os.environ.get(STUDIOML_ARTIFACT_MAPPING)
        if mapping_path:
            with open(mapping_path, 'r') as f:
                return json.load(f)
        else:
            artifacts = os.listdir(os.path.join(os.getcwd(), '..'))
            return {art: os.path.join(os.getcwd(), '..', art)
                    for art in artifacts}
    except BaseException:
        return {}


def get_model_directory(experiment_name=None, userid=None):
    return get_artifact_cache('modeldir', experiment_name, userid=userid)


def get_artifact_cache(tag, experiment_name=None, userid=None):
    assert tag is not None

    '''
    if tag.startswith('experiments/'):
        experiment_name = re.sub(
            '\Aexperiments/',
            '',
            re.sub(
                '/[^/]*\Z',
                '',
                tag))
    '''

    tag = re.sub('\.tar\.?[^\.]*\Z', '', tag)
    if '/' in tag:
        return os.path.join(
            get_studio_home(),
            'experiments',
            tag
        )
    else:
        experiment_name = experiment_name if experiment_name else \
            get_experiment_key()

        if not userid:
            userid = os.environ.get(STUDIOML_USER, 'guest')

        return os.path.join(
            get_studio_home(),
            'experiments',
            'users',
            userid,
            experiment_name + ".data",
            tag
        )


def get_blob_cache(blobkey):
    blobcache_dir = os.path.join(get_studio_home(), 'blobcache')
    if not os.path.exists(blobcache_dir):
        os.makedirs(blobcache_dir)

    blobkey = re.sub('\.tar\.?[^\.]*\Z', '', blobkey)
    if blobkey.startswith('blobstore/'):
        blobkey = re.sub('.*/', '', blobkey)

    return os.path.join(
        get_studio_home(),
        'blobcache',
        blobkey
    )


def _get_artifact_mapping_path(experiment_name=None):
    experiment_name = experiment_name if experiment_name else \
        os.environ[STUDIOML_EXPERIMENT]

    basepath = os.path.join(
        get_studio_home(),
        'artifact_mappings',
        experiment_name
    )
    if not os.path.exists(basepath):
        os.makedirs(basepath)

    return os.path.join(basepath, 'artifacts.json')


def _setup_model_directory(experiment_name, clean=False, userid=None):
    path = get_model_directory(experiment_name, userid=userid)
    if clean and os.path.exists(path):
        shutil.rmtree(path)

    if not os.path.exists(path):
        os.makedirs(path)


def get_queue_directory():
    queue_dir = os.path.join(
        get_studio_home(),
        'queue')
    if not os.path.exists(queue_dir):
        os.makedirs(queue_dir)

    return queue_dir


def get_tensorboard_dir(experiment_name=None):
    return get_artifact_cache('tb', experiment_name)
