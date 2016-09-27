
class Signable(object):
    """ Objects of signable can sign themselves, i.e. their __repr__ 
    without the signatures property, and store the signature to a signature
    property.
    """

    signatures = attr.ib(False, repr=False)

    def sign(self, key):
        """ Signs the JSON repr of itself (without the signatures property) and 
        adds the signatures to its signature properties. """
