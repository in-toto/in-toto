"""
<Program Name>
  exceptions.py

<Author>
  Santiago Torres-Arias <santiago@nyu.edu>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Dec 8, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Define Exceptions used in the gpg package. Following the practice from
  securesystemslib the names chosen for exception classes should end in
  'Error' (except where there is a good reason not to).

"""
class PacketParsingError(Exception):
  pass

class KeyNotFoundError(Exception):
  pass

class PacketVersionNotSupportedError(Exception):
  pass

class SignatureAlgorithmNotSupportedError(Exception):
  pass
