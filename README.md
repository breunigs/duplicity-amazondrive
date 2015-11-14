# Setup

```
cp amazonclouddrivebackend.py /usr/lib/python2.7/dist-packages/duplicity/backends/

# Setup acd_cli as per yadayada’s setup guide
acd_cli init
cp ~/downloads/oauth_data ~/.cache/acd_cli

# Manually create the backup target directory, e.g.:
acd_cli --parents /backup/my_new_backup
```

# Usage
```
duplicity source_path acd:///backup/my_new_backup
```

It probably doesn’t support Windows because it hard-links files, which is not supported on that platform. If there are any Windows users, please drop me a note.

# License

Same as Duplicity
