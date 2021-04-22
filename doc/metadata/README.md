Verify in-toto's supply chain with in-toto
===========================================

**Overview**  
This document describes how to use in-toto to verify the software supply chains for the PyPi source of in-toto. In this documentation, We are using in-toto v1.0.1 as an example.

The basic supply chains are laid out in "in_toto_sdist.layout" and consist of two steps:

1. "git-tag" -- Tag the release.
2. "create-sdist" -- Creates source distribution (.tar.gz) using the same materials from (1).

To create link files, we may want to start with a clean clone or using ```--exclude``` to make sure that we don't record any additional files (such as egg files and pyc files) as materials.

We will use the following commands to create the link files:

1. ```in-toto-run --step-name git-tag --materials . --key keys/bob -- git tag --sign v1.0.1 -m "v1.0.1"```
2. ```in-toto-run --step-name create-sdist --materials . --products in-toto.1.0.1.tar.gz --key keys/bob -- python setup.py sdist```

The example links are laid out in "git-tag.776a00e2.link" and "create-sdist.776a00e2.link". The key for signing the steps is the bob's key from the in-toto demo: https://github.com/in-toto/demo/tree/master/functionary_bob

To verify the supply chain, we can run the in-toto verify command:  
```in-toto-verify -l in-toto-sdist-signed.layout -k keys/alice.pub -v```

*The "in-toto-sdist-signed" layout is signed with the alice's (owner) key, which is also from the in-toto demo. 

**Notes/Discussion**  

- For the bootstrapping/chicken-egg situation, we assume that the user already has an older version of the in-toto locally.
- For the first step, we want to explicitly allow all the files to make sure we tag all the materials files to sign.
- Since we only tag a release in the first step, no files are changed and there will be no products. So we only need to add the "DISALLOW *" rule for the expected products.
- For the second step, we match all the files with the materials in the first step, because we don't have products in the first step.

**Todos**

- Combine the "Creates binary distribution (.whl)" step with the second step.
- We need to decide where to put the layout file. One idea is to attach the layout file to each release, but we probably want to make it available somewhere other than Github.
