import logging
import os
import re
from shutil import copyfile

from bs4 import BeautifulSoup, NavigableString, Tag

_log_format = "%(asctime)s - [%(name)s] %(levelname)s: %(message)s"
_date_format = "%H:%M:%S"

logging.basicConfig(
    format=_log_format,
    datefmt=_date_format,
    level=logging.INFO
)

_logger = logging.getLogger(__name__)

_reg2 = re.compile(r"^(.*[^/])(/|$)")
_reg3 = re.compile(r"[\n\t&_#/?=\-+|\s\\]+")
_reg4 = re.compile(r"(\-?\.html?)+")
_reg5 = re.compile(r"(\\\w+)")

# Keywords for filtering headers
_deprecated_words = [
    "access", "control",
    "children", "special", "audience",
    "third", "party", "providers", "services",
    "international", "transfers",
    "update", "policy", "statement", "changes to this policy",
    "contact", "who we are", "links",
    "rights", "options",
]


def do(input_folder, global_folder_results):
    """
    Algorithm: 1. Find files with Huawei in name 2. Load them into beautiful
    soup format 3. Determine keywords for headers 4. Search headers with
    templates 5. If header is bad, delete paragraphs until new header has
    been found or file end has been reached

    What to delete:
    * How to access & control your personal data
    * How we process children" personal data (special audience)
    * Third party providers and their services
    * International transfers of your personal data
    * Updates to this policy
    * How to contact us

    :return: None
    """
    tmp = os.path.join(global_folder_results, "huawei_filter_backup")

    exceptions_rules = {
        "www.huaweicloud.com-intl-en-us-declaration-sa-prp.html": [
            template17,
            template18,
            contents_template11,
        ],
        "www.huaweicloud.com-intl-en-us-declaration-sa-cookies.html": [
            template17,
            template18,
            contents_template11,
        ]
    }

    templates = [
        template1,
        template2,
        template3,
        template4,
        template5,
        template6,
        template7,
        template8,
        template9,
        template10,
        template11,
        template12,
        template13,
        template14,
        template15,
        template16,
        template19,
        template20,
        template21,
        template22,
        template23,
        template24,
        contents_template1,
        contents_template2,
        contents_template3,
        contents_template4,
        contents_template5,
        contents_template6,
        contents_template7,
        contents_template8,
        contents_template9,
        contents_template10,
    ]

    input_files = []
    for (dir_path, dir_names, file_names) in os.walk(input_folder):
        input_files.extend([(dir_path, f) for f in file_names])

    for f in input_files:
        os.rename(os.path.join(*f), os.path.join(f[0], normalize_name(f[1])))

    input_files = []
    for (dir_path, dir_names, file_names) in os.walk(input_folder):
        input_files.extend([(dir_path, f) for f in file_names])

    # Filter huawei files
    files_to_filter = [f for f in input_files if
                       "huawei" or "privacy-drcn" in f[1]]

    _logger.info(f"There are files to filter: {files_to_filter}")

    # Backup files
    if not os.path.exists(tmp):
        os.mkdir(tmp)

    for f in files_to_filter:
        if not os.path.exists(os.path.join(tmp, f[1])):
            copyfile(os.path.join(*f), os.path.join(tmp, f[1]))
        else:
            copyfile(os.path.join(tmp, f[1]), os.path.join(*f))

    # Handle general files
    # Filtering exceptional files
    files_to_filter = [f for f in input_files if
                       f[1] not in exceptions_rules.keys()]

    for f in files_to_filter:
        soup = read_policy(f)
        _logger.info(f"Filtering policy {f[1]}")
        store_policy(f, filter_policy(soup, templates))

    # Handle exceptions
    for key in exceptions_rules:
        soup = read_policy((input_folder, key))
        _logger.info(f"Filtering policy {key}")
        store_policy((input_folder, key),
                     filter_policy(soup, exceptions_rules[key]))


def read_policy(file_path):
    _logger.info(f"Opening policy {file_path[1]} from {file_path[0]}")
    with open(os.path.join(*file_path), "r", encoding="utf-8") as stream:
        soup = BeautifulSoup(stream, "lxml")
    return soup


def store_policy(file_path, soup):
    _logger.info(f"Storing policy {file_path[1]} to {file_path[0]}")
    with open(os.path.join(*file_path), "w", encoding="utf-8") as stream:
        stream.write(soup.prettify())


def normalize_name(name):
    name = _reg2.match(name)
    name = _reg3.sub("-", name.group(1))
    name = _reg4.sub("", name)
    return f"{name.lower()}.html"


