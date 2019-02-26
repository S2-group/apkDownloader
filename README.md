# apkDownloader
A python script to download Android app binaries.

App download is performed from APKPure.com.
If the `gplaycli` command line parameter is provided as input, it will use [gplaycli](https://github.com/matlink/gplaycli) (if installed on the system) instead to perform the download.

Includes pause/resume (if the script is stopped, it will skip any app already downloaded when restarted). 

Requires Python >= 3.6

## Usage

From the command line, navigate to the script folder and run
`python apps_downloader.py`

## Parameters
`APP_LIST` => path to list of apps to download. 

`ERROR_LOG` => path to a file where eventual errors encountered during download will be logged

`MISSING_LIST` => path to a file where apps that could not be downloaded will be listed

`TARGET_DIR` => path to a folder where downloaded apk files will be stored

`INVALID_DIR` => path to a folder where corrupted apk files will be stored

`TIMEOUT` => download timeout in seconds  

`BASE_URL` => don't touch this
