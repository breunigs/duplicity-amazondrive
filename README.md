## Shipped with Duplicity 0.8+

This backend has already been merged upstream and will be included in Duplicity 0.8+. If you have any bug reports, please direct them at the Duplicity mailing list at duplicity-talk@nongnu.org.


## Setup

This backend needs at least Duplicity 0.7+ and python-requests python-requests-oauthlib.


**1. Download:**

Obtain most [recent version through Launchpad](http://bazaar.launchpad.net/~duplicity-team/duplicity/0.8-series/view/head:/duplicity/backends/adbackend.py). Just click the "download file" button and you should get the raw version.

**2. Move:**
```
# Linux
cp adbackend.py /usr/lib/python2.7/dist-packages/duplicity/backends/

# MacOS X
cp adbackend.py /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/duplicity/backends
```

**3. Authenticate:**

On first usage you will need to open an URL in a browser and copy the resulting URL back into the tool to enable oauth access. The data will be stored in `~/.duplicity_ad_oauthtoken.json`.


## Usage
```
duplicity source_path ad:///backup/my_new_backup
```

# License

Same as Duplicity
