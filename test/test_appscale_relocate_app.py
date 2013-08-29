#!/usr/bin/env python
# Programmer: Chris Bunch (chris@appscale.com)


# General-purpose Python library imports
import json
import os
import sys
import time
import unittest


# Third party libraries
from flexmock import flexmock
import SOAPpy


# AppScale import, the library that we're testing here
lib = os.path.dirname(__file__) + os.sep + ".." + os.sep + "lib"
sys.path.append(lib)
from appscale_logger import AppScaleLogger
from appscale_tools import AppScaleTools
from custom_exceptions import AppScaleException
from custom_exceptions import BadConfigurationException
from local_state import LocalState
from parse_args import ParseArgs


class TestAppScaleRelocateApp(unittest.TestCase):


  def setUp(self):
    self.keyname = "boobazblargfoo"
    self.function = "appscale-relocate-app"
    self.appid = 'my-crazy-app'

    # mock out any writing to stdout
    flexmock(AppScaleLogger)
    AppScaleLogger.should_receive('log').and_return()
    AppScaleLogger.should_receive('success').and_return()
    AppScaleLogger.should_receive('warn').and_return()

    # mock out all sleeping
    flexmock(time)
    time.should_receive('sleep').and_return()

    # mock out reading the locations.json file, and slip in our own json
    flexmock(os.path)
    os.path.should_call('exists')  # set the fall-through
    os.path.should_receive('exists').with_args(
      LocalState.get_locations_json_location(self.keyname)).and_return(True)

    fake_nodes_json = flexmock(name="fake_nodes_json")
    fake_nodes_json.should_receive('read').and_return(json.dumps([{
      "public_ip" : "public1",
      "private_ip" : "private1",
      "jobs" : ["shadow", "login"]
    }]))
    fake_nodes_json.should_receive('write').and_return()
    builtins = flexmock(sys.modules['__builtin__'])
    builtins.should_receive('open').with_args(
      LocalState.get_locations_json_location(self.keyname), 'r') \
      .and_return(fake_nodes_json)

    # put in a mock for reading the secret file
    builtins.should_call('open')  # set the fall-through

    secret_key_location = LocalState.get_secret_key_location(self.keyname)
    fake_secret = flexmock(name="fake_secret")
    fake_secret.should_receive('read').and_return('the secret')
    builtins.should_receive('open').with_args(secret_key_location, 'r') \
      .and_return(fake_secret)


  def add_appcontroller_mocks(self, app_running):
    fake_appcontroller = flexmock(name='fake_appcontroller')

    if app_running:
      fake_appcontroller.should_receive('get_app_info_map').with_args(
        'the secret').and_return(json.dumps({}))
    else:
      fake_appcontroller.should_receive('get_app_info_map').with_args(
        'the secret').and_return(json.dumps({}))

    flexmock(SOAPpy)
    SOAPpy.should_receive('SOAPProxy').with_args('https://1.2.3.4:17443') \
      .and_return(fake_appcontroller)


  def test_fails_if_destination_port_invalid(self):
    # If the user wants to relocate their app to port X, X should be a port
    # number that apps can actually be served on (e.g., between 1 and 65535).
    argv = [
      '--appname', self.appid,
      '--port', '100000'
    ]
    self.assertRaises(BadConfigurationException, ParseArgs, argv, self.function)


  def test_fails_if_app_isnt_running(self):
    # If the user wants to relocate their app to port X, but their app isn't
    # even running, this should fail.

    # Assume that the AppController is running but our app isn't.
    self.add_appcontroller_mocks(app_running=False)

    argv = [
      '--keyname', self.keyname,
      '--appname', self.appid,
      '--port', '80'
    ]
    options = ParseArgs(argv, self.function).args
    self.assertRaises(AppScaleException, AppScaleTools.relocate_app, options)


  def test_fails_if_destination_port_in_use(self):
    # If the user wants to relocate their app to port X, but something else
    # is running on port X, this should fail.
    pass


  def test_all_ok(self):
    # If the user wants to relocate their app to port X, and nothing else
    # runs on that port, this should succeed.
    pass
