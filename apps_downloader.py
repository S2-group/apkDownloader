import csv
import os
from typing import Callable
import requests
import zipfile
from subprocess import call
import sys
from bs4 import BeautifulSoup

BASE_URL = "https://apkpure.com/"
APP_LIST = "../app_annie_scraper/apps_no_dups.csv"
ERROR_LOG = "error_log.txt"
MISSING_LIST = "missing_apks.txt"
TARGET_DIR = "downloaded_apps"
INVALID_DIR = "invalid_apps"
TIMEOUT = 180


def write_error_log(_apk_name):
    with open(ERROR_LOG, 'a+') as log_file:
        log_file.write(_apk_name + "\n")
        log_file.flush()
        log_file.close()


def build_search_url(_package_name):
    return BASE_URL + "search?q=" + _package_name + "&region="


def apk_is_valid(_apk_name):
    with open(os.devnull, "w") as null:
        error_state = call(["aapt", "dump", "permissions", _apk_name], stdout=null)
        if error_state != 0:
            print("Not a valid apk, maybe it's an xapk?")
        return error_state == 0


def xapk_is_valid(_xapk_name, _package_name):
    with zipfile.ZipFile(_xapk_name) as zfile:
        if _package_name in zfile.namelist():
            return True
        else:
            return False


def unpack_xapk(_xapk_name: str, _package_name: str) -> None:
    with zipfile.ZipFile(os.path.join(TARGET_DIR, _xapk_name)) as zfile:
        zfile.extract(_package_name, TARGET_DIR)


def verify_apk(apk_path: str, apk_name: str) -> None:
    if not apk_is_valid(apk_path):
        if xapk_is_valid(apk_path, apk_name + ".apk"):
            new_name = apk_path.split(".apk")[0] + ".xapk"
            os.rename(apk_path, new_name)
            unpack_xapk(apk_name + ".xapk", apk_name + ".apk")
            os.remove(new_name)
            if not apk_is_valid(apk_path):
                write_error_log(apk_path)
                os.remove(apk_path)
                print("Invalid file {}, removed".format(apk_path))
            else:
                print("Xapk unpacked successfully!")
        else:
            write_error_log(apk_path)
            os.remove(apk_path)
            print("Invalid file {}, removed".format(apk_path))


def download_via_apkpure(package_name: str, apk_path: str) -> None:
    """ Downloads a given apk from the apkpure website"""
    # Search the apk by package id
    r = requests.get(build_search_url(package_name), timeout=TIMEOUT)
    if r.ok:
        soup = BeautifulSoup(r.text, "html.parser")
        details_url = soup.find("p", {"class": "search-title"}).a['href'][1:]
    else:
        raise Exception

    # Now search the details page for the download url
    r = requests.get(BASE_URL + details_url, timeout=TIMEOUT)
    if r.ok:
        soup = BeautifulSoup(r.text, "html.parser")
        download_page_url = soup.find("div", {"class": "ny-down"}).a['href'][1:]
    else:
        raise Exception

    # Check that we got the right link
    if package_name not in download_page_url:
        raise Exception

    # Now open the download page and download the apk
    r = requests.get(BASE_URL + download_page_url, timeout=TIMEOUT)
    if r.ok:
        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.find("a", {"id": "download_link"})
        download_request = requests.get(link['href'], timeout=TIMEOUT)
        if download_request.ok:
            with open(apk_path, 'wb+') as output_file:
                output_file.write(download_request.content)
                output_file.flush()
                output_file.close()
                print("Download completed for {}".format(package_name))
            verify_apk(apk_path, package_name)


def download_via_gplaycli(package_name: str, apk_path: str):
    """ Downloads a given apk via gplaycli """
    with open(os.devnull, "w") as null:
        error_state = call(["gplaycli", "-d", package_name, "-f", TARGET_DIR], stdout=null)
        return error_state == 0


def make_missing_list(package_name: str, apk_path: str):
    """ Not a real downloader, creates a list of missing apks """
    with open(MISSING_LIST, "a") as out_list:
        out_list.write(package_name + '\n')
        out_list.flush()
        out_list.close()


def main(download_fun: Callable[[str, str], None]):
    with open(APP_LIST) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        print('Using the {} downloader'.format(download_fun.__name__.upper()))
        for index, row in enumerate(csvreader):
            try:
                print("App numero {}".format(index + 1))
                apk_path = TARGET_DIR + "/" + row['package_name'] + ".apk"

                if os.path.isfile(apk_path):
                    print("Salto il download di {}".format(row['package_name']))
                    continue

                print("Inizio il download di {}".format(row['package_name']))
                download_fun(row['package_name'], apk_path)

            except Exception as e:
                print("Error occurred during iteration {}: {}".format(index, e))
                write_error_log(row['package_name'])


if __name__ == '__main__':
    download_method = download_via_apkpure
    if len(sys.argv) > 1 and sys.argv[1] == 'gplaycli':
        download_method = download_via_gplaycli
    elif len(sys.argv) > 1 and sys.argv[1] == 'makelist':
        download_method = make_missing_list
    main(download_method)
