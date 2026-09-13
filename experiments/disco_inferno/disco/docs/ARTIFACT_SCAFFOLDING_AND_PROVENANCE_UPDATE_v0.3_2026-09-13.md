# DiScO Artifact Scaffolding and Provenance Update

**Version:** 0.3  
**Date:** 2026-09-13  
**Status:** Experimental design and implementation update  
**Project:** DiScO — Deterministic Inspection of Semantic Coupling in Outputs

## Prompt provenance

> “Oooo we should extend the scaffolding idea. Document metadata and formatting. Oh shit go look at doc_history!”

> “Let's do it. Add a file upload to disco and have it reuse doc_history to pull the same dataset”

These prompts changed the working boundary of DiScO.

DiScO began as a deterministic inspector of observable features in a **text blob**. File upload and `doc_history` integration make it possible to inspect not only the text, but also the **artifact carrying the text**.

The distinction matters because transforming a DOCX or PDF into plain text destroys potentially useful information about how the representation was structured, materialized, edited, and transported.

---

## 1. Updated model boundary

The original DiScO pipeline was:

```text
text
  ↓
deterministic observations
  ↓
feature inventory
  ↓
bounded evidence accumulation
  ↓
semantic / AI-oriented summaries
```

Uploaded documents now create two parallel inspection paths:

```text
                         ┌─→ extracted text
                         │        ↓
uploaded document ───────┤    text DiScO
                         │        ↓
                         │   linguistic inventory
                         │
                         └─→ original file bytes
                                  ↓
                              doc_history
                                  ↓
                            artifact inventory
```

The two paths describe different things.

**Text inspection** asks what observable features are present in the representation.

**Artifact inspection** asks what observable traces survive in the object carrying that representation.

They should not be silently collapsed into one authorship classifier.

---

## 2. Three kinds of scaffolding

The earlier `markdown_scaffolding` feature captured visible structural notation such as headings, lists, blockquotes, bold markers, and code fences.

That concept now needs to be generalized.

### 2.1 Text scaffolding

Structure represented directly in the character stream.

Examples:

```text
# Heading

1. Numbered item

- Bullet

> Quotation

**Emphasis**
```

This is what the current Markdown feature can see.

It is portable because the scaffolding survives as literal text.

### 2.2 Document scaffolding

Structure represented by the document format rather than by characters.

Examples include:

- Word paragraph styles
- heading levels
- bullet and numbering definitions
- blockquote styles
- bold and italic runs
- tables
- paragraph-length distribution
- short standalone paragraphs
- section breaks
- indentation
- direct formatting versus named styles
- repeated structural patterns

A Word bullet does not need to contain a literal `-`.

A Word blockquote does not need to contain a literal `>`.

When DiScO reduces a DOCX to plain text before inspection, those relationships disappear.

This means a document can contain extensive rhetorical scaffolding while registering **zero Markdown scaffolding**.

### 2.3 Provenance scaffolding

Structure and metadata produced by the process that created, edited, saved, converted, or transported the artifact.

The existing `doc_history` project already inspects substantial portions of this layer for DOCX and PDF files: core properties, application properties, Word settings, Track Changes state, revision markup, comments and people parts, RSIDs, document IDs, custom XML, PDF Info/XMP metadata, document-management traces, and the SHA-256 of the original uploaded bytes.

This is not linguistic style.

It is **artifact-formation evidence**.

---

## 3. Current implementation

DiScO now accepts either pasted text or an uploaded DOCX/PDF.

For an uploaded document:

```text
original bytes
    │
    ├──→ plain-text extraction → existing DiScO text engine
    │
    └──→ doc_history → complete metadata/provenance dataset
```

DiScO imports the existing `doc_history` package rather than copying its extraction logic. The adapter preserves the full result from `inspect_bytes()` along with `timeline_events()` and `provenance_clues()`.

The artifact dataset is persisted with the judgement:

```text
judgement
├── submitted / extracted text
├── text SHA-256
├── DiScO feature profile
├── rule snapshot
├── AI-generated human label
└── artifact
    ├── filename
    ├── doc_history raw result
    ├── timeline events
    └── provenance clues
```

