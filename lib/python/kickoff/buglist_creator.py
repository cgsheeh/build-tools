import logging
import re
import requests
from operator import itemgetter
from pkg_resources import parse_version
from simplejson import JSONDecodeError

BACKOUT_REGEX = r'backout|back out|backed out|backing out'
BUGZILLA_BUGLIST_TEMPLATE = 'https://bugzilla.mozilla.org/buglist.cgi?bug_id={bugs}\n'
BUG_NUMBER_REGEX = r'bug \d*'
CHANGELOG_TO_FROM_STRING = '{product}_{version}_RELEASE'
CHANGESET_URL_TEMPLATE = 'https://hg.mozilla.org/{release_branch}/json-pushes?fromchange={from_version}&tochange={to_version}&full=1'
LIST_DESCRIPTION_TEMPLATE = 'Comparing Mercurial tag {from_version} to {to_version}:\n'
MERCURIAL_TAGS_URL_TEMPLATE = 'https://hg.mozilla.org/{release_branch}/json-tags'
NO_BUGS = ''  # Return this when bug list can't be created

log = logging.getLogger(__name__)


class BuglistCreatorException(Exception):
    """Custom Exception for Buglist creator"""
    pass


def create_bugs_url(release):
    """
    Creates list of bugs and backout bugs for release-drivers email

    :param release: Dict containing information about release, from Ship-It
    :return: Tuple: (Text + link to standard bugs in changeset, text + link to backout bugs in changeset,)
    """
    try:
        current_version_dot = release['version']
        if re.search(r'b1$', current_version_dot):
            # If the version is beta 1, don't make any links
            return NO_BUGS

        product = release['product']
        branch = release['branch']

        current_version_tag, previous_version_tag = _get_tag_versions(product, branch, current_version_dot)
        description_string = LIST_DESCRIPTION_TEMPLATE.format(from_version=previous_version_tag,
                                                              to_version=current_version_tag)

        resp = requests.get(CHANGESET_URL_TEMPLATE.format(release_branch=branch,
                                                          from_version=previous_version_tag, to_version=current_version_tag))
        changeset_data = resp.json()

        unique_bugs, unique_backout_bugs = set(), set()
        for data in changeset_data.values():
            for changeset in data['changesets']:
                if _is_test_only_change(changeset):
                    continue

                changeset_desc_lower = changeset['desc'].lower()
                bug_re = re.search(BUG_NUMBER_REGEX, changeset_desc_lower)

                if bug_re:
                    bug_number = bug_re.group().split(' ')[1]

                    if _is_backout_bug(changeset_desc_lower):
                        unique_backout_bugs.add(bug_number)
                    else:
                        unique_bugs.add(bug_number)

        if unique_bugs or unique_backout_bugs:
            return _format_return_value(description_string, unique_bugs, unique_backout_bugs)
        else:
            return ''

    except (requests.HTTPError, JSONDecodeError, BuglistCreatorException,) as err:
        log.info(err)
        return NO_BUGS


def _is_test_only_change(changeset):
    return 'a=test-only' in changeset['desc']


def _is_backout_bug(changeset_description_lowercase):
    return re.search(BACKOUT_REGEX, changeset_description_lowercase)


def _create_buglist_url(buglist, backout_buglist):
    # Create link if there are bugs, else empty string
    if buglist:
        regular_bugs = '%2C'.join(buglist)
        regular_bugs = 'Relevant bugs: ' + BUGZILLA_BUGLIST_TEMPLATE.format(bugs=regular_bugs)
    else:
        regular_bugs = ''

    # Do the same thing for backouts
    if backout_buglist:
        backout_bugs = '%2C'.join(backout_buglist)
        backout_bugs = 'Backout bugs: ' + BUGZILLA_BUGLIST_TEMPLATE.format(bugs=backout_bugs)
    else:
        backout_bugs = ''

    return regular_bugs, backout_bugs


def _dot_version_to_tag_version(product, dot_version):
    underscore_version = dot_version.replace('.', '_')
    return CHANGELOG_TO_FROM_STRING.format(product=product.upper(), version=underscore_version)


def _tag_version_to_dot_version_parse(tag):
    dot_version = '.'.join(tag.split('_')[1:-1])
    return parse_version(dot_version)


def _get_tag_versions(product, branch, current_version_dot):
    """Gets the previous hg version tag for the product and branch, given the current version tag"""
    current_version_tag = _dot_version_to_tag_version(product, current_version_dot)

    tag_url = MERCURIAL_TAGS_URL_TEMPLATE.format(release_branch=branch)
    response_json = requests.get(tag_url).json()

    def _invalid_tag_filter(tag):
        """Filters by product and removes incorrect major version + base, end releases"""
        major_version = current_version_dot.split('.')[0]
        prod_major_version_re = r'^{product}_{major_version}'.format(product=product.upper(), major_version=major_version)

        return 'BASE' not in tag and \
               'END' not in tag and \
               'RELEASE' in tag and \
               re.match(prod_major_version_re, tag)

    # Get rid of irrelevant tags, sort by date and extract the tag string
    tags = set(map(itemgetter('tag'), response_json['tags']))
    tags = filter(_invalid_tag_filter, tags)
    dot_tag_version_mapping = zip(map(_tag_version_to_dot_version_parse, tags), tags)
    dot_tag_version_mapping = sorted(dot_tag_version_mapping, key=itemgetter(0))

    try:
        next_version_index = map(itemgetter(0), dot_tag_version_mapping).index(parse_version(current_version_dot)) - 1
    except ValueError as err:
        raise BuglistCreatorException("Couldn't find a tag for {}".format(current_version_tag))

    return current_version_tag, dot_tag_version_mapping[next_version_index][1]


def _format_return_value(description, unique_bugs, unique_backout_bugs):
    reg_bugs_link, backout_bugs_link = _create_buglist_url(unique_bugs, unique_backout_bugs)
    return """{description}{regular_bz_url}{backout_bz_url}""".format(description=description,
                                                                      regular_bz_url=reg_bugs_link,
                                                                      backout_bz_url=backout_bugs_link)


if __name__ == '__main__':
    import pickle
    dl = pickle.load(open('d.p', 'r'))

    dum = []
    for d in dl:
        if d['product'] == 'fennec':
            s = create_bugs_url(d)
            dum.append(s)

    from pprint import pprint
    pprint(dum)
