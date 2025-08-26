#include "genogrove/structure/grove/key.hpp"

namespace genogrove::structure {
    template<typename key_type>
    key<key_type>::key() : value(key_type()), data(nullptr),
    single_link(nullptr), multi_link(std::vector<key*>()) {}

    template<typename key_type>
    key<key_type>::key(key_type obj) : value(obj), data(nullptr),
    single_link(nullptr), multi_link(std::vector<key*>()) {}

    // operator overloading
    template<typename key_type>
    bool key<key_type>::operator<(const key_type &other) const {
    }

    template<typename key_type>
    void key<key_type>::serialize(std::ostream& os) const {
        value.serialize(os);
        bool has_data = (data != nullptr); // check if there is data to serialize
        os.write(reinterpret_cast<const char*>(&has_data), sizeof(has_data));

        if(has_data) {
            std::string type_name = data->get_type_name();
            size_t type_name_length = type_name.size();
            os.write(reinterpret_cast<const char*>(&type_name_length), sizeof(size_t));
            os.write(type_name.c_str(), type_name_length);

            data->serialize(os);

            bool has_single_link = (single_link != nullptr);
            os.write(reinterpret_cast<const char*>(&has_single_link), sizeof(has_single_link));
            if(has_single_link) {
                single_link->serialize(os);
            }

            size_t multi_link_size = multi_link.size();
            os.write(reinterpret_cast<const char*>(&multi_link_size), sizeof(multi_link_size));
            for(auto& link : multi_link) {
                link->serialize(os);
            }
        }
    }

    template<typename key_type>
    key<key_type> key<key_type>::deserialize(std::istream& is) {
        key_type obj = key_type::deserialize(is); // serialize the key object
        key<key_type> key1(obj); // create a new key object (with the key object/value)

        bool has_data;
        is.read(reinterpret_cast<char*>(&has_data), sizeof(has_data));
        if(has_data) {
            size_t type_name_length;
            is.read(reinterpret_cast<char*>(&type_name_length), sizeof(type_name_length));
            std::string type_name(type_name_length, '\0');
            is.read(&type_name[0], type_name_length);

            // deserialize the data object
            key1.data = ggt::type_registry::create(type_name);
        }





    }
}