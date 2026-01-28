# Data Registry

The `data_registry` is a singleton registry for storing shared metadata by ID, reducing memory usage when many grove entries share the same metadata (e.g., sample information, experiment details):

```cpp
#include <genogrove/data_type/data_registry.hpp>
#include <iostream>
#include <sstream>
#include <string>

namespace gdt = genogrove::data_type;

struct SampleInfo {
    std::string name;
    std::string tissue;
    int replicate;
};

int main() {
    // 1. Get the singleton registry for SampleInfo
    auto& registry = gdt::data_registry<SampleInfo>::instance();

    // 2. Register data and get an ID
    uint32_t id1 = registry.register_data(SampleInfo{"sample1", "liver", 1});
    uint32_t id2 = registry.register_data(SampleInfo{"sample2", "kidney", 1});

    // 3. Check registry state
    registry.size();      // 2
    registry.empty();     // false
    registry.contains(id1);  // true
    registry.contains(999);  // false

    // 4. Retrieve data by ID (returns pointer, nullptr if invalid)
    const SampleInfo* info = registry.get(id1);
    if (info) {
        std::cout << info->name << "\n";  // "sample1"
    }

    // 5. Mutable access
    SampleInfo* mutable_info = registry.get(id2);
    if (mutable_info) {
        mutable_info->replicate = 2;  // modify in place
    }

    // 6. Use with grove - store lightweight ID instead of full struct
    // grove<interval, uint32_t> g;
    // g.insert("chr1", interval{100, 200}, id1);

    // 7. Serialization
    std::ostringstream oss(std::ios::binary);
    registry.serialize(oss);

    // 8. Deserialization (clears and repopulates the singleton)
    std::istringstream iss(oss.str(), std::ios::binary);
    auto& restored = gdt::data_registry<SampleInfo>::deserialize(iss);

    // 9. Clear registry (invalidates all IDs - use with caution)
    registry.clear();
    // Or via static method:
    gdt::data_registry<SampleInfo>::reset();

    return 0;
}
```

**Data Registry Features:**

- `instance()`: Get the singleton registry for a given type
- `register_data(data)`: Store data and return its ID (no deduplication)
- `get(id)`: Retrieve data by ID (returns pointer, `nullptr` if invalid)
- `contains(id)`: Check if an ID is valid
- `size()`, `empty()`: Query registry state
- `clear()`, `reset()`: Clear all data (invalidates all IDs)
- `serialize(os)`, `deserialize(is)`: Persist and restore registry data
- `null_id`: Sentinel value representing an invalid/unset ID

Each type `T` gets its own independent singleton registry. The `index_registry` similarly manages index identifiers (e.g., chromosome names) used by the grove.
