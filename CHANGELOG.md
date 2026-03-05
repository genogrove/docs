# Changelog

All notable changes to the genogrove documentation project will be documented in this file.

## 2026-03-05

### Changed
- Updated compiler support: GCC 13+, Clang 16+, Apple Clang 15+ ([#60](https://github.com/genogrove/docs/pull/60), closes [#55](https://github.com/genogrove/docs/issues/55), closes [#54](https://github.com/genogrove/docs/issues/54))
- Added try-catch error handling to quick start and all complete examples ([#61](https://github.com/genogrove/docs/pull/61), closes [#38](https://github.com/genogrove/docs/issues/38))

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