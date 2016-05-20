
## Setup

This backend needs at least Duplicity 0.7+.

```
# Linux
cp amazonclouddrivebackend.py /usr/lib/python2.7/dist-packages/duplicity/backends/

# MacOS X
cp amazonclouddrivebackend.py /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/duplicity/backends
```

On first usage you will need to open an URL in a browser and copy the resulting URL back into the tool to enable oauth access. The data will be stored in `~/.duplicity_acd_oauthtoken.json`.


## Usage
```
duplicity source_path acd:///backup/my_new_backup
```

# License

Same as Duplicity
