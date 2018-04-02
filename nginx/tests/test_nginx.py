# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os
# import mock
# import json
import pytest
import subprocess
import requests
import logging
import time
from datadog_checks.stubs import aggregator as _aggregator

from datadog_checks.nginx import Nginx
log = logging.getLogger('test_nginx')
FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
HERE = os.path.dirname(os.path.abspath(__file__))


def wait_for_nginx():
    env = os.environ
    docker_ps = [
        "docker", "ps", "-a"
    ]
    for _ in xrange(0, 100):
        res = None
        try:
            res = requests.get('http://localhost:44441/nginx_status')
            log.info("res: ".format(res))
            log.info("sc: {0} text: {1}".format(res.status_code, res.text))
            res.raise_for_status
            return
        except Exception as e:
            log.info("exception: {0} res: {1}".format(e, res))
            subprocess.check_call(docker_ps, env=env)
            time.sleep(2)


@pytest.fixture(scope="session")
def spin_up_nginx():
    env = os.environ
    env['NGINX_CONFIG'] = os.path.join(HERE, 'config', 'nginx.conf')
    print 'NGINX_CONFIG', env['NGINX_CONFIG']
    args = ["docker-compose",
            "-f", os.path.join(HERE, 'compose', 'nginx.yaml')
            ]
    subprocess.check_call(args + ["up", "-d"], env=env)

    wait_for_nginx()
    # for _ in xrange(0, 100):
    #    requests.get('http://localhost:44441')
    yield
    subprocess.check_call(args + ["down"], env=env)


@pytest.fixture
def aggregator():
    _aggregator.reset()
    return _aggregator


class TestNginx:
    CHECK_NAME = 'nginx'

    CONFIG_STUBS = [
        {'nginx_status_url': 'http://localhost:44441/nginx_status/'},
        {
            'nginx_status_url': 'http://localhost:44441/nginx_status/',
            'tags': ['first_one'],
        },
        {
            'nginx_status_url': 'http://dummyurl:44441/nginx_status/',
            'tags': ['dummy'],
        },
        {
            'nginx_status_url': 'http://localhost:44441/nginx_status/',
            'tags': ['second'],
        },
        {
            'nginx_status_url': 'https://localhost:44441/https_nginx_status/',
            'tags': ['ssl_enabled'],
            'ssl_validation': True,
        },
        {
            'nginx_status_url': 'https://localhost:44441/https_nginx_status/',
            'tags': ['ssl_disabled'],
            'ssl_validation': False,
        },
    ]

    AGENT_CONFIG = {
        'version': '0.1',
        'api_key': 'toto'
    }

    def test_nginx_one_connection(self, aggregator, spin_up_nginx):
        # Testing that connection will work with instance 0
        c = Nginx(self.CHECK_NAME, {}, {})
        for config in self.CONFIG_STUBS:
            c.check(config)
            tags = config["tags"]
            # Checking that only one metric is of type 'nginx.net.connections'
            aggregator.assert_metric("nginx.net.connections", tags=tags, count=1)
            aggregator.reset()
            # self.assertEquals(len([t for t in r if t[0] == "nginx.net.connections"]), 1, r)

#     def test_nginx_tags(self):
#         nginx = load_check('nginx', INSTANCES, AGENT_CONFIG)

#         # Testing that connection will work with instance 1
#         nginx.check(INSTANCES['instances'][1])

#         # Checking that 'tags' attribute of some result is equal to 'tags' attribute in config for instance 1
#         r = nginx.get_metrics()
#         self.assertEquals(r[0][3].get('tags'), ('first_one', ))

#         # Checking that each 'nginx.can_connect' service check's 'tags' attribute match expected host/port from config
#         service_checks = nginx.get_service_checks()
#         can_connect = [sc for sc in service_checks if sc['check'] == 'nginx.can_connect']
#         for i in range(len(can_connect)):
#             self.assertEquals(set(can_connect[i]['tags']), set(['host:localhost', 'port:8180']), service_checks)

#     def test_nginx_ssl_validation_enabled(self):
#         # Note: Throws an SSLError, because we're attempting to connect to an https endpoint with a self-signed
#         #       certificate. In addition, this throws an InsecurePlatformWarning. Both of these are expected;
#         #       versions of Python < 2.7.9 have restrictions in their ssl module limiting the configuration
#         #       urllib3 can apply. (https://urllib3.readthedocs.org/en/latest/security.html#insecurerequestwarning)
#         nginx = load_check('nginx', INSTANCES, AGENT_CONFIG)

