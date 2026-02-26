# Changelog

All notable changes to the genogrove documentation project will be documented in this file.

## 2026-02-25

### Fixed
- Fixed broken code examples across guide pages: private member access, wrong `std::optional` patterns, incorrect BED field descriptions, wrong `insert_data_bulk` API, wrong `size()`/`vertex_count()` calls ([#21](https://github.com/genogrove/docs/pull/21), closes [#10](https://github.com/genogrove/docs/issues/10))

### Changed
- Updated `repos/genogrove` to v0.15.2 (was v0.13.1)

### Issues filed
- [#20](https://github.com/genogrove/docs/issues/20) — Wrong API signatures in `graph_manipulation.md` (`get_edge_list`, `get_edges`, `remove_edge`)
- [#10 comment](https://github.com/genogrove/docs/issues/10#issuecomment-3963767836) — Additional broken examples in `graph_manipulation.md`, `graph.md`, `io.md`, `examples.md`