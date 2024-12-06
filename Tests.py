from unittest.mock import patch, MagicMock
import sys
import pytest
from Downloader import Downloader
from queue import Queue
from Polar_File_Handler import FileHandler
import os
from Controller import Controller, main
import polars as pl
import shutil
import requests
import threading

# fixtures......................................................................

# Fixture for creating a temporary file to simulate a download destination
@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_output.pdf"
    yield str(file_path) # Provide the path to the test
    # Temporary files are automatically cleaned up after tests by pytest


# Fixture for creating a temporary directory to simulate output directory for downloads
@pytest.fixture
def temp_output_dir(tmp_path):
    destination = tmp_path / "output"
    yield destination # Provide the path to the test
    if os.path.exists(destination): # Clean up the directory after test
        shutil.rmtree(destination)


# Fixture for creating temporary test files 
@pytest.fixture
def setup_test_files(tmp_path): 
    url_file = tmp_path / "test_urls.xlsx"  # Simulated file containing URLs
    report_file = tmp_path / "test_report.xlsx" # Simulated report file
    
    # Create mock data for the URL file
    file_data = pl.DataFrame({
        "BRnum": ["BR50058", "BR50059"],
        "Pdf_URL": ["http://dam.abbott.com/en-ie/documents/pdf/2994%20Citizenship%20Report%202016%20v15.pdf", "http://www.abc.net.au/corp/annual-report/2017/documents/ABC_AnnualREport-2017_Volume-1.pdf"],
        "Report Html Address": ["http://www.ie.abbott/about-us/global-citizenship/citizenship-reporting.html", "http://www.abc.net.au/corp/annual-report/2017/home.html"]
    })
    file_data.write_excel(url_file) # Save mock data to the URL file
    report_file.touch()  # Create an empty report file
    return str(url_file), str(report_file), str(tmp_path)



# Unit tests......................................................................
def test_download_success(temp_file):
    downloader = Downloader()
    url = "http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf"

    # Mock requests.get to simulate a successful response
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = b"PDF content"
        mock_get.return_value = mock_response

        success = downloader.download(url, temp_file)
        assert success, "Download should succeed"

        
def test_download_failure_invalid_url(temp_file):
    downloader = Downloader()
    url = "http://invalid_url.com"  

    # Mock requests.get to simulate an exception
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")
        
        success = downloader.download(url, temp_file)
        assert not success, "Download should fail for invalid URL"
    

def test_download_failure_empty_url(temp_file):
    downloader = Downloader()
    url = ""  

    # Test should fail for empty URL without needing a mock
    success = downloader.download(url, temp_file)
    assert not success, "Download should fail for empty URL"


def test_download_alt_success(temp_file):
    downloader = Downloader()
    url = "http://invalid_url.com"
    alt_url = "http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf"

    # Mock requests.get to simulate failures and success
    with patch("requests.get") as mock_get:
        def side_effect(request_url, *args, **kwargs): 
            if request_url == url: # Configure the mock to simulate failure for the main URL
                raise requests.exceptions.RequestException("Invalid URL")
            elif request_url == alt_url: # Simulate a successful response for the alternative URL
                mock_response = MagicMock()
                mock_response.headers = {"content-type": "application/pdf"}
                mock_response.content = b"PDF content"
                return mock_response

        # Set the side effect to simulate request results
        mock_get.side_effect = side_effect

        success = downloader.download(url, temp_file, alt_url)
        assert success, "Download should succeed"
        

def test_download_failure_invalid_alt_url(temp_file):
    downloader = Downloader()
    url = "http://invalid_url.com"  
    alt_url = "http://another_invalid_url.com" 
    downloader = Downloader()

    # Mock the requests.get call to simulate failure for both URLs
    with patch("requests.get") as mock_get:
        def side_effect(request_url, *args, **kwargs):
            if request_url == url:
                raise requests.exceptions.RequestException("Invalid URL")
            elif request_url == alt_url:
                raise requests.exceptions.RequestException("Invalid alt URL")


        # Set the side effect to simulate request results
        mock_get.side_effect = side_effect

        success = downloader.download(url, temp_file, alt_url)
        assert not success, "Download should fail when both URL and alt_url fail"
        
        
def test_download_failure_no_alt_url(temp_file):
    downloader = Downloader()
    url = "http://invalid_url.com"
    alt_url = None  

    # Mock the requests.get call
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")  # Simulate failure on the primary URL
        
        success = downloader.download(url, temp_file, alt_url)
        assert not success, "Download should fail when no alt_url is provided"
        
        
