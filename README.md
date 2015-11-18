# Setup

This backend needs at least Duplicity 0.7+. If you are still using a 0.6 variant, please
see the [first comment in issue #1](https://github.com/breunigs/duplicity-acdcli/issues/1#issue-117038264)
on how to make it compatible with the old version.

```
# Linux
cp amazonclouddrivebackend.py /usr/lib/python2.7/dist-packages/duplicity/backends/

# MacOS X
cp amazonclouddrivebackend.py /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/duplicity/backends


# Setup acd_cli as per yadayada’s setup guide
acd_cli init
cp ~/downloads/oauth_data ~/.cache/acd_cli

# Manually create the backup target directory, e.g.:
acd_cli mkdir --parents /backup/my_new_backup
```

# Usage
```
duplicity source_path acd:///backup/my_new_backup
```

It probably doesn’t support Windows because it hard-links files, which is not supported on that platform. If there are any Windows users, please drop me a note.

# License

Same as Duplicity
