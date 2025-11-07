# PR Notes: Improve Parser Classification for Special Report Types

## Problem Statement

The Congressional Record parser was doing a poor job of classifying things other than speeches. Specifically, it could not identify special report types like **Foreign travel expenditure reports**.

Example documents that should be identified:
- [Foreign travel expenditure report from 2025-10-21](https://www.congress.gov/congressional-record/volume-171/issue-174/house-section/article/H4545-7)
- Similar reports found in: 2025-10-21 and 2018-04-24

The requirement was to **identify these reports** in the JSON output without attempting to parse their contents.

## Solution Overview

Added an optional `document_type` field to the JSON schema that identifies special report types. The parser now automatically detects and classifies these documents based on title patterns.

### Design Principles

1. **Minimal disruption**: Added as an optional field to maintain backward compatibility
2. **Document-level classification**: Works at the document level, not at the content item level
3. **Identification only**: Detects and labels reports without parsing their internal structure
4. **Extensible**: Easy to add more document types in the future

## Changes Made

### 1. Schema Enhancement

**File**: `congressionalrecord/schema.py`

Added a new optional field to `CongressionalRecordDocument`:

```python
document_type: Optional[str] = Field(
    None,
    description=(
        "Type of document when it's a special report rather than regular proceedings. "
        "Examples: 'foreign_travel_expenditure' for foreign travel expenditure reports. "
        "None for regular proceedings/speeches."
    ),
)
```

**Placement**: Added between the `title` and `content` fields to keep metadata together.

**Values**:
- `None` (or omitted): Regular Congressional proceedings/speeches
- `"foreign_travel_expenditure"`: Foreign travel expenditure reports
- Future values can be added for other special report types

### 2. Parser Logic

**File**: `congressionalrecord/govinfo/cr_parser.py`

Added `detect_document_type()` method (lines 372-392):

```python
def detect_document_type(self, title=None, doc_title=None):
    """
    Detect special document types based on title patterns.
    Returns a document type string or None for regular proceedings.
    """
    # Combine title and doc_title for checking
    text_to_check = []
    if title:
        text_to_check.append(title.lower())
    if doc_title:
        text_to_check.append(doc_title.lower())

    combined_text = " ".join(text_to_check)

    # Check for foreign travel expenditure reports
    if "foreign travel" in combined_text and "expenditure" in combined_text:
        return "foreign_travel_expenditure"

    # Future document types can be added here

    return None
```

**Integration**: Modified `write_page()` method to call detection and set the field:

```python
# Detect document type
document_type = self.detect_document_type(title=title, doc_title=self.doc_title)
if document_type:
    self.crdoc["document_type"] = document_type
else:
    self.crdoc["document_type"] = None
```

### 3. Documentation Updates

**File**: `docs/schema.md`

- Updated the Top-Level Document table to include the `document_type` field
- Added a new "Document Types" section with a reference table
- Updated the example JSON to include `document_type: null`

### 4. Dependencies

**File**: `pyproject.toml`

Added `pydantic>=2.0` to the dependencies list. This was already required by `schema.py` but was missing from the project dependencies.

## Technical Details

### Detection Logic

The parser checks both the parsed `title` (from content) and `doc_title` (from metadata) for patterns:

1. Converts both to lowercase for case-insensitive matching
2. Combines them into a single string
3. Checks for keyword combinations (e.g., "foreign travel" + "expenditure")
4. Returns the appropriate document type or `None`

### Backward Compatibility

The implementation is fully backward compatible:

- **Optional field**: Existing code that doesn't know about `document_type` will continue to work
- **Null-safe**: The field defaults to `None` if not specified
- **Schema validation**: Old JSON files without this field will still validate successfully
- **No breaking changes**: Content structure remains unchanged

### Example Output

For a foreign travel expenditure report:

```json
{
  "id": "CREC-2025-10-21-pt1-PgH4545",
  "header": { ... },
  "doc_title": "Foreign Travel Expenditure Report",
  "title": "FOREIGN TRAVEL EXPENDITURE REPORT",
  "document_type": "foreign_travel_expenditure",
  "content": [ ... ]
}
```

For regular proceedings:

```json
{
  "id": "CREC-2025-01-30-pt1-PgS524",
  "header": { ... },
  "doc_title": "SUBMISSION OF CONCURRENT AND SENATE RESOLUTIONS",
  "title": "SUBMISSION OF CONCURRENT AND SENATE RESOLUTIONS",
  "document_type": null,
  "content": [ ... ]
}
```

## Future Extensibility

The design makes it easy to add more document types:

```python
def detect_document_type(self, title=None, doc_title=None):
    # ... existing code ...

    combined_text = " ".join(text_to_check)

    # Check for foreign travel expenditure reports
    if "foreign travel" in combined_text and "expenditure" in combined_text:
        return "foreign_travel_expenditure"

    # Add new document types here
    if "daily digest" in combined_text:
        return "daily_digest"

    if "financial disclosure" in combined_text:
        return "financial_disclosure"

    return None
```

## Testing

Validated the changes with:

1. **Schema validation tests**: Confirmed that the Pydantic schema accepts:
   - Documents with `document_type` set to a value
   - Documents with `document_type` set to `None`
   - Documents without the `document_type` field (backward compatibility)

2. **Detection logic tests**: Verified that the pattern matching correctly identifies:
   - Foreign travel expenditure reports with various title formats
   - Regular proceedings that should not be classified
   - Edge cases with keywords in different fields

## Migration Notes

No migration required. The change is backward compatible:

- Existing JSON files remain valid
- Existing code can ignore the new field
- New code can check for special document types when needed

## Files Modified

1. `congressionalrecord/schema.py` - Added `document_type` field
2. `congressionalrecord/govinfo/cr_parser.py` - Added detection method
3. `docs/schema.md` - Updated documentation
4. `pyproject.toml` - Added missing pydantic dependency

## References

- Original issue: Parser does poor job classifying non-speech items
- Example URL: https://www.congress.gov/congressional-record/volume-171/issue-174/house-section/article/H4545-7
- Example dates with expenditure reports: 2025-10-21, 2018-04-24
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
