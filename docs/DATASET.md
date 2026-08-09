# Dataset statement

## Source-derived description

The project reports describe a combination of:

- COCO 2014 object classes;
- locally captured images of regionally relevant obstacles and environments;
- manual annotation with LabelImg and/or Roboflow;
- random rotation, brightness changes, horizontal flips, crops and Gaussian noise;
- a held-out validation split.

## Canonical project record

The project author has standardised the recorded training corpus to **86,000 images**. This is the canonical image total used across the public repository and portfolio. Earlier draft totals are superseded by this author-confirmed figure.

The original dataset, manifest, export version, annotation archive, training YAML and reproducible split files were not supplied. The 86,000-image figure therefore documents the project record; it cannot be independently reconstructed from this repository alone.

## Remaining unresolved inconsistencies

The supplied reports still contain incompatible descriptions of class composition and evaluation, including references to:

- approximately 80 locally curated images;
- 80 COCO classes plus 20 additional classes;
- 100 total classes;
- controlled tests involving either 80 or 100 target instances.

These remaining discrepancies are preserved rather than silently rewritten as authoritative facts.

## Redistribution status

No training images or annotations are redistributed here. This avoids accidentally publishing:

- images without redistribution rights;
- identifiable participants without consent;
- stale Roboflow links or private project tokens;
- duplicate COCO content under unclear packaging terms.

## What is required for a future dataset release

A complete dataset release should include:

- provenance for every image source;
- permission and privacy review;
- class definitions and label map;
- immutable train/validation/test manifests;
- annotation format and validator;
- licence for custom images and annotations;
- class-frequency table;
- data-collection context and known biases;
- augmentation configuration and random seeds;
- a dataset card and changelog.
