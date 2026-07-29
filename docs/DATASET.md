# Dataset statement

## Source-derived description

The project reports describe a combination of:

- COCO 2014 object classes;
- locally captured images of regionally relevant obstacles and environments;
- manual annotation with LabelImg and/or Roboflow;
- random rotation, brightness changes, horizontal flips, crops and Gaussian noise;
- a held-out validation split.

## Unresolved inconsistencies

The supplied reports contain incompatible dataset descriptions, including references to:

- approximately 80 locally curated images;
- 80 COCO classes plus 20 additional classes;
- 100 total classes;
- 85,000 images with a 70/30 split;
- controlled tests involving either 80 or 100 target instances.

The original dataset, manifest, export version, annotation archive, training YAML and reproducible split files were not supplied. This repository does not silently choose one conflicting number as authoritative.

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
