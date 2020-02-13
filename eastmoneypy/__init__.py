# -*- coding: utf-8 -*-
import json
import logging
import os
from logging.handlers import RotatingFileHandler

from pathlib import Path

EASTMONEY_HOME = os.environ.get('EASTMONEY_HOME')
if not EASTMONEY_HOME:
    EASTMONEY_HOME = os.path.abspath(os.path.join(Path.home(), 'eastmoneypy-home'))


def init_log(file_name='eastmoneypy.log', log_dir=None, simple_formatter=True):
    if not log_dir:
        log_dir = my_env['log_path']

    root_logger = logging.getLogger()

    # reset the handlers
    root_logger.handlers = []

    root_logger.setLevel(logging.INFO)

    file_name = os.path.join(log_dir, file_name)

    fh = RotatingFileHandler(file_name, maxBytes=524288000, backupCount=10)

    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    if simple_formatter:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(name)s:%(filename)s:%(lineno)s  %(funcName)s  %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)


my_env = {}


def init_env(EASTMONEY_HOME: str) -> None:
    """

    :param EASTMONEY_HOME: home path for this lib
    """
    if not os.path.exists(EASTMONEY_HOME):
        os.makedirs(EASTMONEY_HOME)

    my_env['EASTMONEY_HOME'] = EASTMONEY_HOME

    # path for storing logs
    my_env['log_path'] = os.path.join(EASTMONEY_HOME, 'logs')
    if not os.path.exists(my_env['log_path']):
        os.makedirs(my_env['log_path'])

    # create default config.json if not exist
    config_path = os.path.join(EASTMONEY_HOME, 'config.json')
    if not os.path.exists(config_path):
        from shutil import copyfile
        copyfile(os.path.abspath(os.path.join(os.path.dirname(__file__), 'config.json')), config_path)

    with open(config_path) as f:
        config_json = json.load(f)
        for k in config_json:
            my_env[k] = config_json[k]

    init_log()

    import pprint
    pprint.pprint(my_env)


init_env(EASTMONEY_HOME=EASTMONEY_HOME)

from .api import *
