import unittest
from kickoff.buglist_creator import create_bugs_url


class TestCreateBugsUrl(unittest.TestCase):

    def setUp(self):
        raise NotImplementedError('Finish implementing your tests guyyyyyy')

        self.release_object_51_0_1 = {
            'branch': 'releases/mozilla-release',
            'product': 'firefox',
            'version': '51.0.1',
        }

        self.ff_release_object_xxxxx = {
            'branch': 'releases/mozilla-aurora',
            'product': 'firefox',
            'version': '51.0a1',
        }

        self.release_object_xxxxx = {
            'branch': '',
            'product': '',
            'version': '',
        }

        self.release_object_xxxxx = {
            'branch': '',
            'product': '',
            'version': '',
        }

        self.release_object_xxxxx = {
            'branch': '',
            'product': '',
            'version': '',
        }

    def test_release_object_51_0_1(self):
        standard_bugs, backout_bugs = create_bugs_url(self.release_object_51_0_1)

        assert backout_bugs == ''
        assert standard_bugs == 'Relevant bugs: https://bugzilla.mozilla.org/buglist.cgi?bug_id=1294650%2C1333516%2C%2C1331808%2C1333423%2C1333663'
