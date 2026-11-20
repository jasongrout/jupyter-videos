"""Fetch every PR in a milestone (all states) and the given extra PRs, with milestone events."""
import json, subprocess, sys
out, milestone = sys.argv[1], sys.argv[2]
extra = [int(x) for x in sys.argv[3:]]
FIELDS = '''number title url state mergedAt isDraft reviewDecision baseRefName
  author { login }
  milestone { title }
  labels(first: 30) { nodes { name } }
  timelineItems(itemTypes: [MILESTONED_EVENT, DEMILESTONED_EVENT], last: 20) {
    nodes {
      __typename
      ... on MilestonedEvent { createdAt milestoneTitle actor { login } }
      ... on DemilestonedEvent { createdAt milestoneTitle actor { login } }
    }
  }'''
def gql(q):
    r = subprocess.run(['gh', 'api', 'graphql', '-f', f'query={q}'], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    return json.loads(r.stdout)['data']
result, cursor = {}, None
while True:
    after = f', after: "{cursor}"' if cursor else ''
    q = ('query { search(query: "repo:jupyterlab/jupyterlab is:pr milestone:%s", type: ISSUE, first: 100%s) {'
         ' pageInfo { hasNextPage endCursor } nodes { ... on PullRequest { %s } } } }' % (milestone, after, FIELDS))
    d = gql(q)['search']
    for n in d['nodes']:
        result[n['number']] = n
    if not d['pageInfo']['hasNextPage']:
        break
    cursor = d['pageInfo']['endCursor']
missing = [n for n in extra if n not in result]
for i in range(0, len(missing), 30):
    chunk = missing[i:i + 30]
    q = 'query { repository(owner: "jupyterlab", name: "jupyterlab") {\n'
    for n in chunk:
        q += f'  p{n}: pullRequest(number: {n}) {{ {FIELDS} }}\n'
    q += '} }'
    for v in gql(q)['repository'].values():
        result[v['number']] = v
json.dump(result, open(out, 'w'), indent=1)
print(len(result), 'PRs;', len(missing), 'fetched outside the milestone search')
