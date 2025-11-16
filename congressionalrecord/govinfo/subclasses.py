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

    def extract_committee_election_info(self, text):
        """Extract committees and members from committee election announcement."""
        committees = []

        # Normalize text: join lines that don't start with "COMMITTEE ON"
        # This handles cases where member names are split across lines
        normalized_lines = []
        current_line = ""

        for line in text.split('\n'):
            stripped = line.strip()
            if re.match(r'^\s*COMMITTEE ON', line, re.IGNORECASE):
                # New committee - save previous line and start new one
                if current_line:
                    normalized_lines.append(current_line)
                current_line = line
            elif stripped and current_line:
                # Continuation of previous line - join with space
                current_line += " " + stripped
            elif stripped:
                # Standalone line (not part of committee)
                if current_line:
                    normalized_lines.append(current_line)
                    current_line = ""
                normalized_lines.append(line)

        if current_line:
            normalized_lines.append(current_line)

        # Now parse the normalized lines
        for line in normalized_lines:
            committee_match = re.match(r'^\s*COMMITTEE ON ([A-Z\s]+):', line, re.IGNORECASE)
            if committee_match:
                committee_name = "COMMITTEE ON " + committee_match.group(1).strip()
                # Extract members from this line (after the colon)
                members_part = line.split(':', 1)[1] if ':' in line else ''
                members = self._extract_members_from_text(members_part)

                if members:
                    committees.append({
                        "name": committee_name,
                        "members": members
                    })

        return committees

    def _extract_members_from_text(self, text):
        """Extract member names from text line."""
        members = []
        # Pattern to match names like "Mr. RYAN of Wisconsin", "Mrs. BLACKBURN of Tennessee"
        # Improved pattern to capture the full name including state
        pattern = r'M(?:r|s|rs|iss)\.\s+[A-Z]+(?:\s+of\s+[A-Za-z\s]+)?'

        for match in re.finditer(pattern, text):
            member = match.group(0).strip()
            # Remove trailing punctuation
            member = re.sub(r'[,.]$', '', member).strip()
            if member:
                members.append(member)
        return members

    def extract_committee_resignation_info(self, text):
        """Extract committee and member from committee resignation letter."""
        committee = None
        member = None
        state = None

        # Look for committee name in resignation text
        committee_match = re.search(r'Committee on ([A-Za-z\s]+)', text, re.IGNORECASE)
        if committee_match:
            committee = "Committee on " + committee_match.group(1).strip().rstrip(',.')

        # Look for member name in signature
        # Pattern: name followed by "U.S. Senator from [State]"
        member_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z]\.\s+)?[A-Z][a-z]+),?\s+U\.S\. Senator from ([A-Za-z\s]+)', text)
        if member_match:
            member = member_match.group(1).strip()
            state = member_match.group(2).strip().rstrip('.')

        return committee, member, state

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

        # Extract committee election information if applicable
        if self.item["kind"] == "committee_election":
            committees = self.extract_committee_election_info(item_text)
            if committees:
                self.item["committees"] = committees
            # Fix speaker name to include "The"
            if self.item["speaker"] and not self.item["speaker"].startswith("The "):
                self.item["speaker"] = "The " + self.item["speaker"]

        # Extract committee resignation information if applicable
        if self.item["kind"] == "committee_resignation":
            committee, member, state = self.extract_committee_resignation_info(item_text)
            if committee:
                self.item["committee"] = committee
            if member:
                self.item["member"] = member
                # For committee resignations, the speaker is the person resigning
                self.item["speaker"] = member
            if state:
                self.item["state"] = state

    def __init__(self, parent):
        self.item = {"kind": "Unknown", "speaker": "Unknown", "text": None, "turn": -1}

        self.parent = parent
        self.item_builder()
        # self.item['text'] = self.find_items(contentiter)
