[![PyPI version](https://img.shields.io/pypi/v/edx-shopify.svg)](https://pypi.python.org/pypi/edx-shopify)


# edX Shopify

This is a Django app intended for use in Open edX, as a means of integrating it
with Shopify.

For the moment, this requires a patched version of edX.  Please refer to the
[hastexo/master/webhooks](https://github.com/hastexo/edx-platform/tree/hastexo/master/webhooks)
fork of `edx-platform`.


## Deployment

The easiest way for platform administrators to deploy the edX Shopify app and
its dependencies to an Open edX installation is to pip install it to the edxapp
virtualenv.

To deploy `edx-shopify`:

1. Install it via pip:

    ```
    $ sudo /edx/bin/pip.edxapp install edx-shopify
    ```

2. Add it to the `ADDL_INSTALLED_APPS` and `WEBHOOK_APPS` of your LMS
   environment, by editing `/edx/app/edxapp/lms.env.json`:

    ```
    "ADDL_INSTALLED_APPS": [
        "edx_shopify"
    ],
    "WEBHOOK_APPS": [
        "edx_shopify"
    ],
    ```

3. Migrate the `edxapp` database by running:

    ```
    $ sudo /edx/bin/python.edxapp /edx/app/edxapp/edx-platform/manage.py lms --settings=aws migrate
    ```

4. Finally, restart edxapp and its workers:

    ```
    sudo /edx/bin/supervisorctl restart edxapp:
    sudo /edx/bin/supervisorctl restart edxapp_worker:
    ```


## License

This app is licensed under the Affero GPL; see [`LICENSE`](LICENSE) for
details.
