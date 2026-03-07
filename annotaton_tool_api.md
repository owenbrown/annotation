# Annotation Tool API

## Overview

Research and build the page that annotators and managers use to annotate a specific document.

## Inputs

### Image

An image stored locally.

### Annotation Data

Each annotation consists of:

- **Geometry**: A bounding box or polygon coordinates.
- **Key-value data**: Each key maps to a value of one of the following types:
  - String
  - Number
  - Boolean
  - Selection from an enumerated list of strings

Annotation data has two layers:

- **Pre-annotation**: Created at the time the job was created.
- **Current**: The value the annotator set when they last reviewed the document.

We store both because annotators often review their work before submitting, and they may want to refer back to the pre-annotation (e.g., if they accidentally delete a large chunk of text).

### Per-Document Field Assignments

The existing system accepts a schema and tasks the annotator with annotating every field in the schema. This is a problem. Instead, each document in a job should have specific fields assigned for annotation.

This creates an ambiguity: how do we distinguish between "this field was not present in the document" and "this field was not assigned for review"? To resolve this, we need to record explicit **"Field not in Document"** values.

## Honeypot Data

A honeypot is deliberately incorrect pre-annotation, used to measure annotator accuracy. This is necessary because annotators are sometimes correcting data that is already believed to be ~98% accurate.

### Open Questions

**Representation**: If a field appears twice in a document at positions A and B, and we want the honeypot to display data at positions B and C instead, what is the best way to:

1. Store this in the database?
2. Present it to the manager so it's not confusing?
3. Make it easy for the manager to set up?

**Possible design affordance**: A "Copy Real to Honeypot" action that copies all real annotations into the honeypot layer, after which the manager edits or deletes entries as needed. This needs further thought.