#         # Testing that connection will FAIL with instance 4
#         self.assertRaises(requests.exceptions.SSLError, nginx.check, INSTANCES['instances'][4])

#     def test_nginx_ssl_validation_disabled(self):
#         nginx = load_check('nginx', INSTANCES, AGENT_CONFIG)

#         # Testing that connection will work with instance 5
#         nginx.check(INSTANCES['instances'][5])

#         # Checking that 'tags' attribute of some result is equal to 'tags' attribute in config for instance 5
#         r = nginx.get_metrics()
#         self.assertEquals(r[0][3].get('tags'), ('ssl_disabled', ))

#         # Checking that each 'nginx.can_connect' service check's 'tags' attribute match expected host/port from config
#         service_checks = nginx.get_service_checks()
#         can_connect = [sc for sc in service_checks if sc['check'] == 'nginx.can_connect']
#         for i in range(len(can_connect)):
#             self.assertEquals(set(can_connect[i]['tags']), set(['host:localhost', 'port:8180']), service_checks)

#     def test_nginx_plus(self):
#         test_data = Fixtures.read_file('nginx_plus_in.json', sdk_dir=FIXTURE_DIR)
#         expected = eval(Fixtures.read_file('nginx_plus_out.python', sdk_dir=FIXTURE_DIR))
#         nginx = load_check('nginx', INSTANCES, AGENT_CONFIG)
#         parsed = nginx.parse_json(test_data)
#         parsed.sort()

#         # Check that the parsed test data is the same as the expected output
#         self.assertEquals(parsed, expected)

# class dummy_http_response:
#     def __init__(self, json):
#         self._json = json

#     def json(self):
#         return json.loads(self._json)

# def api_call(*args, **kwargs):

#     json = ""
#     url = args[1]

#     if "nginx" in url:
#         json = Fixtures.read_file('plus_api_nginx.json', sdk_dir=FIXTURE_DIR)
#     elif "processes" in url:
#         json = Fixtures.read_file('plus_api_processes.json', sdk_dir=FIXTURE_DIR)
#     elif "connections" in url:
#         json = Fixtures.read_file('plus_api_connections.json', sdk_dir=FIXTURE_DIR)
#     elif "ssl" in url:
#         json = Fixtures.read_file('plus_api_ssl.json', sdk_dir=FIXTURE_DIR)
#     elif "slabs" in url:
#         json = Fixtures.read_file('plus_api_slabs.json', sdk_dir=FIXTURE_DIR)
#     elif "http/requests" in url:
#         json = Fixtures.read_file('plus_api_http_requests.json', sdk_dir=FIXTURE_DIR)
#     elif "http/server_zones" in url:
#         json = Fixtures.read_file('plus_api_http_server_zones.json', sdk_dir=FIXTURE_DIR)
#     elif "http/caches" in url:
#         json = Fixtures.read_file('plus_api_http_caches.json', sdk_dir=FIXTURE_DIR)
#     elif "http/upstreams" in url:
#         json = Fixtures.read_file('plus_api_http_upstreams.json', sdk_dir=FIXTURE_DIR)
#     elif "stream/upstreams" in url:
#         json = Fixtures.read_file('plus_api_stream_upstreams.json', sdk_dir=FIXTURE_DIR)
#     elif "stream/server_zones" in url:
#         json = Fixtures.read_file('plus_api_stream_server_zones.json', sdk_dir=FIXTURE_DIR)

#     return dummy_http_response(json)

# class TestNginxPlusAPI(AgentCheckTest):

#     CHECK_NAME = "nginx"

#     def test_plus_api(self):
#         config = {
#             "instances": [{
#                 "nginx_status_url": "http://dummy/api",
#                 "use_plus_api": True
#             }]
#         }
#         self.load_check(config, {})
#         with mock.patch('datadog_checks.nginx.Nginx._perform_request', side_effect=api_call):
#             self.run_check(config)
#             self.assertEquals(len(self.metrics), 956)

#     def test_nest_payload(self):
#         self.load_check({}, {})
#         keys = ["foo", "bar"]
#         payload = {
#             "key1": "val1",
#             "key2": "val2"
#         }

#         result = self.check._nest_payload(keys, payload)
#         expected = {
#             "foo": {
#                 "bar": payload
#             }
#         }

#         self.assertEquals(result, expected)