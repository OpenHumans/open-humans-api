# How to contribute
![awesome-dog](https://am24.akamaized.net/tms/cnt/uploads/2014/09/dog-youre-awesome.gif)

First of all: You are awesome for wanting to contribute to this project.
Thank you so much for this! 🎉 🍾 😍.
Making it easy for people to integrate the *Open Humans* API into their own
projects is central to our mission.

The easiest way to contribute to this is by [opening issues](https://github.com/OpenHumans/open-humans-api/issues)
of things you have noticed. Please check whether a similar issue already exists
before opening a new one.

## Contributing code

### Install your development environment
If you want to contribute code you should install `open-humans-api` in the editable mode.

The easiest workflow to set up your development environment is the following.

1. Clone this repository into your own *GitHub* account. Then run the following:

```
git clone https://github.com/$YOUR_USER_NAME/open-humans-api.git
cd open-humans-api
pip install -e .
```

This will install the whole package from the cloned repository in editable mode.
If you want to run tests and style checks locally you should also install
the required development packages. From your repository you can do so by running
`pip install -r dev-requirements.txt`. This will install `py.test` and `flake8`.

### Submitting a pull request
If you have written some code that you would like us to merge into `OpenHumans/open-humans-api`
[you can start a pull request](https://github.com/OpenHumans/open-humans-api/pulls) (PR).
Some guidelines for these:
- You should submit PRs from your own repository, ideally from a new feature-branch.
To switch to one you can run `git checkout -b your_branch_name`. Do your edits,
commit them, push them to your fork and then you can make a pull request to us.
- If you are still working on a pull request please prefix the name
of the pull request with `WIP` or `[WIP]` to state that it's a *Work In Progress*.
- Once you think your pull request is ready to be merged edit the title and replace
`[WIP]` with `[MRG]`.
- We are using some continuous integration services to automatically evaluate all
pull requests:
  - `TravisCI` will run all existing tests over each commit to see whether things have accidentally broken. Your pull request can only be merged if all tests pass
  - `HoundCI` runs `flake8` to identify whether your new code breaks the style guide. It will leave comments on each line that does so. Please respond to all the comments `Hound` makes, otherwise your PR can not be merged.
  - Lastly, `CodeClimate` will evaluate whether the addition of new code will decrease the overall test coverage. If your code decreases the test coverage it also can't be merged. This means: New functionalities should come with tests that show that they work.

### What to contribute

#### Fixing existing problems
You [read through our issues or created your own one](https://github.com/OpenHumans/open-humans-api/issues) and you happen to know the solution to it? And even better, you want to contribute the solution? We are [happy to accept your pull requests](https://github.com/OpenHumans/open-humans-api/pulls). Ideally pull requests should just tackle a single issue at a time and come with a description of what will be fixed and how.

#### Contributing new features.
You have an idea for a new feature or an extension of existing features? Maybe open an issue first so that we can all discuss whether it's a good idea to add it!

#### Contributing documentation.
Software is only as good as its documentation. If you see that our documentation is out of date, ambiguous, or just plain wrong: Please improve it and we'll happily merge it!

---
Thanks again for your interest in contributing to the `open-humans-api` client for Python! We appreciate it a lot! 🎉 🍾 😍
