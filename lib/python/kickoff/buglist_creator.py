import logging
import re
import requests
from operator import itemgetter
from pkg_resources import parse_version
from simplejson import JSONDecodeError

BACKOUT_REGEX = r'back(\s?)out|backed out|backing out'
BUGZILLA_BUGLIST_TEMPLATE = 'https://bugzilla.mozilla.org/buglist.cgi?bug_id={bugs}'
BUG_NUMBER_REGEX = r'bug \d+'
CHANGELOG_TO_FROM_STRING = '{product}_{version}_RELEASE'
CHANGESET_URL_TEMPLATE = 'https://hg.mozilla.org/{release_branch}/json-pushes?fromchange={from_version}&tochange={to_version}&full=1'
LIST_DESCRIPTION_TEMPLATE = 'Comparing Mercurial tag {from_version} to {to_version}:\n'
MERCURIAL_TAGS_URL_TEMPLATE = 'https://hg.mozilla.org/{release_branch}/json-tags'
NO_BUGS = ''  # Return this when bug list can't be created
URL_SHORTENER_TEMPLATE = 'https://bugzilla.mozilla.org/rest/bitly/shorten?url={url}'

log = logging.getLogger(__name__)


class BuglistCreatorException(Exception):
    """Custom Exception for Buglist creator"""
    pass


def create_bugs_url(release):
    """
    Creates list of bugs and backout bugs for release-drivers email

    :param release: dict -> containing information about release, from Ship-It
    :return: str -> description of compared releases, with Bugzilla links containing all bugs in changeset
    """
    try:
        current_version_dot = release['version']
        if re.search(r'b1$', current_version_dot):
            # If the version is beta 1, don't make any links
            return NO_BUGS

        product = release['product']
        branch = release['branch']

        current_version_tag, previous_version_tag = get_tag_versions(product, branch, current_version_dot)
        description_string = LIST_DESCRIPTION_TEMPLATE.format(from_version=previous_version_tag,
                                                              to_version=current_version_tag)

        resp = requests.get(CHANGESET_URL_TEMPLATE.format(release_branch=branch,
                                                          from_version=previous_version_tag,
                                                          to_version=current_version_tag))
        changeset_data = resp.json()

        unique_bugs, unique_backout_bugs = get_bugs_in_changeset(changeset_data)

        if unique_bugs or unique_backout_bugs:
            return format_return_value(description_string, unique_bugs, unique_backout_bugs)
        else:
            return NO_BUGS

    except (requests.HTTPError, JSONDecodeError, BuglistCreatorException,) as err:
        log.info(err)
        return NO_BUGS


def get_bugs_in_changeset(changeset_data):
    unique_bugs, unique_backout_bugs = set(), set()
    for data in changeset_data.values():
        for changeset in data['changesets']:
            if is_test_only_change(changeset):
                continue

            changeset_desc_lower = changeset['desc'].lower()
            bug_re = re.search(BUG_NUMBER_REGEX, changeset_desc_lower)

            if bug_re:
                bug_number = bug_re.group().split(' ')[1]
                print bug_re.group()

                if is_backout_bug(changeset_desc_lower):
                    unique_backout_bugs.add(bug_number)
                else:
                    unique_bugs.add(bug_number)

    return unique_bugs, unique_backout_bugs


def is_test_only_change(changeset):
    return 'a=test-only' in changeset['desc']


def is_backout_bug(changeset_description_lowercase):
    return re.search(BACKOUT_REGEX, changeset_description_lowercase)


def create_short_url_with_prefix(buglist, backout_buglist):
    # Create link if there are bugs, else empty string
    urls = []
    for set_of_bugs, prefix in ((buglist, 'Bugs since previous changeset: ',),
                               (backout_buglist, 'Backouts since previous changeset: ',)):
        if set_of_bugs:
            long_bugzilla_link = BUGZILLA_BUGLIST_TEMPLATE.format(bugs='%2C'.join(set_of_bugs))
            url = requests.get(URL_SHORTENER_TEMPLATE.format(url=long_bugzilla_link)).json()['url']
            url = prefix + url + '\n'
        else:
            url = ''

        urls.append(url)

    return urls[0], urls[1]


def dot_version_to_tag_version(product, dot_version):
    underscore_version = dot_version.replace('.', '_')
    return CHANGELOG_TO_FROM_STRING.format(product=product.upper(), version=underscore_version)


def tag_version_to_dot_version_parse(tag):
    dot_version = '.'.join(tag.split('_')[1:-1])
    return parse_version(dot_version)


def get_tag_versions(product, branch, current_version_dot):
    """Gets the previous hg version tag for the product and branch, given the current version tag"""
    current_version_tag = dot_version_to_tag_version(product, current_version_dot)

    tag_url = MERCURIAL_TAGS_URL_TEMPLATE.format(release_branch=branch)
    response_json = requests.get(tag_url).json()

    def _invalid_tag_filter(tag):
        """Filters by product and removes incorrect major version + base, end releases"""
        major_version = current_version_dot.split('.')[0]
        prod_major_version_re = r'^{product}_{major_version}'.format(product=product.upper(),
                                                                     major_version=major_version)

        return 'BASE' not in tag and \
               'END' not in tag and \
               'RELEASE' in tag and \
               re.match(prod_major_version_re, tag)

    # Get rid of irrelevant tags, sort by date and extract the tag string
    tags = set(map(itemgetter('tag'), response_json['tags']))
    tags = filter(_invalid_tag_filter, tags)
    dot_tag_version_mapping = zip(map(tag_version_to_dot_version_parse, tags), tags)
    dot_tag_version_mapping = sorted(dot_tag_version_mapping, key=itemgetter(0))

    try:
        next_version_index = map(itemgetter(0), dot_tag_version_mapping).index(parse_version(current_version_dot)) - 1
    except ValueError as err:
        raise BuglistCreatorException("Couldn't find a tag for {}: {}".format(current_version_tag, err))

    return current_version_tag, dot_tag_version_mapping[next_version_index][1]


def format_return_value(description, unique_bugs, unique_backout_bugs):
    reg_bugs_link, backout_bugs_link = create_short_url_with_prefix(unique_bugs, unique_backout_bugs)
    return_str = '{description}{regular_bz_url}{backout_bz_url}'.format(description=description,
                                                                        regular_bz_url=reg_bugs_link,
                                                                        backout_bz_url=backout_bugs_link)

    return return_str[:-1] if return_str.endswith('\n') else return_str  # Remove trailing newline

#
# if __name__ == '__main__':
#     # import pickle
#     # dl = pickle.load(open('d.p', 'r'))
#     #
#     # dum = []
#     # for d in dl:
#     #     if d['product'] == 'fennec':
#     #         s = create_bugs_url(d)
#     #         dum.append(s)
#     #
#     # from pprint import pprint
#     # pprint(dum)
#
#     url = 'https://hg.mozilla.org/releases/mozilla-release/json-pushes?fromchange=d345b657d381&tochange=f87a819106bd&full=1'
#     changeset_data = requests.get(url).json()
#
#     bugs, backouts = get_bugs_in_changeset(changeset_data)
#     print bugs
#     print backouts