def test_header(header):
    clean_header = _reg5.sub(" ", header.lower())
    clean_header = _reg3.sub(" ", clean_header)

    for dw in _deprecated_words:
        if dw in clean_header:
            return True


def filter_policy(soup, templates):
    valid_headers_list = []
    headers_to_delete_list = []

    for t in templates:
        r = t(soup)
        valid_headers_list.extend(r[0])
        headers_to_delete_list.extend(r[1])

    main_list = [*valid_headers_list, *headers_to_delete_list]
    to_remove = []

    # for sh in main_list:
    #     if sh.nextSibling in main_list:
    #         to_remove.append(sh)

    # if headers_to_delete_list:
    #
    #     first_header = None
    #     for sibling in main_list:
    #         if all([True if s not in valid_headers_list else False for s in sibling.previous_siblings]):
    #             first_header = sibling
    #
    #     for sibling in first_header.previous_siblings:
    #         to_remove.append(sibling)

    for sh in headers_to_delete_list:
        to_remove.append(sh)
        for sibling in sh.next_siblings:
            if sibling in valid_headers_list:
                break
            to_remove.append(sibling)

    for e in to_remove:
        e.extract()

    return soup


def template1(soup):
    """

    MARKUP VARIANT 1
    <p class="medium margin-top-24">
        <span>...</span>
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p:not(:has(> a)).medium.margin-top-24 > span:not(.indent-point):not(:has(> a))"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template2(soup):
    """

    MARKUP VARIANT 2
    <p>
        <strong>
            <span>
                <span>...</span>
                ...
            </span>
        </strong>
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p:not(:has(> a)) > strong > span:not(.indent-point) > span:not(.indent-point)"):
        if test_header(e.parent.parent.parent.text):
            headers_to_delete.append(e.parent.parent.parent)
        else:
            valid_headers.append(e.parent.parent.parent)

    return valid_headers, headers_to_delete


