from unittest.mock import patch, MagicMock
import pytest
from Downloader import Downloader
from queue import Queue
from Polar_File_Handler import FileHandler
import os
from Controller import Controller
import polars as pl
import shutil

# Unit tests......................................................................
@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_output.pdf"
    yield str(file_path)


def test_download_success(temp_file):
    downloader = Downloader()
    url = "http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf"
    # destination_path = "test_output.pdf"

    # Mock the requests.get call
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.content = b"PDF content"
        mock_get.return_value = mock_response

        success = downloader.download(url, temp_file)
        assert success, "Download should succeed"
        
        
def test_download_failure_invalid_url():
    downloader = Downloader()
    url = ""
    destination_path = "test_output.pdf"
    success = downloader.download(url, destination_path)
    assert not success, "Download should fail for an empty URL"
    
   
@pytest.fixture
def temp_output_dir(tmp_path):
    destination = tmp_path / "output"
    yield destination
    if os.path.exists(destination):
        shutil.rmtree(destination)
         
def test_download_thread(temp_output_dir):
    destination = temp_output_dir
    queue = Queue()
    finished_dict = {"BRnum": [], "pdf_downloaded": []}
    queue.put(["http://www.hkexnews.hk/listedco/listconews/SEHK/2017/0512/LTN20170512165.pdf", str(destination), "BR50045", None, finished_dict])

    file_handler = FileHandler()

    with patch("Downloader.Downloader.download") as mock_download:
        mock_download.return_value = True
        file_handler.download_thread(queue)

    assert finished_dict["BRnum"] == ["BR50045"], "BRnum should be updated"
    assert finished_dict["pdf_downloaded"] == ["yes"], "Download status should be 'yes'"
    assert os.path.exists(destination), "Destination directory should exist"
    


# Integration tests......................................................................   
@pytest.fixture
def setup_test_files(tmp_path):
    # Create test input files
    url_file = tmp_path / "test_urls.xlsx"
    report_file = tmp_path / "test_report.xlsx"
    
    # Populate test_urls.xlsx with valid data
    file_data = pl.DataFrame({
        "BRnum": ["BR50058", "BR50059"],
        "Pdf_URL": ["http://dam.abbott.com/en-ie/documents/pdf/2994%20Citizenship%20Report%202016%20v15.pdf", "http://www.abc.net.au/corp/annual-report/2017/documents/ABC_AnnualREport-2017_Volume-1.pdf"],
        "Report Html Address": ["http://www.ie.abbott/about-us/global-citizenship/citizenship-reporting.html", "http://www.abc.net.au/corp/annual-report/2017/home.html"]
    })
    file_data.write_excel(url_file)
    report_file.touch()
    return str(url_file), str(report_file), str(tmp_path)

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