import unittest
from kickoff.buglist_creator import create_bugs_url


class TestCreateBugsUrlDesktop(unittest.TestCase):

    def setUp(self):
        self.release_object_51_0_1 = {
            'branch': 'releases/mozilla-release',
            'product': 'firefox',
            'version': '51.0.1',
        }

        self.release_object_54_0b1 = {
            'branch': 'releases/mozilla-beta',
            'product': 'firefox',
            'version': '54.0b1',
        }

        self.release_object_53_0b10 = {
            'branch': 'releases/mozilla-beta',
            'product': 'firefox',
            'version': '53.0b10',
        }

    def test_51_0_1(self):
        buglist_str = create_bugs_url(self.release_object_51_0_1)
        desc, regular, backouts = buglist_str.split('\n')

        assert desc == 'Comparing Mercurial tag FIREFOX_51_0_RELEASE to FIREFOX_51_0_1_RELEASE:', 'Mercurial tags improperly generated'
        assert all(bug in regular for bug in ['1294650', '1333516', '1331808', '1333423', '1333663']), 'Some bugs are missing from the string'
        assert backouts == '', 'There should be no backouts for 51.0.1'

    def test_beta_54_0b1(self):
        buglist_str = create_bugs_url(self.release_object_54_0b1)

        assert buglist_str == '', 'Beta 1 releases should have no bugs to display.'

    def test_beta_53_0b10(self):
        buglist_str = create_bugs_url(self.release_object_53_0b10)
        desc, regular, backouts = buglist_str.split('\n')[:-1]

        assert desc == 'Comparing Mercurial tag FIREFOX_53_0b9_RELEASE to FIREFOX_53_0b10_RELEASE:', 'Mercurial tags improperly formatted, check 9 is before 10'
        assert all(str(bug) in regular
                   for bug in [1350661, 1350783, 1352926, 1350844, 1345873, 1353129, 1317191, 1333486, 1353476, 1344467,
                               1352406, 1341352, 1349581, 1353439, 1347075, 1352367, 1314543, 1328001, 1348941, 1349862,
                               1345687, 1342433, 1353740, 1352373, 1353333, 1348454, 1351964, 1353373, 1354496, 1333858,
                               1347617, 1349650, 1353041, 1354115, 1349719, 1346862, 1349612, 1353789]), 'Some bugs are missing'
        assert all(str(bug) in backouts
                   for bug in [1346862, 1352406, 1349719, 1192818]), 'Some backout bugs are missing'

    # TODO: Test ESR releases, test-only changes excluded,


class TestCreateBugsUrlMobile(unittest.TestCase):

    def setUp(self):
        self.release_object_53_0b1 = {
            'branch': 'releases/mozilla-release',
            'version': '53.0b1',
            'product': 'fennec'
        }

        self.release_object_38_0b10 = {
            'branch': 'releases/mozilla-release',
            'version': '38.0b10',
            'product': 'fennec',
        }

        self.release_object_xx_xx = {
            'branch': '',
            'version': '',
            'product': 'fennec'
        }

        self.release_object_xx_xx = {
            'branch': '',
            'version': '',
            'product': 'fennec'
        }

        self.release_object_xx_xx = {
            'branch': '',
            'version': '',
            'product': 'fennec'
        }

        self.release_object_xx_xx = {
            'branch': '',
            'version': '',
            'product': 'fennec'
        }

    def test_53_0b1(self):
        buglist_str = create_bugs_url(self.release_object_53_0b1)
        assert buglist_str == '', 'There should be no bugs to compare for beta 1.'

    def test_53_0b10(self):
        buglist_str = create_bugs_url(self.release_object_38_0b10)


