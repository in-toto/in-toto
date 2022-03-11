"""
ITE-4:
Github has many abstract entities such as Pull Requests and Commits. This code
helps provide attestationns about these artifacts by getting the hash from the
Github entities.
"""

from urllib3.util import Url
from urllib3 import PoolManager
import json
import hashlib


def _get_resolvable_url(generic_uri):
  """
  Convert a generic uri to an API URL that represent a Github entity

  We should consider what generic_url looks like. Here is a draft idea of what
  it should look like.
    github:org/repo:pr:number
    github:org/repo:commit:id

  Args:
    generic_uri: a generic_uri representing a GitHub entity

  Returns:
    an API URL representing a GitHub entity
  """
  uri_split = generic_uri.split(':')

  if uri_split[2] == 'pr':
    path = 'repos/{}/pulls/{}'.format(uri_split[1], uri_split[3])
  elif uri_split[2] == 'commit':
    path = 'repos/{}/commits/{}'.format(uri_split[1], uri_split[3])

  resolvable_url = Url(scheme='https', host='api.github.com', path=path)

  return resolvable_url


def _hash_review_representation(review):
  '''
  Capture representative fields in a review and return its hash. We may want to 
  be able to retrieve each status of the comment, such as CHANGES_REQUESTED and 
  APPROVED. We may also want to know who reviewed the PR and approved it.

  some possible policies of reviews:
  - Reviews should be done by authorized personnel (such as the memeber of the 
    organization)
  - The code should not be pushed unless it has an APPROVED state

  We can incorporate ITE-4 there for review attestations. This could be a part
  of the statement's subject.

  Args:
    Review response data from Github API calls

  Returns:
    A hash that represent a Github review
  '''
  review_representation = {}
  review_representation['id'] = review['id']
  review_representation['author'] = review['user']['login']
  review_representation['author_association'] = review['author_association']
  review_representation['state'] = review['state']

  dhash = hashlib.md5()
  encoded = json.dumps(review_representation, sort_keys=True).encode()
  dhash.update(encoded)
  hash_artifact = dhash.hexdigest()

  return hash_artifact


def get_hashable_representation(generic_uri):
  """
  Obtain a dict that helps provide attestationns about a GitHub entity

  Args:
    generic_uri: a generic_uri representing a GitHub entity

  Returns:
    A dictionary that represent a Github enitty
  """
  resolvable_url = _get_resolvable_url(generic_uri)
  github_entity_type = generic_uri.split(':')[2]

  http = PoolManager()

  response = http.request('GET', str(resolvable_url),
      headers={'User-Agent': 'in-toto Reference Implementation'})
  response_data = json.loads(response.data)

  representation_object = {}
  representation_object['type'] = github_entity_type

  if github_entity_type == 'commit':
    representation_object['commit_id'] = response_data['sha']
    representation_object['author'] = response_data['author']['login']
    representation_object['tree'] = response_data['tree']['sha']

    return representation_object

  elif github_entity_type == 'pr':
    representation_object['user'] = response_data['user']['login']
    representation_object['head'] = response_data['head']['label']
    representation_object['base'] = response_data['base']['label']

    representation_object['commits'] = []
    commits_url = response_data['commits_url']
    commits_api_response = http.request('GET', str(commits_url),
        headers={'User-Agent': 'in-toto Reference Implementation'})
    commits_response_data = json.loads(commits_api_response.data)
    for commit in commits_response_data:
      representation_object['commits'].append(commit['sha'])

    representation_object['reviews'] = []
    review_url = str(resolvable_url) + '/reviews'
    review_api_response = http.request('GET', review_url,
        headers={'User-Agent': 'in-toto Reference Implementation'})
    review_response_data = json.loads(review_api_response.data)
    for review in review_response_data:
      representation_object['reviews'].append(
          _hash_review_representation(review))

def hash_artifacts(generic_url):
    """
    Obtain a hash from a GitHub abstract entity

    Args:
      generic_uri: a generic_uri representing a GitHub entity

    Returns:
      A hash that represent a Github enitty
    """
    representation_object = get_hashable_representation(generic_url)

    dhash = hashlib.md5()
    encoded = json.dumps(representation_object, sort_keys=True).encode()
    dhash.update(encoded)

    hash_artifacts = dhash.hexdigest()
    return hash_artifacts
