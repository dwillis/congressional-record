import logging
import re


class crItem(object):
    def is_break(self, line):
        for pat in self.parent.item_breakers:
            if re.match(pat, line):
                return True

    def is_skip(self, line):
        for pat in self.parent.skip_items:
            if re.match(pat, line):
                return True

    def extract_constitutional_authority(self, text):
        """Extract Article, Section, and Clause from constitutional authority text."""
        # Initialize fields
        article = None
        section = None
        clause = None
        bill_number = None

        # Extract bill number (e.g., H.R. 3456, H.J. Res. 62)
        bill_match = re.search(r"(H\.(R\.|J\. Res\.|Con\. Res\.|Res\.)|S\.) \d+", text)
        if bill_match:
            bill_number = bill_match.group(0).strip()

        # Extract Article (Roman numerals)
        article_match = re.search(
            r"Article ([IVX]+|[0-9]+)", text, re.IGNORECASE
        )
        if article_match:
            article = article_match.group(1)

        # Extract Section
        section_match = re.search(
            r"Section (\d+)", text, re.IGNORECASE
        )
        if section_match:
            section = section_match.group(1)

        # Extract Clause
        clause_match = re.search(
            r"Clause (\d+(?:\s+and\s+(?:Clause\s+)?\d+)?)", text, re.IGNORECASE
        )
        if clause_match:
            clause = clause_match.group(1).replace("Clause ", "")

        return article, section, clause, bill_number

    def extract_prayer_info(self, text):
        """Extract name and title from prayer introduction text."""
        # Initialize fields
        prayer_name = None
        prayer_title = None

        # Pattern to match prayer introduction
        # Examples:
        # "The Chaplain, Dr. Barry C. Black, offered the following prayer:"
        # "The Reverend Dr. Kenneth L. Samuel, Pastor, Victory Baptist Church,
        # Stone Mountain, GA, offered the following prayer:"

        # First, try to extract the full introduction. The text might span multiple lines.
        # Remove newlines within the first few lines to handle line wrapping
        text_normalized = re.sub(r'\n', ' ', text[:500])  # Normalize first 500 chars
        # Normalize multiple spaces to single space
        text_normalized = re.sub(r'\s+', ' ', text_normalized)

        intro_match = re.search(
            r"The (.+?), offered the following prayer:",
            text_normalized,
            re.IGNORECASE
        )

        if intro_match:
            full_intro = intro_match.group(1).strip()

            # Try to parse the intro. It can be in two main formats:
            # 1. "Chaplain, Dr. Barry C. Black" (title, name)
            # 2. "Reverend Dr. Kenneth L. Samuel, Pastor, Victory Baptist Church, Stone Mountain, GA" (name, additional title/affiliation)

            # Check if it starts with "Chaplain" (Senate format)
            if full_intro.startswith("Chaplain"):
                # Senate format: "Chaplain, Dr. Barry C. Black"
                parts = full_intro.split(",", 1)
                if len(parts) == 2:
                    prayer_title = parts[0].strip()  # "Chaplain"
                    prayer_name = parts[1].strip()   # "Dr. Barry C. Black"
                else:
                    prayer_title = full_intro
            else:
                # House format: "Reverend Dr. Kenneth L. Samuel, Pastor, Victory Baptist Church, Stone Mountain, GA"
                # The name typically comes first, followed by additional title/affiliation
                parts = full_intro.split(",")
                if len(parts) >= 2:
                    # First part is typically the name with title prefix
                    prayer_name = parts[0].strip()
                    # Everything after is the additional title/affiliation
                    # Strip each part and rejoin to normalize whitespace
                    prayer_title = ", ".join(p.strip() for p in parts[1:])
                else:
                    prayer_name = full_intro

        return prayer_name, prayer_title

    def item_builder(self):
        parent = self.parent
        if parent.lines_remaining == False:
            logging.info("Reached end of document.")
            return
        item_types = parent.item_types
        content = [parent.cur_line]
        # What is this line
        for kind, params in list(item_types.items()):
            for pat in params["patterns"]:
                amatch = re.match(pat, parent.cur_line)
                if amatch:
                    self.item["kind"] = kind
                    # if params['special_case']:
                    #    self.item['flag'] = params['condition']
                    # else:
                    #    self.item['flag'] = False
                    if params["speaker_re"]:
                        them = amatch.group(params["speaker_group"])
                        self.item["speaker"] = them
                        if them in list(self.parent.speakers.keys()):
                            self.item["speaker_bioguide"] = self.parent.speakers[them][
                                "bioguideid"
                            ]
                        else:
                            self.item["speaker_bioguide"] = None
                    else:
                        self.item["speaker"] = params["speaker"]
                        self.item["speaker_bioguide"] = None
                    break
            if amatch:
                break
        # OK so now put everything else in with it
        # that doesn't interrupt an item
        # conditional logic for edge cases goes here.
        # if self.item['flag'] == 'emptystr':
        #    pass
        # else:
        for line in parent.the_text:
            if self.is_break(line):
                break
            elif self.is_skip(line):
                pass
            else:
                content.append(line)
        # The original text was split on newline, so ...
        item_text = "\n".join(content)
        self.item["text"] = item_text

        # Extract constitutional authority information if applicable
        if self.item["kind"] == "constitutional_authority":
            article, section, clause, bill_number = self.extract_constitutional_authority(item_text)
            if article:
                self.item["constitutional_authority_article"] = article
            if section:
                self.item["constitutional_authority_section"] = section
            if clause:
                self.item["constitutional_authority_clause"] = clause
            if bill_number:
                self.item["bill_number"] = bill_number

        # Extract prayer information if applicable
        if self.item["kind"] == "prayer":
            prayer_name, prayer_title = self.extract_prayer_info(item_text)
            if prayer_name:
                self.item["prayer_name"] = prayer_name
            if prayer_title:
                self.item["prayer_title"] = prayer_title

    def __init__(self, parent):
        self.item = {"kind": "Unknown", "speaker": "Unknown", "text": None, "turn": -1}

        self.parent = parent
        self.item_builder()
        # self.item['text'] = self.find_items(contentiter)
