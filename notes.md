# Implementation Notes

## Constitutional Authority Statement Parsing (2025-11-06)

### Overview
Added support for parsing Constitutional Authority Statements for legislation introduced in the House of Representatives. These statements cite the specific constitutional authority under which Congress has the power to enact proposed legislation.

### Changes Made

#### 1. Schema Updates (`congressionalrecord/schema.py`)
- Added new `kind` type: `constitutional_authority` to ContentItem
- Added optional fields to `ContentItem`:
  - `bill_number`: Bill or resolution number (e.g., "H.R. 3456", "H.J. Res. 62")
  - `constitutional_authority_article`: Article of the Constitution (e.g., "I", "V")
  - `constitutional_authority_section`: Section number (e.g., "8")
  - `constitutional_authority_clause`: Clause number(s) (e.g., "3", "1 and 18")

#### 2. Parser Updates (`congressionalrecord/govinfo/cr_parser.py`)
- Added `re_constitutional_authority` pattern to match "By Mr./Mrs./Ms. NAME:" format
- Added `re_bill_number` pattern to identify bill/resolution numbers
- Modified `re_allcaps` pattern to exclude bill numbers from matching as titles (preventing incorrect splitting)
- Added `constitutional_authority` item type to `item_types` dictionary with:
  - `speaker_re: True` to extract the sponsor's name
  - `break_flow: True` to separate individual statements
  - `special_case: True` for custom extraction logic
- Positioned `constitutional_authority` before `recorder` in `item_types` to ensure correct pattern matching priority

#### 3. Extraction Logic (`congressionalrecord/govinfo/subclasses.py`)
- Added `extract_constitutional_authority()` method to extract:
  - Bill/resolution number using regex: `(H\.(R\.|J\. Res\.|Con\. Res\.|Res\.)|S\.) \d+`
  - Article using regex: `Article ([IVX]+|[0-9]+)` (supports Roman and Arabic numerals)
  - Section using regex: `Section (\d+)`
  - Clause using regex: `Clause (\d+(?:\s+and\s+(?:Clause\s+)?\d+)?)` (supports compound clauses)
- Modified `item_builder()` to call extraction method when `kind == "constitutional_authority"`
- Extraction only adds fields to output if they are found in the text

#### 4. Test Files
- Created test HTML file: `tests/test_files/CREC-2005-07-20/html/CREC-2005-07-20-pt1-PgH6200-ConstitutionalAuthority.htm`
  - Contains 4 sample constitutional authority statements
  - Tests various formats: simple clause, compound clauses, article only
- Updated `tests/test_files/CREC-2005-07-20/mods.xml` with metadata entry
- Generated expected JSON output: `tests/test_files/CREC-2005-07-20/json/CREC-2005-07-20-pt1-PgH6200-ConstitutionalAuthority.json`

#### 5. Test Suite (`tests/test_parser.py`)
- Added `testConstitutionalAuthority` class with:
  - `test_constitutional_authority_parsing()` method
  - Validates correct parsing of all 4 test statements
  - Verifies proper extraction of bill numbers, articles, sections, and clauses
  - Tests edge cases (missing clauses, missing sections)

### Example Output

```json
{
  "kind": "constitutional_authority",
  "speaker": "Mr. SMITH of Texas",
  "speaker_bioguide": null,
  "text": "  By Mr. SMITH of Texas:\n  H.R. 3456.\n  Congress has the power...",
  "turn": -1,
  "itemno": 2,
  "bill_number": "H.R. 3456",
  "constitutional_authority_article": "I",
  "constitutional_authority_section": "8",
  "constitutional_authority_clause": "3"
}
```

### Technical Challenges and Solutions

#### Challenge 1: Pattern Matching Order
**Problem**: Initial implementation had `constitutional_authority` pattern checked after `recorder` pattern, causing "By Mr. X:" to be incorrectly classified as recorder statements.

**Solution**: Reordered `item_types` dictionary to check `constitutional_authority` before `recorder`.

#### Challenge 2: Item Splitting
**Problem**: Bill numbers (e.g., "H.R. 3456") were matching the `re_allcaps` title pattern, causing constitutional authority statements to split into multiple items.

**Solution**: Modified `re_allcaps` pattern to use negative lookahead `(?!...H\.(R\.|J\. Res\.|...)...` to exclude bill numbers from matching as titles.

#### Challenge 3: Format Variations
**Problem**: Constitutional authority statements have varying formats:
- Article, Section, and Clause (most common)
- Article and Section only
- Article only (e.g., Article V for constitutional amendments)

**Solution**: Made section and clause fields optional, only adding them to output if found in text. Used flexible regex patterns to handle variations.

### Testing

Run the test suite:
```bash
uv run python -m pytest tests/test_parser.py::testConstitutionalAuthority -v
```

Or run all tests:
```bash
uv run python run_tests.py
```

### Future Enhancements

Potential improvements for future versions:
1. Support for amendments to the Constitution (currently handles Article V correctly)
2. Enhanced extraction of multiple constitutional citations in a single statement
3. Validation of Article/Section/Clause combinations against actual Constitution structure
4. Link to specific constitutional text on official sources

### References

- Example constitutional authority statement: https://www.congress.gov/congressional-record/volume-171/issue-179/house-section/article/H4560-17
- House Rules, Clause 7, Rule XII: Requires constitutional authority statements for bills and joint resolutions
