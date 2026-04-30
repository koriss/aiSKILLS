
# v8 Identity + Package Audit

## Problems observed in v7 examples

- HTML was delivered without proof package.
- Reports could say v7-proof without `completion-proof.json`.
- Person reports included social profiles without identity-resolution table.
- Sources were sometimes listed as names/groups rather than full URL tables.
- Global verification claims could be stronger than claims registry support.

## v8 fixes

- final delivery requires `research-package.zip`;
- HTML must include full clickable source URLs;
- HTML must embed completion proof and package manifest JSON;
- person research requires identity-resolution artifacts;
- social profiles cannot support claims without confirmed/probable identity;
- name-only matches cannot support claims;
- privacy gate added for person research;
- validators added for package, identity, source links, global overclaiming, and semantic tables.
