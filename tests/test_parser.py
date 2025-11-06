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


class testConstitutionalAuthority(unittest.TestCase):
    def setUp(self):
        input_string = "tests/test_files/CREC-2005-07-20"
        self.crdir = cr.ParseCRDir(input_string)
        self.input_path = "tests/test_files/CREC-2005-07-20/html/CREC-2005-07-20-pt1-PgH6200-ConstitutionalAuthority.htm"

    def test_constitutional_authority_parsing(self):
        """
        Test that Constitutional Authority Statements are correctly parsed
        """
        crfile = cr.ParseCRFile(self.input_path, self.crdir)

        # Find all constitutional authority items
        ca_items = [item for item in crfile.crdoc.get("content", [])
                    if item.get("kind") == "constitutional_authority"]

        # Should have 4 constitutional authority statements
        self.assertEqual(len(ca_items), 4, "Should have 4 constitutional authority statements")

        # Test first statement: Mr. SMITH of Texas, H.R. 3456, Article I, Section 8, Clause 3
        self.assertEqual(ca_items[0]["speaker"], "Mr. SMITH of Texas")
        self.assertEqual(ca_items[0]["bill_number"], "H.R. 3456")
        self.assertEqual(ca_items[0]["constitutional_authority_article"], "I")
        self.assertEqual(ca_items[0]["constitutional_authority_section"], "8")
        self.assertEqual(ca_items[0]["constitutional_authority_clause"], "3")

        # Test second statement: Mrs. JOHNSON of Connecticut, H.R. 3457, Article I, Section 8, Clause 1 and 18
        self.assertEqual(ca_items[1]["speaker"], "Mrs. JOHNSON of Connecticut")
        self.assertEqual(ca_items[1]["bill_number"], "H.R. 3457")
        self.assertEqual(ca_items[1]["constitutional_authority_article"], "I")
        self.assertEqual(ca_items[1]["constitutional_authority_section"], "8")
        self.assertEqual(ca_items[1]["constitutional_authority_clause"], "1 and 18")

        # Test third statement: Mr. JONES, H.R. 3458, Article I, Section 8 (no clause)
        self.assertEqual(ca_items[2]["speaker"], "Mr. JONES")
        self.assertEqual(ca_items[2]["bill_number"], "H.R. 3458")
        self.assertEqual(ca_items[2]["constitutional_authority_article"], "I")
        self.assertEqual(ca_items[2]["constitutional_authority_section"], "8")
        self.assertNotIn("constitutional_authority_clause", ca_items[2])

        # Test fourth statement: Ms. WATERS, H.J. Res. 62, Article V (no section/clause)
        self.assertEqual(ca_items[3]["speaker"], "Ms. WATERS")
        self.assertEqual(ca_items[3]["bill_number"], "H.J. Res. 62")
        self.assertEqual(ca_items[3]["constitutional_authority_article"], "V")
        self.assertNotIn("constitutional_authority_section", ca_items[3])
        self.assertNotIn("constitutional_authority_clause", ca_items[3])
