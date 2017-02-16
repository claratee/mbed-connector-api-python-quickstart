# mbed-cloud-sdk-python-quickstart
This is a quickstart application for the [mbed-cloud-sdk-python](https://github.com/ARMmbed/mbed-cloud-sdk-python) package. 
The goal of this application is to get the user up and running, using the mbed-cloud python sdk package and talking to devices through mbed cloud client in under 5 min, 5 steps or less.
The quickstart webapp is meant to be paired with the [quickstart embedded app](https://github.com/mbartling/mbed-cloud-client-example/tree/simple-client-qs-ethernet). The quickstart web app will allow the user to visualize quickstart embedded devices and interact with them. 

### Pre-requisites
- A [mbed cloud portal](https://portal.mbedcloud.com/) account and have generated an [API token](https://portal.mbedcloud.com/access/keys)
- A endpoint running the [mbed cloud client quickstart example](https://github.com/mbartling/mbed-cloud-client-example/tree/simple-client-qs-ethernet)
- Install the required packages `pip install -r requirements.txt`

### Use
1. Put your [API key](https://portal.mbedcloud.com/access/keys) into the app.py file, replace the following text

    ```python
    api_key = "" # Insert your API key
    ```

    or set an evironment variable called `ACCESS_KEY` with the value of your API key

2. Run the `app.py` file

```python
python ./app.py
```

3. Open a web page to the web.py server. Usually [//localhost:8002](//localhost:8002) will work. 

4. Interact with the web page, blink the LED's, subscribe to the resources, click the button on the board and see the numbers tick up on the web app.
    {{TODO: insert gif's here}}

5. Modify : go checkout the API for the [mbed-cloud-sdk-python](https://github.com/ARMmbed/mbed-cloud-sdk-python) and make your own applications!


## Troubleshooting
Here are some common problems and their solutions.

##### Cannot establish a secure connection
This is most likely caused by not having the `requests[security]` package installed. If you are using Ubuntu 14.4 LTS you may need to update pip first `pip install -U pip` and then install the requests security package `pip install -U requests[security]`. 

##### WebSocket transport not available
Dont worry about that warning message, it is not applicable to this demo, but likewise the warning message cannot be disabled. 

##### ERROR 500 on trying to run the app.py file
Make sure you added your [API token](https://portal.mbedcloud.com/access/keys) to the app. You can do this by either changing the value of the `token` variable in the app.py file or by setting the `ACCESS_KEY` environment variable to your access key. 

