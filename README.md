# Now shipped with duplicity!

If your duplicity version is **newer than 0.7.07**, then you should use the ACD backend shipped with duplicity.

### Update Guide:
You need to switch your backends from `acd:///some_backup_folder/` to `acd+acdcli:///some_backup_folder/`. The two backends are compatible, so you can switch between them if problems arise. If you are sure the shipped variant works for you, you should delete the old `amazonclouddrivebackend.py`.

## Setup

This backend needs at least Duplicity 0.7+. Older versions are incompatible and will not function properly.

```
# Is it higher than 0.7.07? Then use the bundled "acd+acdli" backend
duplicity --version

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

## Usage
```
duplicity source_path acd:///backup/my_new_backup
```

# License

Same as Duplicity
