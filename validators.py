def validate_materials(self, Attribute, materials):

    for material in materials:
        validate_individual_product(self, material)

def validate_products(self, Attribute, products):
    return validate_materials(self, Attribute, products)


def validate_match_operation(self, keywords):

    MATERIAL_OR_PRODUCT = {'product', 'material'}

    if not isinstance(keywords, list):
        raise TypeError("this matching rule is not a list")

    if len(keywords) != 5:
        raise TypeError("Wrong operation format, should be: "
                        "match <target> from <step> (material/product).\n\t"
                        "Got: {}".format(" ".join(keywords)))

    operation, material_or_product, target, _, step = keywords

    if operation != "match":
        raise TypeError("Wrong operation to verify! {}".format(operation))

    if material_or_product not in MATERIAL_OR_PRODUCT:
        raise TypeError("Wrong target! Target should be "
                        "either material or product")

def validate_generic_operation(self, keywords):

    VALID_OPERATIONS = {'create', 'update', 'drop', 'pin'}

    if not isinstance(keywords, list):
        raise TypeError("this matching rule is not a list")

    if len(keywords) != 2: 
        raise TypeError("Wrong operation format, should be: "
                        "{} <target>", keywords[0])

    operation, material_or_product = keywords

    if operation not in VALID_OPERATIONS:
        raise TypeError("Wrong operation to verify! {}".format(operation))

def validate_individual_product(self, product):

    OPERATION_KEYWORDS = {'match': validate_match_operation,
            'create': validate_generic_operation, 
            'update': validate_generic_operation,
            'pin': validate_generic_operation,
            'drop': validate_generic_operation
            }

    keywords = product.split(" ")
    operation = keywords[0]
    if operation not in OPERATION_KEYWORDS:
        raise TypeError("error in {}.\n\t"
                        "material should be one of "
                        "{}".format(product,
                                    OPERATION_KEYWORDS.keys()))
    return OPERATION_KEYWORDS[operation](self, keywords)