def template3(soup):
    """

    MARKUP VARIANT 3
    <p class="emui_master_subtitle medium margin-top-24">
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p.emui_master_subtitle.medium.margin-top-24:not(:has(> a))"):
        valid = True

        try:
            if not isinstance(e, Tag) or e.name != "p":
                valid = False

            c0 = list(e.children)

            if len(c0) != 1:
                valid = False

            if not isinstance(c0[0], NavigableString):
                valid = False

        except (AttributeError, IndexError):
            valid = False

        if valid:
            if test_header(e.text):
                headers_to_delete.append(e)
            else:
                valid_headers.append(e)

    return valid_headers, headers_to_delete


def template4(soup):
    """

    MARKUP VARIANT 4
    <strong>
        <div>
            ...
        </div>
    </strong>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("strong > div"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template5(soup):
    """

    MARKUP VARIANT 5
    <p class="textSizeSubTitle2">
        <strong>
            ...
        </strong>
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("p:not(:has(> a)).textSizeSubTitle2 > strong"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template6(soup):
    """

    MARKUP VARIANT 6
    <div class="title title-bold one_txt">
        ...
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.title.title-bold.one_txt"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template7(soup):
    """

    MARKUP VARIANT 7
    <div class="title title-bold one_txt">
        <span>
            ...
        </span>
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "div.title.title-bold.one_txt > span:not(.indent-point)"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template8(soup):
    """

    MARKUP VARIANT 8
    <div class="title title-bold one_txt">
        <span>
            ...
        </span>
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "div.title.title-bold.one_txt > span:not(.indent-point)"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template9(soup):
    """

    MARKUP VARIANT 9
    <p class="medium margin-top-24" vid="title_health_kit">
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("p:not(:has(> a)).medium.margin-top-24"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template10(soup):
    """

    MARKUP VARIANT 10
    <h2>...</h2>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("h2"):
        valid = True

        try:
            if not isinstance(e, Tag) or e.name != "h2":
                valid = False

            c0 = list(e.children)

            if len(c0) != 1:
                valid = False

            if not isinstance(c0[0], NavigableString):
                valid = False

        except (AttributeError, IndexError):
            valid = False

        if valid:
            if test_header(e.text):
                headers_to_delete.append(e)
            else:
                valid_headers.append(e)

    return valid_headers, headers_to_delete


def template11(soup):
    """

    MARKUP VARIANT 11
    <div class="text-one-column__container js-one-column">
        <div class="heading heading-04 text-one-column__block-title">
            ...
        </div>
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.text-one-column__container.js-one-column > "
                         "div.heading.heading-04.text-one-column__block-title"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template12(soup):
    """

    MARKUP VARIANT 12
    <p class="top-title">
        <a>
            ...
        </a>
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("p.top-title > a"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template13(soup):
    """

    MARKUP VARIANT 13
    <strong>
        <span>
            ...
        </span>
        ...
    </strong>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("strong > span:not(.indent-point)"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template14(soup):
    """

    MARKUP VARIANT 14
    <div class="text1">
        <a>
            ...
        </a>
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.text1 > a"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template15(soup):
    """

    MARKUP VARIANT 15
    <div class="sectionTitle">
        ...
    </div>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.sectionTitle"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template16(soup):
    """

    MARKUP VARIANT 16
    <h1>
        <span>
            ...
        </span>
    </h1>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("h1 > span:not(.indent-point)"):
        if test_header(e.parent.text):
            headers_to_delete.append(e.parent)
        else:
            valid_headers.append(e.parent)

    return valid_headers, headers_to_delete


def template17(soup):
    """

    MARKUP VARIANT 17
    <p>
        <strong>
            <span>
                ...
            </span>
        </strong>
        ...
    </p>

    :param soup:
    :return:
    """
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p:not(:has(> a)) > strong > span:not(.indent-point)"):
        if test_header(e.parent.parent.text):
            headers_to_delete.append(e.parent.parent)
        else:
            valid_headers.append(e.parent.parent)

    return valid_headers, headers_to_delete


def template18(soup):
    hide = soup.select(
        "div.hide-content, div.law_left, div.print, hr, h2.show-print")
    for h in hide:
        h.extract()

    content = soup.select("div#content")
    for c in content:
        for s in list(c.previous_siblings):
            s.extract()
        for s in list(c.next_siblings):
            s.extract()

    return [], []


def template19(soup):
    content = soup.select("main, div.main, div#main, div.content, div#content")
    for c in content:
        for s in list(c.previous_siblings):
            s.extract()
        for s in list(c.next_siblings):
            s.extract()
    return [], []


def template20(soup):
    try:
        soup.html["style"] = ""
    except KeyError:
        pass
    return [], []


def template21(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p.emui_mst_subtitle.margin-top-24:not(:has(> a)):has(> span:not(.indent-point):not(:has(> a)):not(:has(> span:not(.indent-point))))"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template22(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p.emui_mst_subtitle.margin-top-24:not(:has(> a)):has(> span:not(.indent-point):not(:has(> a)):has(> span:not(.indent-point):not(:has(> a))))"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template23(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p.emui_mst_subtitle.margin-top-8:not(:has(> a)):has(> span:not(.indent-point):not(:has(> a)):not(:has(> span:not(.indent-point))))"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def template24(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select(
            "p.emui_mst_subtitle.margin-top-8:not(:has(> a)):has(> span:not(.indent-point):not(:has(> a)):has(> span:not(.indent-point):not(:has(> a))))"):
        if test_header(e.text):
            headers_to_delete.append(e)
        else:
            valid_headers.append(e)

    return valid_headers, headers_to_delete


def contents_template1(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.title-bold.two_txt"):
        if "This Statement describes" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template2(soup):
    valid_headers = []
    headers_to_delete = []
    for e in soup.select(
            "p.emui_mst_subtitle:has(> span:not(.indent-point):has(> span:not(.indent-point):has(> span:not(.indent-point):has(> span:not(.indent-point)))))"):
        if "This Statement describes" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template3(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("p"):
        if "This Statement describes" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template4(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("p"):
        if "This Statement covers the following topics" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template5(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div.text2.marginS"):
        if "This Statement describes" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template6(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("ol:has(> li:has(> button))"):
        headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template7(soup):
    valid_headers = []
    headers_to_delete = []

    l = []
    l.extend(list(soup.body.children))

    while len(l) > 0:
        e = l.pop(0)

        if isinstance(e, NavigableString):
            if "This Statement describes" in str(e):
                headers_to_delete.append(e)
        else:
            l.extend(list(e.children))

    return valid_headers, headers_to_delete


def contents_template8(soup):
    valid_headers = []
    headers_to_delete = []

    for e in soup.select("div > span:not(.indent-point)"):
        if "Acceptance of Privacy Policy" in e.parent.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template9(soup):
    valid_headers = []
    headers_to_delete = []
    for e in soup.select("p.regular.margin-top-8"):
        if "This statement describes the following" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template10(soup):
    valid_headers = []
    headers_to_delete = []
    for e in soup.select("p"):
        if "This Policy describes" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete


def contents_template11(soup):
    valid_headers = []
    headers_to_delete = []
    for e in soup.select("p:has(> span:not(.indent-point))"):
        if "We have created this Statement to help you understand" in e.text:
            headers_to_delete.append(e)

    return valid_headers, headers_to_delete
