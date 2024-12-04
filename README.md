# PDF Downloader

## Prerequisites

To run the project simply first create a new virtual environment

``` ps
python -m venv .venv
```

for windows make sure that LocalMachine execution policy is set to AllSigned

``` ps
Set-ExecutionPolicy -ExecutionPolicy AllSigned -Scope LocalMachine
```

then run

``` ps
./.venv/Scripts/activate
```

for windows or

``` ps
. .venv/bin/activate
```

for macos or linux
then

``` ps
pip install -r requirements.txt
```

## Usage

### Run with default values

``` ps
python Controller.py
```

### Overwrite parameters

1. ` -h ` Shows a help of the overwrite parameters
2. `-d` Overwrite default directory
3. `-rf` Overwrites the default report file destination and name
4. `-uf` Overwrites the default filename with url links. For now it must have the following coloumns : `BRNum, pdf_url, Report Html Address`
5. `-t` Overwrites number of threads

I have no speficic points I want you to look at for feedback, so just find what you deem the most necesarry

## Changes

### Create directory and add data file

> /customer_data/  
> &emsp; GRI_2017_2020.xlsx

### BRNum and download status not in the same order

> Polar_File_Handler.py  
> &emsp; ln: 28-31

### Er Queue() threadsafe?

### Changed controller function name

controller.py : ln 20

```py
set_repor_file()
```

Changed to

```py
set_report_file()
```

### Changed write error handling to correctly catch exceptions

```py
with open(destination_path, "wb") as file:
    try:
        file.write(response.content)
    except:
        return False
```

Changed to

```py
try:
    with open(destination_path, "wb") as file:
        file.write(response.content)
except:
    return False
```

### Moved if __name__ == "__main__" logic to main()