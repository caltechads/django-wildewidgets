#!/bin/bash

if test $(git rev-parse --abbrev-ref HEAD) = "main"; then
    if test -z "$(git status --untracked-files=no --porcelain)"; then
        MSG="$(git log -1 --pretty=%B)"
        echo "$MSG" | grep "Bump version"
        if test $? -eq 0; then
            VERSION=$(echo "$MSG" | awk -F→ '{print $2}')
            echo "---------------------------------------------------"
            echo "Releasing version ${VERSION} ..."
            echo "---------------------------------------------------"
            echo
            echo
            echo "Pushing main to origin ..."
            git push --tags origin main
            echo "Uploading to PyPI ..."
            twine upload dist/*
        else
            echo "Last commit was not a bumpversion; aborting."
            echo "Last commit message: ${MSG}"
        fi
    else
        git status
        echo
        echo
        echo "------------------------------------------------------"
        echo "You have uncommitted changes; aborting."
        echo "------------------------------------------------------"
    fi
else
    echo "You're not on main; aborting."
fi
