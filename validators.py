def validate_materials(self, Attribute, materials):
    # TODO: fixme
    pass

def validiate_products(self, Attribute, products):
    return validate_materials(self, Attribute, products)

def validate_individual_product(product):

    OPERATION_KEYWORDS = {'match', 'create', 'update', 'pin'}

    keywords = product.split(" ")
    operation = keywords[-1]
    if operation not in OPERATION_KEYWORDS:
        raise TypeError("material should be one of "
                        "{}".format(OPERATION_KEYWORDS))

def validate_match_operation(self, keywords):

    try: 
        operation, target, _, step, material_or_product = keywords
    except:
        raise TypeError("Wrong operation format, should be: "
                        "match <target> from <step> (material/product)")
    if operation != "match":
        raise TypeError("Wrong operation to verify! {}".operation)
