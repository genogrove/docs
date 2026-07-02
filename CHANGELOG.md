# Changelog

All notable changes to the genogrove documentation project will be documented in this file.

## 2026-07-01

### Added
- Documented the pygenogrove `region=` keyword on `BedReader`/`GffReader`/`VcfReader` in the Python I/O tab of `guide/io.md` — a new Region-Based Random Access section mirroring the C++ side (#179): 1-based-inclusive tabix coordinate convention vs each reader's native system, bgzip+tabix/CSI index requirement with `bgzip`/`tabix`/`bcftools` recipes, `RuntimeError`-at-construction contract, empty-region streaming fallback, and O(region) framing; plus `region=""` added to the three reader signatures ([#181](https://github.com/genogrove/docs/pull/181), closes [#180](https://github.com/genogrove/docs/issues/180))

## 2026-06-30

### Added
- Documented region-based random access for the BED/GFF/VCF readers (the `region` tabix-string option) in `guide/io.md` — coordinate convention (1-based inclusive), bgzip+tabix/CSI index requirements with `bgzip`/`tabix`/`bcftools index` recipes, `std::runtime_error` cases, empty-region streaming fallback, and O(region) performance — plus a `tabix_reader` autodoc stub in `reference/cpp/io.md` ([#179](https://github.com/genogrove/docs/pull/179), closes [#177](https://github.com/genogrove/docs/issues/177))

## 2026-06-29

### Changed
- Bumped docs version to 0.24.8 in `conf.py` and the README badge ([8646978](https://github.com/genogrove/docs/commit/8646978), closes [#178](https://github.com/genogrove/docs/issues/178))

## 2026-06-27

### Changed
- Bumped the `pygenogrove` pin to 0.6.2 (`source/requirements.txt` + `conf.py` tab label) to pick up wheel 313 ([a3b89a4](https://github.com/genogrove/docs/commit/a3b89a4))
- Dropped the C++ `release` from the navbar title (`html_title = "genogrove"`) — genogrove and pygenogrove version independently and each guide tab is already version-stamped, so the global one was redundant and misleading ([#176](https://github.com/genogrove/docs/pull/176))

## 2026-06-26

### Added
- Documented the genogrove v0.24.7 public API surface in one batch ([#172](https://github.com/genogrove/docs/pull/172)): the C++ `vcf_reader` / `vcf_entry` / `sample_genotype` / `vcf_reader_options` + value types in `guide/io.md` with autodoc stubs in `reference/cpp/io.md` (closes [#161](https://github.com/genogrove/docs/issues/161)); the node-less `grove_to_sif(std::ostream&)` whole-grove SIF export in `guide/serialization.md` (closes [#162](https://github.com/genogrove/docs/issues/162)); the 12-byte `.gg` file header (`gg_header` / `gg_payload_type`) layout + re-index note (closes [#142](https://github.com/genogrove/docs/issues/142)); `idx`/`isec` GFF/GTF dispatch, `.gg` `payload_type`, and the cross-type-query restriction in `cli.md` (closes [#143](https://github.com/genogrove/docs/issues/143)); `idx -l/--links` TSV format, constraints, and a worked example (closes [#145](https://github.com/genogrove/docs/issues/145)); dataless `grove<key_type>` (`data_type = void`) in `guide/grove/grove.md` (closes [#146](https://github.com/genogrove/docs/issues/146)); and the `add_edge` no-deduplication / parallel-edge behavior in `guide/grove/graph.md` (closes [#144](https://github.com/genogrove/docs/issues/144))

### Changed
- Bumped the `pygenogrove` pin to 0.6.0 (`source/requirements.txt` + `conf.py` tab label) so autodoc builds the Python reference from the surface the guide already documents — `Numeric`/`Kmer` + `NumericGrove`/`KmerGrove`, `VcfReader`/`VcfEntry`, `to_sif`, and the `StringRegistry → Registry` rename (the pin had lagged at 0.5.0, which lacked those classes) ([#175](https://github.com/genogrove/docs/pull/175))
- Synced the guide's per-topic C++/Python language tabs (`:sync:` keys) so a reader's language choice persists across all pages, and stamped each tab label with the version it reflects (**C++ · genogrove 0.24.7** / **Python · pygenogrove 0.5.0**, sourced centrally from `conf.py`); added a User Guide index note explaining the two version tracks ([#174](https://github.com/genogrove/docs/pull/174))
- Bumped docs version to 0.24.7 in `conf.py` and the README badge ([dbb3386](https://github.com/genogrove/docs/commit/dbb3386), [41dfdce](https://github.com/genogrove/docs/commit/41dfdce), closes [#163](https://github.com/genogrove/docs/issues/163))
- Restructured the Python docs: split tutorial-style content out of **API Reference** into per-topic C++/Python tabs under `guide/**` (`sphinx_design` tab-sets), and made `reference/python/*` autodoc-generated from the compiled `pygenogrove` module; wired `conf.py` autodoc with a guard that omits the Python reference when the module is not importable. Folded in the outstanding pygenogrove doc fixes: `Registry` rename + two-arg `intern(key, payload)`/JSON payloads, `Numeric`/`Kmer` point keys + `NumericGrove`/`KmerGrove`, threading & GIL notes, the predicate-callback contract, `Grove.to_sif(path)` export, and `VcfReader`/`VcfEntry`/`SampleGenotype` ([#171](https://github.com/genogrove/docs/pull/171), closes [#165](https://github.com/genogrove/docs/issues/165), closes [#166](https://github.com/genogrove/docs/issues/166), closes [#167](https://github.com/genogrove/docs/issues/167), closes [#168](https://github.com/genogrove/docs/issues/168), closes [#169](https://github.com/genogrove/docs/issues/169), closes [#170](https://github.com/genogrove/docs/issues/170))
- Bumped the `repos/genogrove` clone to upstream `1af9e79` to pick up the Doxygen header-comment fixes ([genogrove#455](https://github.com/genogrove/genogrove/pull/455), closes [genogrove#454](https://github.com/genogrove/genogrove/issues/454)), clearing the `@HD`/`#CHROM`/`grove_insert @param` warnings from the docs build
- Pinned `pygenogrove==0.5.0` in `source/requirements.txt` so autodoc builds against the documented API surface instead of drifting to the latest PyPI release ([#171](https://github.com/genogrove/docs/pull/171))
- Dropped the unused `pygenogrove` clone from `.readthedocs.yaml` `pre_build` — `Doxyfile` only scans `repos/genogrove/include` and the Python reference comes from the pinned PyPI wheel ([#171](https://github.com/genogrove/docs/pull/171))

### Fixed
- Pinned the Read the Docs build to Python 3.12 in `.readthedocs.yaml` so `pygenogrove` installs from its prebuilt wheel — pygenogrove ships cp39–cp312 wheels only, so on Python 3.13 pip fell back to the sdist and failed compiling from source (no htslib in the RTD env), breaking the build at the pip step ([#173](https://github.com/genogrove/docs/pull/173))
- Corrected the `Numeric` constructor signature in `guide/data_types.md` (stray `GenomicCoordinate ->` copy-paste artifact) ([#171](https://github.com/genogrove/docs/pull/171))

## 2026-06-13

### Added
- Documented the **pygenogrove** Python API (current v0.5.0 surface, reflecting the 0.4.0+ genomics-first redesign), replacing the "coming soon" placeholder with a 7-page reference under `reference/python/`: `coordinates.md` (strand-aware `GenomicCoordinate` key, `*` wildcard vs `.` unstranded, sort order), `grove.md` (universal JSON `Grove`, predicate-filtered `flanking`, `remove_key`/`compact` + vertex/storage counts, serialization), `graph.md` (graph overlay, external keys, labelled edges, edge cleanup/bulk linking), `typed_groves.md` (`BedGrove`/`GffGrove` + `BedEntry`/`GffEntry`, entry-deriving and fast-path bulk inserts), `io.md` (`BedReader`/`GffReader`/`BamReader`/`FastaReader`, `FastaIndex`, `FiletypeDetector`), `registry.md` (`StringRegistry`), and `index.md` (overview, install, `__version__`/`__genogrove_version__`, coordinate-systems table); also dropped the "coming soon" framing for the Python library in `reference/index.md` ([#164](https://github.com/genogrove/docs/pull/164), closes [#148](https://github.com/genogrove/docs/issues/148), closes [#149](https://github.com/genogrove/docs/issues/149), closes [#150](https://github.com/genogrove/docs/issues/150), closes [#151](https://github.com/genogrove/docs/issues/151), closes [#152](https://github.com/genogrove/docs/issues/152), closes [#153](https://github.com/genogrove/docs/issues/153), closes [#154](https://github.com/genogrove/docs/issues/154), closes [#155](https://github.com/genogrove/docs/issues/155), closes [#156](https://github.com/genogrove/docs/issues/156), closes [#157](https://github.com/genogrove/docs/issues/157), closes [#158](https://github.com/genogrove/docs/issues/158), closes [#159](https://github.com/genogrove/docs/issues/159), closes [#160](https://github.com/genogrove/docs/issues/160))

## 2026-05-23

### Changed
- Reverted the const-pointer wording for `query_result::get_keys()` and `flanking_query_result::get_predecessor()`/`get_successor()` in `guide/grove/grove.md` to match the v0.24.5 library revert ([genogrove#436](https://github.com/genogrove/genogrove/pull/436)); dropped the `const_cast` workaround in the `remove_key` example added in [#138](https://github.com/genogrove/docs/pull/138), switched result iteration to `auto*`, and replaced the "const-pointer guarantee" section with a `warning` block noting that `key::set_value()`-corruption discipline is convention-enforced (same risk exists via `insert_data()`), not API-enforced ([#141](https://github.com/genogrove/docs/pull/141), closes [#139](https://github.com/genogrove/docs/issues/139))
- Bumped version to 0.24.5 in `conf.py` and README badge ([ce90e61](https://github.com/genogrove/docs/commit/ce90e61), closes [#140](https://github.com/genogrove/docs/issues/140))

## 2026-05-22

### Added
- Documented the `idx` CLI subcommand (implemented as of genogrove v0.24.3) — usage, options (`-o`, `-k`, `-s`, `-t`), examples, and the BED-only-input note — replacing the previous "not yet implemented" admonition ([#138](https://github.com/genogrove/docs/pull/138), closes [#131](https://github.com/genogrove/docs/issues/131))
- Documented the new `isec -i/--indexfile` option for searching a prebuilt `.gg` index; clarified that `-t` and `-i` are alternatives (at least one required, `-i` takes precedence) and added an index-then-search workflow example ([#138](https://github.com/genogrove/docs/pull/138), closes [#132](https://github.com/genogrove/docs/issues/132))
- Noted that `gio::bed_entry` (with nested `gio::block_info`) is a serializable grove payload in `serialization.md` — `grove<gdt::interval, gio::bed_entry>` can be persisted directly, and the `.gg` files produced by the `idx` CLI subcommand are this form ([#138](https://github.com/genogrove/docs/pull/138), closes [#130](https://github.com/genogrove/docs/issues/130))

### Changed
- Broadened `fasta_index` exception note in `io.md`: all lookup methods (`fetch`, `sequence_name`, `sequence_length`) throw `std::out_of_range` on missing/invalid inputs; `fetch` additionally throws it on invalid regions (`start >= end`, or exceeding htslib's coordinate limit); `std::runtime_error` is reserved for an actual htslib fetch failure ([#138](https://github.com/genogrove/docs/pull/138), closes [#129](https://github.com/genogrove/docs/issues/129))
- Bumped version to 0.24.4 in `conf.py` and README badge ([7f24f69](https://github.com/genogrove/docs/commit/7f24f69), closes [#128](https://github.com/genogrove/docs/issues/128), closes [#133](https://github.com/genogrove/docs/issues/133), closes [#134](https://github.com/genogrove/docs/issues/134))

### Fixed
- Corrected the native grove file extension from `.ggx` to `.gg` in `serialization.md` and `registry.md`, and added the missing built-in key types `numeric` and `kmer` to the `index.md` feature list ([#138](https://github.com/genogrove/docs/pull/138), closes [#136](https://github.com/genogrove/docs/issues/136))
- Corrected installation guide: CMake minimum version is 3.14 (not 3.15) per `CMakeLists.txt`; sanitizer CMake option is `ENABLE_SANITIZER` (singular), not the silently-ignored `ENABLE_SANITIZERS` ([#138](https://github.com/genogrove/docs/pull/138), closes [#137](https://github.com/genogrove/docs/issues/137))
- Suppressed Sphinx's `cpp.duplicate_declaration` warning for C++20 `requires`-clause overloads with identical visible signatures — the v0.24.4 `key<T, void>` default constructor collides with the existing `key<T, D>` default constructor under Breathe ([#138](https://github.com/genogrove/docs/pull/138))

### Issues filed
- [#135](https://github.com/genogrove/docs/issues/135) — `graph.md` examples that feed query-result keys into `add_edge`/`link_if` fail to compile because `query_result::get_keys()` returns `const key*`; closed in favour of upstream library issue [genogrove/genogrove#435](https://github.com/genogrove/genogrove/issues/435) (revert `query_result` to non-const pointers)

## 2026-05-18

### Added
- New "Tagged Singletons" and "Storing Richer Payloads" sections in `registry.md` covering the `Tag` phantom parameter and the new `Payload` parameter + `intern(key, payload)` two-arg overload with first-write-wins semantics ([#127](https://github.com/genogrove/docs/pull/127), closes [#113](https://github.com/genogrove/docs/issues/113), closes [#124](https://github.com/genogrove/docs/issues/124))
- New "Serialization and Deserialization" subsection in `registry.md` documenting the strong exception guarantee, count validation, duplicate-key rejection, and concurrency note for `registry::deserialize` ([#127](https://github.com/genogrove/docs/pull/127), closes [#120](https://github.com/genogrove/docs/issues/120))
- New "Reclaiming removed-key storage (`compact`)" section in `grove.md` covering `compact()` and `key_storage_size()`, pointer-invalidation rules, and external-keys-unaffected guarantee ([#127](https://github.com/genogrove/docs/pull/127), closes [#116](https://github.com/genogrove/docs/issues/116))
- New "Source Stream Must Be Seekable for Concatenated Payloads" section in `serialization.md` for the `grove::deserialize` non-seekable-source error and `stringstream` workaround ([#127](https://github.com/genogrove/docs/pull/127), closes [#119](https://github.com/genogrove/docs/issues/119))
- New "Iterator Equality Contract" section in `io.md` documenting position-aware equality on `file_reader_iterator` ([#127](https://github.com/genogrove/docs/pull/127), closes [#118](https://github.com/genogrove/docs/issues/118))
- Documented `sam_entry::consumes_reference()` and the zero-ref-consuming CIGAR semantics on `start`/`end`; added recommended insertion pattern gated on `consumes_reference()` ([#127](https://github.com/genogrove/docs/pull/127), closes [#117](https://github.com/genogrove/docs/issues/117))

### Changed
- Rewrote `key<>` comparison section: value-only semantics, added `operator<` / `operator>`, fixed the now-incorrect `kd1 == kd3` example, noted that `<=`/`>=` are not auto-generated ([#127](https://github.com/genogrove/docs/pull/127), closes [#122](https://github.com/genogrove/docs/issues/122))
- Documented const-pointer return contract and `key_type_base` concept constraint on `query_result` / `flanking_query_result`; switched query iteration examples to `const auto*` ([#127](https://github.com/genogrove/docs/pull/127), closes [#121](https://github.com/genogrove/docs/issues/121))
- Updated read-only graph_overlay accessor signatures (`has_edge`, `get_edges`, `get_edge_list`, `get_neighbors`, `get_neighbors_if`, `out_degree`) to `const key*`; noted that `serialize()` works on a `const grove&` ([#127](https://github.com/genogrove/docs/pull/127), closes [#115](https://github.com/genogrove/docs/issues/115))
- Tightened `bam_reader` docs: `read_next()` now throws on truncated auxiliary data (not just I/O errors) ([#127](https://github.com/genogrove/docs/pull/127), closes [#114](https://github.com/genogrove/docs/issues/114))
- Marked the CLI `idx` subcommand as "not yet implemented" and removed the examples that would fail at runtime ([#127](https://github.com/genogrove/docs/pull/127), closes [#126](https://github.com/genogrove/docs/issues/126))
- Bumped version to 0.24.1 in `conf.py` and README badge ([#127](https://github.com/genogrove/docs/pull/127), closes [#125](https://github.com/genogrove/docs/issues/125), closes [#123](https://github.com/genogrove/docs/issues/123))

### Issues filed
- [#126](https://github.com/genogrove/docs/issues/126) — `cli.md` documented `idx` subcommand as working, but implementation throws "not yet implemented" (resolved in this release)

## 2026-05-15

### Changed
- Rewrote `registry` guide around the new dedup-on-insert API (`intern()`, `find()`, `registry_value` concept with custom-type `std::hash` example, thread-safety section); dropped the removed mutable `get()` example and updated `register_data()` → `intern()` in the serialization combined-persistence example ([#112](https://github.com/genogrove/docs/pull/112), closes [#108](https://github.com/genogrove/docs/issues/108))
- Bumped version to 0.23.0 in `conf.py` and README badge ([b89d818](https://github.com/genogrove/docs/commit/b89d818), closes [#109](https://github.com/genogrove/docs/issues/109))

### Fixed
- Corrected project license in `source/index.md` and the README badge: MIT → GPL-3.0-or-later, matching upstream `LICENSE` and SPDX headers ([#112](https://github.com/genogrove/docs/pull/112), closes [#110](https://github.com/genogrove/docs/issues/110))
- Fixed `performance.md`: replaced the nonexistent `gst::unsorted` tag with the correct no-tag `insert_data()` overload, and moved graph edges + external keys out of the "Not saved" list since `grove::serialize()` now persists them ([#112](https://github.com/genogrove/docs/pull/112), closes [#111](https://github.com/genogrove/docs/issues/111))

## 2026-05-08

### Added
- Documented `grove::flanking()` predecessor/successor query API and `flanking_query_result`, including the predicate-filtered overload, the interval-vs-scalar selection rule, and a Doxygen reference stub ([#107](https://github.com/genogrove/docs/pull/107), closes [#103](https://github.com/genogrove/docs/issues/103))
- Documented that `bed_reader`/`gff_reader` accept both BGZF and plain gzip transparently via htslib's `bgzf_open()` ([#107](https://github.com/genogrove/docs/pull/107), closes [#104](https://github.com/genogrove/docs/issues/104))
- Documented new zero-record reader behavior: structurally valid but record-less inputs yield an empty iterator instead of throwing; added empty-detection pattern and explicit list of conditions that still raise ([#107](https://github.com/genogrove/docs/pull/107), closes [#105](https://github.com/genogrove/docs/issues/105))

### Changed
- Bumped version to 0.22.0 in `conf.py` and README badge ([#107](https://github.com/genogrove/docs/pull/107), closes [#106](https://github.com/genogrove/docs/issues/106))

## 2026-04-13

### Added
- Documented `grove::remove_key()` with rebalance/root-collapse behaviour and automatic graph edge cleanup ([#102](https://github.com/genogrove/docs/pull/102), closes [#100](https://github.com/genogrove/docs/issues/100))
- Documented bulk edge removal APIs (`remove_edges_from`, `remove_edges_to`, `remove_all_edges`, `remove_edges_if`) in graph manipulation guide ([#102](https://github.com/genogrove/docs/pull/102), closes [#100](https://github.com/genogrove/docs/issues/100))
- Added FASTA/FASTQ I/O section covering streaming `fasta_reader` and indexed random-access `fasta_index`, including GFF→FASTA coordinate example ([#102](https://github.com/genogrove/docs/pull/102), closes [#98](https://github.com/genogrove/docs/issues/98), closes [#99](https://github.com/genogrove/docs/issues/99))
- Added Doxygen directives for `fasta_reader`, `fasta_index`, `fasta_entry`, and `fasta_reader_options` in the C++ I/O reference ([#102](https://github.com/genogrove/docs/pull/102), closes [#99](https://github.com/genogrove/docs/issues/99))

### Changed
- Updated grove constructor docs: minimum order raised from 2 to 3; throws `std::invalid_argument`; dropped removed `fill_factor` parameter and `get_fill_factor`/`set_fill_factor` references ([#102](https://github.com/genogrove/docs/pull/102), closes [#100](https://github.com/genogrove/docs/issues/100), closes [#101](https://github.com/genogrove/docs/issues/101))
- Removed stale `fill_factor` bullet from serialization guide ([#102](https://github.com/genogrove/docs/pull/102), closes [#100](https://github.com/genogrove/docs/issues/100))
- Replaced outdated "BED, GFF/GTF, VCF" feature bullet on the landing page with "BED, GFF/GTF, BAM/SAM, FASTA/FASTQ" ([#102](https://github.com/genogrove/docs/pull/102))
- Bumped version to 0.21.0 in `conf.py` and README badge ([#102](https://github.com/genogrove/docs/pull/102))

### Fixed
- Corrected `fasta_reader` example to use try/catch on `std::runtime_error` instead of a post-loop `get_error_message()` check (reader has no lenient mode; `read_next()` throws on parse/I/O errors) ([#102](https://github.com/genogrove/docs/pull/102))

## 2026-03-30

### Added
- Documented `get_root_nodes()` const-reference return semantics and `set_root_nodes()` privatization in grove guide ([#93](https://github.com/genogrove/docs/pull/93), closes [#85](https://github.com/genogrove/docs/issues/85), closes [#72](https://github.com/genogrove/docs/issues/72), closes [#74](https://github.com/genogrove/docs/issues/74))
- Documented `interval::INVALID_POSITION` and `kmer::BASE_MASK` named constants ([#93](https://github.com/genogrove/docs/pull/93), closes [#87](https://github.com/genogrove/docs/issues/87))
- Documented GTF quoted semicolon handling in attribute values ([#93](https://github.com/genogrove/docs/pull/93), closes [#89](https://github.com/genogrove/docs/issues/89))
- Documented graph overlay edge serialization and breaking format change ([#93](https://github.com/genogrove/docs/pull/93), closes [#92](https://github.com/genogrove/docs/issues/92))

### Changed
- Updated GFF/GTF coordinate semantics to 1-based inclusive (native format); added per-format conversion table in I/O guide and updated all GFF examples ([#93](https://github.com/genogrove/docs/pull/93), closes [#88](https://github.com/genogrove/docs/issues/88))
- Replaced `set_start()`/`set_end()` with `set_range(start, end)` in interval and genomic_coordinate docs; noted `set_strand()` validation ([#93](https://github.com/genogrove/docs/pull/93), closes [#90](https://github.com/genogrove/docs/issues/90))
- Updated bulk insert range concept requirements: `forward_range`+`sized_range` for sorted bulk, `random_access_range`+`sized_range` for unsorted bulk ([#93](https://github.com/genogrove/docs/pull/93), closes [#91](https://github.com/genogrove/docs/issues/91))
- Removed `skip_invalid_records` from `bam_reader_options` documentation ([#93](https://github.com/genogrove/docs/pull/93), closes [#86](https://github.com/genogrove/docs/issues/86))
- Bumped version to 0.19.0 in `conf.py` and README badge ([#97](https://github.com/genogrove/docs/pull/97), closes [#96](https://github.com/genogrove/docs/issues/96))

### Fixed
- Fixed bulk insert examples in `grove.md` and `performance.md` to use single container of pairs instead of non-existent separate-container API ([#97](https://github.com/genogrove/docs/pull/97), closes [#94](https://github.com/genogrove/docs/issues/94))
- Added missing `'*'` wildcard strand to `set_strand()` validation comment in `data_types.md` ([#97](https://github.com/genogrove/docs/pull/97), closes [#95](https://github.com/genogrove/docs/issues/95))

## 2026-03-19

### Added
- Documented node and grove copy/move semantics (non-copyable, move-only) in API reference, grove guide, and serialization guide ([#81](https://github.com/genogrove/docs/pull/81), closes [#71](https://github.com/genogrove/docs/issues/71))

### Changed
- Documented `get_error_message()` contract: reflects most recent record only, cleared each iteration; added Error Message Lifecycle section with correct usage pattern ([#82](https://github.com/genogrove/docs/pull/82), closes [#76](https://github.com/genogrove/docs/issues/76))
- Updated graph guide examples to use `const auto&` for `get_keys()` which now returns by const reference ([#83](https://github.com/genogrove/docs/pull/83), closes [#77](https://github.com/genogrove/docs/issues/77))
- Documented opt-in GTF attribute validation (`validate_gtf` option) with usage examples ([#83](https://github.com/genogrove/docs/pull/83), closes [#78](https://github.com/genogrove/docs/issues/78))
- Bumped version to 0.18.0 in `conf.py` and README badge ([#83](https://github.com/genogrove/docs/pull/83), closes [#79](https://github.com/genogrove/docs/issues/79))

### Fixed
- Fixed wrong parameter types in graph function signatures: `key_type*` → `gdt::key<key_type, data_type>*` in all signature blocks across `graph.md` and `graph_manipulation.md` ([#84](https://github.com/genogrove/docs/pull/84), closes [#80](https://github.com/genogrove/docs/issues/80))
- Renamed `data_registry` → `registry` throughout docs to match library rename; removed stale `index` and `index_registry` API reference sections; updated `registry::get()` to return references instead of pointers ([#81](https://github.com/genogrove/docs/pull/81))

## 2026-03-05

### Changed
- Updated compiler support: GCC 13+, Clang 16+, Apple Clang 15+ ([#60](https://github.com/genogrove/docs/pull/60), closes [#55](https://github.com/genogrove/docs/issues/55), closes [#54](https://github.com/genogrove/docs/issues/54))
- Added try-catch error handling to quick start and all complete examples ([#61](https://github.com/genogrove/docs/pull/61), closes [#38](https://github.com/genogrove/docs/issues/38))
- Updated `aggregate()` to pairwise signature, documented `string_view` adoption and concept constraints ([#62](https://github.com/genogrove/docs/pull/62), closes [#53](https://github.com/genogrove/docs/issues/53), closes [#58](https://github.com/genogrove/docs/issues/58))
- Updated entry structs to use `start`/`end` fields, documented coordinate semantics (readers = half-open, grove = closed) ([#63](https://github.com/genogrove/docs/pull/63), closes [#52](https://github.com/genogrove/docs/issues/52))
- Documented grove constructor `order >= 2` validation, `fill_factor` parameter, and deserialization error handling ([#64](https://github.com/genogrove/docs/pull/64), closes [#56](https://github.com/genogrove/docs/issues/56), closes [#57](https://github.com/genogrove/docs/issues/57), closes [#59](https://github.com/genogrove/docs/issues/59))
- Renamed `overlap()` → `overlaps()` in all code examples and prose; bumped version to 0.17.0; documented zlib compression in serialization; fixed stale compiler versions in `user_guide.md`; added Doxygen directives for `sorted_t`, `bulk_t`, `string_hash`, `key_type_base` ([#70](https://github.com/genogrove/docs/pull/70), closes [#65](https://github.com/genogrove/docs/issues/65), closes [#66](https://github.com/genogrove/docs/issues/66), closes [#67](https://github.com/genogrove/docs/issues/67), closes [#68](https://github.com/genogrove/docs/issues/68), closes [#69](https://github.com/genogrove/docs/issues/69))

## 2026-03-02

### Added
- Documented `bam_reader` header access methods (`get_header()`, `get_reference_names()`) in I/O guide ([#45](https://github.com/genogrove/docs/pull/45), closes [#36](https://github.com/genogrove/docs/issues/36))
- Added missing Doxygen directives for BED support types (`rgb_color`, `thick_info`, `block_info`), BAM/SAM types (`sam_flags`, `sam_tag`), and serialization utilities (`serialization_traits`, `serializer`) ([#46](https://github.com/genogrove/docs/pull/46), closes [#37](https://github.com/genogrove/docs/issues/37))
- Added `bed_reader_options` and `gff_reader_options` Doxygen directives; consolidated all reader options into a dedicated API reference section ([#50](https://github.com/genogrove/docs/pull/50))

### Fixed
- Fixed code examples discarding `[[nodiscard]]` return values from `data_registry::deserialize()`, `size()`, `empty()`, and `contains()` ([#47](https://github.com/genogrove/docs/pull/47), closes [#40](https://github.com/genogrove/docs/issues/40))

### Changed
- Updated `intersect()` examples to pass temporaries directly, reflecting the `const key_type&` parameter change ([#48](https://github.com/genogrove/docs/pull/48), closes [#41](https://github.com/genogrove/docs/issues/41))
- Documented `constexpr` support for data type constructors, operators, and overlap detection with compile-time example ([#49](https://github.com/genogrove/docs/pull/49), closes [#42](https://github.com/genogrove/docs/issues/42))
- Rewrote Error Handling section: readers now throw `std::runtime_error` by default; documented lenient mode via options structs; added try-catch to main reader examples ([#50](https://github.com/genogrove/docs/pull/50), closes [#43](https://github.com/genogrove/docs/issues/43))
- Bumped version to 0.16.0 in `conf.py` and README badge ([#51](https://github.com/genogrove/docs/pull/51), closes [#44](https://github.com/genogrove/docs/issues/44))

## 2026-02-27

### Added
- Added dedicated grove loading guide (`loading_data.md`) with BED (incremental + bulk), GFF/GTF, and BAM/SAM examples ([#34](https://github.com/genogrove/docs/pull/34), closes [#23](https://github.com/genogrove/docs/issues/23), closes [#24](https://github.com/genogrove/docs/issues/24), closes [#25](https://github.com/genogrove/docs/issues/25))
- Documented error handling pattern for file readers with `get_error_message()` post-loop check ([#35](https://github.com/genogrove/docs/pull/35), closes [#18](https://github.com/genogrove/docs/issues/18))

### Issues filed
- [genogrove/genogrove#110](https://github.com/genogrove/genogrove/issues/110) — Throw on parse errors instead of silently stopping iteration

### Changed
- Moved grove loading examples from I/O guide to grove section ([#34](https://github.com/genogrove/docs/pull/34))

## 2026-02-26

### Added
- Added serialization guide covering grove persistence, combined `data_registry` serialization, and custom type serialization ([#30](https://github.com/genogrove/docs/pull/30), partially addresses [#15](https://github.com/genogrove/docs/issues/15))
- Documented mixed BED format support (BED3/BED6/BED12) in I/O guide ([#31](https://github.com/genogrove/docs/pull/31), closes [#16](https://github.com/genogrove/docs/issues/16))
- Documented non-copyable/movable ownership pattern for file readers in I/O guide ([#32](https://github.com/genogrove/docs/pull/32), closes [#17](https://github.com/genogrove/docs/issues/17))
- Added missing Doxygen reference directives for I/O entry types (`bed_entry`, `gff_entry`, `sam_entry`), BAM/SAM types (`alignment_flags`, `bam_reader_options`, `cigar_element`, `mate_info`), enums (`filetype`, `compression_type`, `gff_format`, `cigar_op`), and data types (`numeric`, `kmer`, `data_registry`, `index`, `index_registry`) ([#27](https://github.com/genogrove/docs/pull/27), closes [#12](https://github.com/genogrove/docs/issues/12))

### Fixed
- Fixed wrong API signatures for `get_edges()`, `get_edge_list()`, and `remove_edge()` in `graph_manipulation.md` ([#33](https://github.com/genogrove/docs/pull/33), closes [#20](https://github.com/genogrove/docs/issues/20))
- Fixed orphaned guide pages not reachable from sidebar navigation ([#28](https://github.com/genogrove/docs/pull/28), closes [#13](https://github.com/genogrove/docs/issues/13))
- Removed stale `sphinx-immaterial` dependency from `requirements.txt` ([#29](https://github.com/genogrove/docs/pull/29), closes [#14](https://github.com/genogrove/docs/issues/14))

### Changed
- Extended GFF/GTF section in I/O guide with precise field types, format detection explanation, coordinate conversion note, attribute access patterns with fallback behavior, GTF validation rules, and convenience methods ([#26](https://github.com/genogrove/docs/pull/26))
- Removed internal base classes (`file_reader_base`, `file_reader`) from I/O API reference ([#27](https://github.com/genogrove/docs/pull/27))
- Organized I/O API reference into Readers, Entry Types, BAM/SAM Types, and Enums sections ([#27](https://github.com/genogrove/docs/pull/27))
- Expanded sidebar navigation by default (`show_nav_level: 2`) and added cross-references to Linking Keys and Graph Manipulation on the grove page ([#28](https://github.com/genogrove/docs/pull/28))

### Issues filed
- [#24](https://github.com/genogrove/docs/issues/24) — Add GFF/GTF grove loading example to grove user guide
- [#25](https://github.com/genogrove/docs/issues/25) — Add BAM/SAM grove loading example to grove user guide

## 2026-02-25

### Added
- Added BAM/SAM/CRAM reader section to I/O guide with iterator usage, filtering options, `sam_entry` fields, CIGAR operations, tag access, convenience methods, and grove loading example ([#22](https://github.com/genogrove/docs/pull/22), closes [#11](https://github.com/genogrove/docs/issues/11))
- Added `CLAUDE.md` with project instructions ([#22](https://github.com/genogrove/docs/pull/22))

### Fixed
- Fixed broken code examples across guide pages: private member access, wrong `std::optional` patterns, incorrect BED field descriptions, wrong `insert_data_bulk` API, wrong `size()`/`vertex_count()` calls ([#21](https://github.com/genogrove/docs/pull/21), closes [#10](https://github.com/genogrove/docs/issues/10))
- Fixed version mismatch: updated `conf.py` and `README.md` badge to v0.15.2 ([#22](https://github.com/genogrove/docs/pull/22))

### Changed
- Updated `repos/genogrove` to v0.15.2 (was v0.13.1)

### Issues filed
- [#20](https://github.com/genogrove/docs/issues/20) — Wrong API signatures in `graph_manipulation.md` (`get_edge_list`, `get_edges`, `remove_edge`)
- [#10 comment](https://github.com/genogrove/docs/issues/10#issuecomment-3963767836) — Additional broken examples in `graph_manipulation.md`, `graph.md`, `io.md`, `examples.md`