def test_download_failure_non_pdf_content(temp_file):
    downloader = Downloader()
    url = "http://www.abc.net.au/corp/annual-report/2017/home.html"  # A URL returning non-PDF content

    # Mock the requests.get call to not return a pdf
    with patch("requests.get") as mock_get:  
        mock_response = MagicMock() 
        mock_response.headers = {"content-type": "text/html"}  
        mock_response.content = b"Some text content"
        mock_get.return_value = mock_response

        success = downloader.download(url, temp_file)
        assert not success, "Download should fail for non-PDF content"
   
   
def test_download_failure_file_write(temp_file):
    downloader = Downloader()
    url = "http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf"

    # Mock the requests.get call to simulate a successful response
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = b"PDF content"
        mock_get.return_value = mock_response

        # Patch the open function to simulate an IO error while writing the file
        with patch("builtins.open", side_effect=IOError("Write Error")):
            success = downloader.download(url, temp_file)
            assert not success, "Download should fail due to file write error"

 
def test_controller_initialization():
    controller = Controller()
    assert controller.url_file_name == os.path.join("customer_data","GRI_2017_2020.xlsx")
    assert controller.report_file_name == os.path.join("customer_data","Metadata2017_2020.xlsx")
    assert controller.destination == "files"


def test_correct_number_of_threads_used(setup_test_files):
    url_file, report_file, destination = setup_test_files
    file_handler = FileHandler(number_of_threads=5)  # Set the number of threads to 5

    # Mock `requests.get` to simulate a fast response
    with patch("requests.get", return_value=MagicMock(headers={"content-type": "application/pdf"}, content=b"PDF content")):
        # Mock `threading.Thread` to count thread creations
        with patch("threading.Thread") as mock_thread:
            # Mock `Queue.join` to skip waiting for threads to complete
            with patch("queue.Queue.join", return_value=None):
                file_handler.start_download(url_file, report_file, destination)

                # Ensure the correct number of threads were created
                assert mock_thread.call_count == 5, f"Expected 5 threads, but got {mock_thread.call_count}"



# Integration tests......................................................................   
def test_download_thread(temp_output_dir):
    destination = temp_output_dir
    queue = Queue()
    finished_dict = {"BRnum": [], "pdf_downloaded": []}
    queue.put(["http://www.hkexnews.hk/listedco/listconews/SEHK/2017/0512/LTN20170512165.pdf", str(destination), "BR50045", None, finished_dict])

    file_handler = FileHandler()

    with patch("Downloader.Downloader.download") as mock_download:
        mock_download.return_value = True # Simulate successful download
        file_handler.download_thread(queue)

    assert finished_dict["BRnum"] == ["BR50045"], "BRnum should be updated"
    assert finished_dict["pdf_downloaded"] == ["yes"], "Download status should be 'yes'"
    assert os.path.exists(destination), "Destination directory should exist"
    

def test_controller_run(setup_test_files):
    url_file, report_file, destination = setup_test_files
    controller = Controller()
    controller.set_url_file(url_file)
    controller.set_report_file(report_file)
    controller.set_destination(destination)

    controller.run(number_of_threads=2)

    # Verify outputs
    assert os.path.exists(destination), "Destination folder should be created"
    assert os.listdir(destination), "Destination folder should contain downloaded files"


def test_command_line_args(setup_test_files):
    url_file, report_file, destination = setup_test_files
    
    # Simulate passing arguments through the command line
    test_args = ["main.py", "-uf", url_file, "-rf", report_file, "-d", destination, "-t", "4"]

    # Patch sys.argv to simulate the command-line arguments
    with patch.object(sys, "argv", test_args):
        # Patch the methods set_url_file, set_report_file, and set_destination
        with (patch("Controller.Controller.set_url_file") as mock_set_url_file, 
             patch("Controller.Controller.set_report_file") as mock_set_report_file, 
             patch("Controller.Controller.set_destination") as mock_set_destination, 
             patch("Controller.FileHandler.start_download", return_value=None), 
             patch("builtins.open", MagicMock()), 
             patch("requests.get", return_value=MagicMock(status_code=200, content=b"PDF content"))
        ):
            
            # Call the main function (which simulates running the script directly)
            main()

            # Assert that the set_url_file, set_report_file, and set_destination methods were called with the correct arguments
            mock_set_url_file.assert_called_once_with(url_file)
            mock_set_report_file.assert_called_once_with(report_file)
            mock_set_destination.assert_called_once_with(destination)