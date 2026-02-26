# Changelog

All notable changes to the genogrove documentation project will be documented in this file.

## 2026-02-26

### Changed
- Extended GFF/GTF section in I/O guide with precise field types, format detection explanation, coordinate conversion note, attribute access patterns with fallback behavior, GTF validation rules, and convenience methods ([#26](https://github.com/genogrove/docs/pull/26))

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