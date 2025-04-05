# Host Files Directory

This directory is mounted into the Docker container at `/host-files`. 

## Pre-built Extension Files

You can place a pre-built extension zip file in this directory to have it used by the Docker container instead of rebuilding it.

### Expected filename:
- `gnosis-wraith-extension-{version}.zip` 

Where `{version}` matches the version set in the Dockerfile (currently 1.0.5).

For example:
- `gnosis-wraith-extension-1.0.5.zip`

If this file exists here, the Docker build will use it instead of rebuilding the extension zip from scratch.