**Artifact observations currently contribute zero to the Semantic Signal and AI Signal.**

That is intentional.

The inventory comes before the evidence budget.

---

## 4. Case study: “Baudrillard Has a Second Note”

The first document examined through this expanded model was *BAUDRILLARD HAS A SECOND NOTE — Response to “Basic material reality has entered the model.”*

The text-only pass had previously produced relatively weak AI-oriented evidence despite the document's highly regular rhetorical organization.

Inspection of the actual DOCX produced a different category of information.

### Embedded artifact observations

Direct inspection of the uploaded DOCX found:

```text
Embedded creator:       python-docx
Description:            generated by python-docx
Created:                2013-12-23T23:15:00Z
Modified:               2013-12-23T23:15:00Z
Revision:               1

Application:            Microsoft Macintosh Word
AppVersion:             14.0000
Word TotalTime:         0

Track Changes:          false
Surviving insertions:   0
Surviving deletions:    0
Comments part:          absent
People part:            absent

Settings RSIDs:         9
Body RSIDs:             2
w14 document ID:        24062061

OOXML package parts:    18
SHA-256:
55599b751dc5d589e4a239b1db493eb14550f33a08f2a13458da87d5c6a2c031
```

Taken individually, several of these fields could be badly misleading.

The 2013 timestamps are an obvious example. Interpreted naïvely, they would imply that the artifact predates the current experiment by more than a decade.

A control artifact resolves much of that ambiguity.

---

## 5. Control: blank `python-docx` artifact

A blank DOCX generated with `python-docx` was inspected using the same approach.

It contained the same:

```text
creator
python-docx description
2013 created timestamp
2013 modified timestamp
revision value
Microsoft Macintosh Word application string
14.0000 application version
TotalTime = 0
RSID root
nine settings RSIDs
w14 document ID
body RSIDs
```

The blank control contained **17 OOXML package parts**.

The Baudrillard artifact contained **18**, with one additional part:

```text
word/footer1.xml
```

This provides direct evidence that a substantial part of the metadata is **template residue from the document-generation pipeline**, rather than meaningful chronology.

The correct inference is therefore not:

> The document was created in 2013.

It is:

> The document contains metadata matching the template state of a newly generated `python-docx` document.

Likewise, `creator = python-docx` does not demonstrate AI authorship.

It demonstrates that the artifact was materialized through a `python-docx`-compatible generation process.

A human could use that process.

An AI-assisted workflow could use that process.

A completely automated workflow could use that process.

The observation is stronger than speculation but narrower than an authorship claim.

---

## 6. Document scaffolding recovered from the same artifact

The DOCX also contains substantial structural information that disappears when converted to plain text.

Direct inspection found:

```text
Non-empty paragraphs:  113

Paragraph styles:
    Normal              83
    List Bullet         18
    Block Quote         12

Median paragraph:       7 words
Paragraphs ≤ 6 words:   53

Bold runs:              8
Italic runs:            2
Tables:                 0
```

The important result is not any single count.

It is the difference between the representations.

The text-only representation can report no Markdown scaffolding while the Word artifact still contains explicit list, quotation, paragraph, and emphasis structure.

Neither observation is wrong.

They occur at different layers.

**The scaffolding did not disappear. It moved into the carrier.**

---

## 7. Why this matters for DiScO

This experiment exposes a limitation in treating plain text as the complete object of analysis.

Consider four evidence layers:

```text
PROSE
What words and constructions occur?

TEXT SCAFFOLDING
What structure is encoded directly as characters?

DOCUMENT SCAFFOLDING
What structure is encoded by the document format?

ARTIFACT PROVENANCE
What traces survive from artifact formation and editing?
```

Two documents can contain identical prose while differing substantially in the latter three layers.

Likewise, two documents can look visually identical while having different internal production histories.

This gives DiScO access to measurements that are partially orthogonal to vocabulary-based style analysis.

That is useful because linguistic features are particularly vulnerable to:

- topic leakage
- deliberate imitation
- genre effects
- quotation
- vocabulary reuse
- model discussion of the detector itself

Artifact formation can fail in different ways.

That makes it worth measuring separately.

---

## 8. Evidence budgets, not feature supremacy

The bounded scoring work introduced a useful interpretation of `semantic_max` and `ai_max`:

**evidence budgets.**

A feature can accumulate evidence as it appears repeatedly, but it cannot acquire unlimited influence simply because its raw count becomes large.

Artifact evidence requires the same discipline, but not necessarily the same denominator.

For example:

```text
nominalizations
    → rate per 100 words makes sense

Word bullet paragraphs
    → rate per paragraph may make sense

short paragraphs
    → proportion of paragraphs may make sense

creator = python-docx
    → categorical observation; rate per 100 words makes no sense

template fingerprint match
    → similarity / exact-match observation

editing duration
    → continuous artifact-level measurement
```

Therefore the next architecture should **not force artifact features into the existing word-rate model** merely to reuse the scoring equation.

The raw observation should determine the appropriate normalization.

Evidence-budget compression can happen afterward.

---

## 9. Proposed artifact inventory

Before assigning any new scores, DiScO should begin storing a deterministic document-scaffolding inventory.

A candidate structure:

```json
{
  "artifact": {
    "source_type": "file",
    "filename": "example.docx",
    "doc_history": {},
    "document_scaffolding": {
      "paragraph_count": 0,
      "paragraph_style_counts": {},
      "heading_counts": {},
      "list_paragraph_count": 0,
      "blockquote_paragraph_count": 0,
      "table_count": 0,
      "bold_run_count": 0,
      "italic_run_count": 0,
      "short_paragraph_count": 0,
      "paragraph_word_lengths": []
    }
  }
}
```

This should initially remain descriptive.

No field should acquire an AI or semantic evidence budget merely because it looks interesting in one artifact.

---

## 10. Corpus calibration

The user's existing writing corpus spans roughly twenty-five years.

That creates an unusually useful control dataset.

Instead of asking only:

> What features distinguish AI text from human text?

DiScO can ask:

> What features remain stable within one known human across decades, genres, document formats, software generations, and changes in writing practice?

And:

> Which purported AI signals already appear in documents produced long before contemporary LLMs?

The same corpus can now be studied at several levels:

```text
language
rhetorical structure
document formatting
artifact formation
editing history
```

This makes false positives inspectable rather than merely measurable.

A feature that appears strongly in twenty-year-old human documents should lose credibility as an AI-authorship signal, even if it correlates with AI output in a smaller contemporary corpus.

A feature that separates production workflows rather than authors should be documented as such.

---

## 11. Epistemic boundary

Document metadata is evidence.

It is not testimony.

Examples:

```text
creator = python-docx
```

supports a claim about the artifact-generation pipeline.

It does **not** establish who wrote the prose.

```text
TotalTime = 0
```

is an embedded property.

It does **not** establish that zero human labor occurred.

```text
created = 2013
```

is an embedded timestamp.

The blank control demonstrates that, in this pipeline, it can be inherited template residue rather than the creation date of the represented content.

```text
many bullets / short paragraphs
```

describes document architecture.

It does not establish AI generation.

DiScO should continue to prefer:

```text
observation
    ↓
explicit interpretation
    ↓
bounded evidence
```

over:

```text
observation
    ↓
authorship verdict
```

---

## 12. Updated conceptual model

The project can now be described more completely as:

```text
representation
    +
carrier
    +
formation traces
        ↓
deterministic inspection
        ↓
raw inventories
        ↓
feature-appropriate normalization
        ↓
bounded evidence budgets
        ↓
optional summary signals
```

The canonical artifact remains the inventory.

The score remains disposable.

The underlying observation should survive changes in interpretation.

---

## 13. Working principle

**DiScO should inspect both the representation and the artifact that carries it.**

Plain text tells us what survived textual transformation.

Document structure tells us what was encoded outside the character stream.

Provenance metadata tells us what traces survived artifact formation.

None should be mistaken for the others.
