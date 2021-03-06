# -*- coding: utf-8 -*-
import json
import unittest

import requests
import requests_mock
from mock import MagicMock

from app.modules import util
from tests.helper import testdata_helper


@requests_mock.Mocker()
class TestUtil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    def test_itemize_app_id(self, _):
        group, vertical, subgroup, name, color = util.itemize_app_id("/group/vertical/name")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("", subgroup)
        self.assertEquals("name", name)
        self.assertEquals("GRN", color)

        group, vertical, subgroup, name, color = util.itemize_app_id("/group/vertical/name/blu")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("", subgroup)
        self.assertEquals("name", name)
        self.assertEquals("BLU", color)

        group, vertical, subgroup, name, color = util.itemize_app_id("/group/vertical/subgroup/name")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("subgroup", "subgroup")
        self.assertEquals("name", name)
        self.assertEquals("GRN", color)

        group, vertical, subgroup, name, color = util.itemize_app_id("/group/vertical/subgroup/name/blu")
        self.assertEquals("group", group)
        self.assertEquals("vertical", vertical)
        self.assertEquals("subgroup", "subgroup")
        self.assertEquals("name", name)
        self.assertEquals("BLU", color)

    def test_get_job_info(self, _):
        self.assertDictEqual({"status": 0, "message": "ok", "started": None, "stopped": None, "running": False},
                             util.get_job_info(
                                 job={
                                     "status": "OK",
                                     "message": "ok"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": None, "stopped": None, "running": True},
                             util.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "running": "some-id"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": "today", "stopped": None, "running": False},
                             util.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "started": "today"
                                 }))

        self.assertDictEqual({"status": 2, "message": "warning", "started": "today", "stopped": None, "running": False},
                             util.get_job_info(
                                 job={
                                     "status": "WARNING",
                                     "message": "warning",
                                     "started": "today",
                                     "running": None
                                 }))

        self.assertDictEqual(
            {"status": 2, "message": "warning", "started": "yesterday", "stopped": "today", "running": True},
            util.get_job_info(
                job={
                    "status": "WARNING",
                    "message": "warning",
                    "started": "yesterday",
                    "stopped": "today",
                    "running": "some-id"
                }))

    def test_get_application_status_200(self, request_mock):
        status = testdata_helper.get_status()
        request_mock.register_uri('GET', "http://some-status-url/status", text=json.dumps(status),
                                  headers={'x-color': 'GRN'})

        app_status, active_color, status_code = util.get_application_status("http://some-status-url/status", {})
        self.assertEquals(status, app_status)
        self.assertEquals("GRN", active_color)
        self.assertEquals(200, status_code)

    def test_get_application_status_with_cookies(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=200)

        app_status, active_color, status_code = util.get_application_status("http://some-status-url/status",
                                                                            {'cookies': {"cake": "strawberry"}})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(200, status_code)
        cookies = request_mock.request_history[0]._request._cookies._cookies['']['/']
        self.assertEquals(1, len(cookies))
        self.assertEquals({"cake": "strawberry"}, {cookies['cake'].name: cookies['cake'].value})

    def test_get_application_status_with_headers(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=200)

        app_status, active_color, status_code = util.get_application_status("http://some-status-url/status",
                                                                            {'headers': {"Accept": "strawberry"}})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(200, status_code)
        self.assertEquals("strawberry", request_mock.request_history[0]._request.headers['Accept'])

    def test_get_application_status_400(self, request_mock):
        request_mock.register_uri('GET', "http://some-status-url/status", status_code=400)

        app_status, active_color, status_code = util.get_application_status("http://some-status-url/status", {})
        self.assertEquals({}, app_status)
        self.assertEquals(None, active_color)
        self.assertEquals(400, status_code)

    def test_get_application_status_not_available(self, request_mock):
        tmp = requests.get
        requests.get = MagicMock(side_effect=requests.exceptions.Timeout)

        app_status, active_color, status_code = util.get_application_status("http://some-status-url/status", {})
        self.assertEquals({}, app_status)
        self.assertEquals(0, len(request_mock.request_history))
        self.assertEquals(None, active_color)
        self.assertEquals(None, status_code)
        requests.get = tmp
