# DNAC API Samples

### Running the scripts

These scripts demonstrate the logic needed to use DNA Center APIs. Customers can choose to use whatever orchestrator tool they are comfortable with. I used Python 3.7.4 on my Macbook to run these scripts.

To view the APIs: Cisco DNA Center -> Platform -> Developer Toolkit -> APIs

### pnp.py

This goes through the logic necessary to automate plug and play of the day-0 template of one device. It doesn't cover automation in bulk.
It starts off by doing an api call for the following:
* device - pass in the SN to request the device id of device that needs to be claimed
* site hierarchy - we use the site id from this response to assign the device to a site
* templates - returns template id of template that is used to onboard device
    * Note that when using the API, network profiles are not necessary.

After making the first three API calls, we use the id's in their responses to make a fourth API call that claims the device.
* We pass the three id's obtained earlier in the body of the POST.
* configParameters is where we pass the list of variables from the template.
* There is an option to provide image to upgrade, but I did not include that in this example

You can test this script, even without an available PnP device by doing the following:

1.  Cisco DNA Center -> Provision -> Devices -> Plug and Play
2.  Click on: (+) Add Device
3.  Serial Number: DEMO0000002
4.  Product ID: C9500-16X
5.  Device Name: demo2
6.  Click on 'Add Device'
7.  The new device will be listed in 'Plug and Play Devices', state will be 'Unclaimed'
8.  Run the pnp.py script and input the device SN, onboarding template, and site.
9.  Once the script completes, the device state should now be 'Planned', meaning that when DNAC detects this device, it will automatically onboard it
10. Click on the device, go to 'Configuration' -> 'Template' and you'll see the template pushed to the device.

### configbackup.py

This script gets the config from all devices and stores it in a directory.

