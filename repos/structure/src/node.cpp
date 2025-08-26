#include "genogrove/structure/grove/node.hpp"

namespace genogrove::structure {
    template<typename key_type>
    node<key_type>::node(int order) : order(order), keys{}, children{}, parent{nullptr}, next{nullptr}, is_leaf{false} {}

    template<typename key_type>
    void node<key_type>::add_child(node<key_type> *child, int index) {
        this->children.insert(this->children.begin() + index, child);
    }

    template<typename key_type>
    node<key_type>* node<key_type>::get_child(int index) { return this->children[index]; }
}



