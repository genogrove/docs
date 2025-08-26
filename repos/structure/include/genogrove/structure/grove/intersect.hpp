#ifndef GENOGROVE_STRUCTURE_INTERSECT_HPP
#define GENOGROVE_STRUCTURE_INTERSECT_HPP

#include <genogrove/data_type/query_result.hpp>

namespace ggt = genogrove::data_type;

namespace genogrove::structure::grove {
    template<typename query_type>
    ggt::query_result<query_type> intersect(query_type& query) {
        ggt::query_result<query_type> result{query};

    }
}

#endif //GENOGROVE_STRUCTURE_INTERSECT_HPP
