import requests
import unittest
from kickoff.buglist_creator import is_test_only_change, create_bugs_url, is_backout_bug, get_tag_versions, \
    format_return_value, create_short_url_with_prefix, get_bugs_in_changeset


class TestBuglistCreator(unittest.TestCase):

    def test_beta_1_release(self):
        release_object_54_0b1 = {
            'branch': 'releases/mozilla-beta',
            'product': 'firefox',
            'version': '54.0b1',
        }
        buglist_str_54_0b1 = create_bugs_url(release_object_54_0b1)
        assert buglist_str_54_0b1 == '', 'There should be no bugs to compare for beta 1.'

    def test_is_test_only_change(self):
        test_only_description = {
            'desc': 'something something something a=test-only something something something',
        }
        assert is_test_only_change(test_only_description)

    def test_is_backout_bug(self):
        backout_bugs_descs = [
            'I backed out this bug because',
            'Backing out this bug due to',
            'Backout bug xyz',
            'Back out bug xyz',
        ]
        for backout_desc in backout_bugs_descs:
            assert is_backout_bug(backout_desc.lower()), 'is_backout_bug did not catch a backout.'

    def test_get_tag_versions(self):
        current_and_previous_tag_versions = [
            (['firefox', 'releases/mozilla-beta', '53.0b10'], ('FIREFOX_53_0b10_RELEASE', 'FIREFOX_53_0b9_RELEASE')),
            (['firefox', 'releases/mozilla-release', '51.0.1'], ('FIREFOX_51_0_1_RELEASE', 'FIREFOX_51_0_RELEASE')),
            (['fennec', 'releases/mozilla-beta', '52.0b4'], ('FENNEC_52_0b4_RELEASE', 'FENNEC_52_0b2_RELEASE')),
        ]
        for args, expected in current_and_previous_tag_versions:
            results = get_tag_versions(args[0], args[1], args[2])
            assert expected == results

    def test_format_return_value(self):
        desc = 'Went from release a to release b\n'
        new_bugs = {'1220832', '1220837', '1347119'}
        backout_bugs = {'1340639', '1340641'}
        formatted_return_value = format_return_value(desc, new_bugs, backout_bugs)

        lines = formatted_return_value.split('\n')

        assert not formatted_return_value.endswith('\n'), "There shouldn't be a newline at the end."
        assert lines[0] == desc[:-1], 'Description in output does not match description in input.'
        assert lines[1] and lines[2], 'Incorrect formatting of the second and third lines.'

    def test_create_short_url_with_prefix(self):
        new_bugs = {'1220832', '1220837', '1347119'}
        backout_bugs = {'1340639', '1340641'}
        regular_bug_link, backout_bug_link = create_short_url_with_prefix(new_bugs, backout_bugs)

        assert 'Bugs since previous changeset' in regular_bug_link
        assert 'Backouts since previous changeset' in backout_bug_link

    def test_get_bugs_in_changeset(self):
        url = 'https://hg.mozilla.org/releases/mozilla-release/json-pushes?fromchange=d345b657d381&tochange=f87a819106bd&full=1'
        changeset_data = requests.get(url).json()
        bugs, backouts = get_bugs_in_changeset(changeset_data)

        assert bugs == {'1356563', '1344529', '1348409', '1341190', '1360626', '1337861', '1332731', '1328762',
                        '1306543', '1355870', '1358089', '1354911', '1354038'}
        assert backouts == {'1337861', '1320072'}


class TestHgJSONAPI(unittest.TestCase):
    """Tests the Hg JSON API to ensure correct behaviour"""

    def test_tags_json_format(self):
        json_tags_request_string = 'https://hg.mozilla.org/releases/mozilla-beta/json-tags'
        tags_json = requests.get(json_tags_request_string).json()
        assert 'tags' in tags_json, 'tags field missing from json-tags API.'

        for tag in tags_json['tags']:
            assert 'tag' in tag, 'Hg JSON API missing tag subfield.'

    def test_changeset_json_format(self):
        json_changeset_request_string = 'https://hg.mozilla.org/releases/mozilla-release/json-pushes?fromchange=FIREFOX_51_0_RELEASE&tochange=FIREFOX_51_0_1_RELEASE&full=1'
        changeset_json = requests.get(json_changeset_request_string).json()
        for changeset_entry in changeset_json.values():
            assert 'changesets' in changeset_entry, 'No changeset field for {}'.format(changeset_entry)

            for changeset in changeset_entry['changesets']:
                assert 'desc' in changeset
