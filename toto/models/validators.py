
def validate_materials(self, Attribute, materials):

    for material in materials:
        validate_individual_product(self, material)

def validate_products(self, Attribute, products):
    return validate_materials(self, Attribute, products)


def validate_match_operation(self, keywords):

    MATERIAL_OR_PRODUCT = {'PRODUCT', 'MATERIAL'}

    if not isinstance(keywords, list):
        raise TypeError("this matching rule is not a list")

    if len(keywords) != 5:
        raise TypeError("Wrong operation format, should be: "
                        "MATCH (MATERIAL/PRODUCT) <target> FROM <step>.\n\t"
                        "Got: {}".format(" ".join(keywords)))

    operation, material_or_product, target, from_keyword, step = keywords

    if operation != "MATCH":
        raise TypeError("Wrong operation to verify! {}".format(operation))

    if from_keyword != "FROM":
        raise TypeError("FROM should come before step")

    if material_or_product not in MATERIAL_OR_PRODUCT:
        raise TypeError("Wrong target! Target should be "
                        "either MATERIAL or PRODUCT")

def validate_generic_operation(self, keywords):

    VALID_OPERATIONS = {'CREATE', 'MODIFY', 'DROP',}

    if not isinstance(keywords, list):
        raise TypeError("this matching rule is not a list")

    if len(keywords) != 2: 
        raise TypeError("Wrong operation format, should be: "
                        "{} <target>", keywords[0])

    operation, material_or_product = keywords

    if operation not in VALID_OPERATIONS:
        raise TypeError("Wrong operation to verify! {}".format(operation))

def validate_individual_product(self, keywords):

    OPERATION_KEYWORDS = {'MATCH': validate_match_operation,
            'CREATE': validate_generic_operation, 
            'MODIFY': validate_generic_operation,
            'DROP': validate_generic_operation
            }

    if not isinstance(keywords, list):
        raise TypeError("Product and Material matchers should be a list!")

    operation = keywords[0]
    if operation not in OPERATION_KEYWORDS:
        raise TypeError("error in {}.\n\t"
                        "material should be one of "
                        "{}".format(product,
                                    OPERATION_KEYWORDS.keys()))
    return OPERATION_KEYWORDS[operation](self, keywords)

