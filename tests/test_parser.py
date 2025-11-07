import json
import logging
import os
import random
import re
import unittest

from congressionalrecord.govinfo import cr_parser as cr

logging.basicConfig(filename="tests.log", level=logging.DEBUG)

"""
These tests make sure that basic parser functions
run as expected, generating files full of JSON output
such that nothing that looks like
a speech exists outside of a "speech" JSON item.
"""


class testCRDir(unittest.TestCase):
    def setUp(self):
        pass

    def test_crdir(self):
        """
        CRDir pointed at correct path
        """
        input_string = "tests/test_files/CREC-2005-07-20"
        crdir = cr.ParseCRDir(input_string)
        self.assertEqual(crdir.cr_dir, input_string)


class testCRFile(unittest.TestCase):
    def setUp(self):
        input_string = "tests/test_files/CREC-2005-07-20"
        self.crdir = cr.ParseCRDir(input_string)
        input_dir = os.path.join(input_string, "html")
        input_file = random.choice(os.listdir(input_dir))  # nosec
        self.input_path = os.path.join(input_dir, input_file)

    def test_top_level_keys(self):
        """
        CRFile has all the right fixins' in the crdoc
        """
        crfile = cr.ParseCRFile(self.input_path, self.crdir)
        for x in ["doc_title", "header", "content", "id"]:
            self.assertIn(x, crfile.crdoc.keys(), msg="{0} not in crdoc!".format(x))

    def test_content_length(self):
        crfile = cr.ParseCRFile(self.input_path, self.crdir)
        self.assertGreater(len(crfile.crdoc["content"]), 0, msg="No items in content!")


class testLineBreak(unittest.TestCase):
    def setUp(self):
        self.sp = re.compile(
            r"^(\s{1,2}|<bullet>)(?P<name>((((Mr)|(Ms)|(Mrs)|(Miss))\. (([-A-Z\'])(\s)?)+( of [A-Z][a-z]+)?)|((The ((VICE|ACTING|Acting) )?(PRESIDENT|SPEAKER|CHAIR(MAN)?)( pro tempore)?)|(The PRESIDING OFFICER)|(The CLERK)|(The CHIEF JUSTICE)|(The VICE PRESIDENT)|(Mr\. Counsel [A-Z]+))( \([A-Za-z.\- ]+\))?))\."
        )

    def test_fixedLineBreak(self):
        rootdir = "tests/test_files/CREC-2005-07-20/json"
        for apath in os.listdir(rootdir):
            thepath = os.path.join(rootdir, apath)
            with open(thepath, "r") as thefile:
                thejson = json.load(thefile)
            for item in thejson["content"]:
                if item["kind"] != "speech":
                    for line in item["text"].split("\n"):
                        self.assertFalse(self.sp.match(line), "Check {0}".format(apath))


class testTitleContent(unittest.TestCase):
    """
    Test that titles don't contain content that should be
    classified as speech. The regex fix prevents speech patterns from being
    matched as titles.
    """

    def test_titles_not_speech_patterns(self):
        """
        Ensure titles don't contain speech patterns that would indicate
        they are actually speech content misclassified as titles.
        This test specifically checks for patterns like ", I " (first person speech)
        and titles starting with "I " which are clear indicators of speech.
        """
        rootdir = "tests/test_files/CREC-2005-07-20/json"
        # Patterns that indicate speech rather than titles
        speech_patterns = [
            (re.compile(r',\s+I\s'), ", I "),  # ", I " pattern common in first-person speech
            (re.compile(r'^\s*I\s'), "starting with 'I '"),  # Starting with "I "
        ]

        for apath in os.listdir(rootdir):
            thepath = os.path.join(rootdir, apath)
            with open(thepath, "r") as thefile:
                thejson = json.load(thefile)

            # Check document title if present
            if thejson.get("title"):
                title = thejson["title"]
                # Check for speech patterns that shouldn't be in titles
                for pattern, description in speech_patterns:
                    self.assertIsNone(
                        pattern.search(title),
                        f"Document title contains speech pattern ({description}) in {apath}: {title[:100]}..."
                    )

            # Check titles within content items
            for i, item in enumerate(thejson["content"]):
                if item["kind"] == "title":
                    title_text = item["text"]

                    # Check for speech patterns
                    for pattern, description in speech_patterns:
                        self.assertIsNone(
                            pattern.search(title_text),
                            f"Content item #{i} title contains speech pattern ({description}) in {apath}: {title_text[:150]}..."
                        )
