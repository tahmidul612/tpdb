# Plex Poster Organizer

Plex Poster Organizer is a Python utility designed to organize movie and TV show posters fetched from 'The Poster DB' and match them with respective media folders in a Plex library. This tool facilitates the seamless arrangement and association of posters with media content within a Plex server.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Setup](#setup)
  - [Plex Configuration](#plex-configuration)
- [Usage](#usage)
  - [Download Poster](#download-poster)
  - [Organize Posters](#organize-posters)
  - [Sync Posters](#sync-posters)

## Installation

To install and run the Plex Poster Organizer utility, follow these steps:

1. Clone this repository:

    ```console
    git clone https://github.com/tahmidul612/tpdb.git
    cd tpdb
    ```

1. Install dependencies:

    ```console
    pip install -r requirements.txt
    ```

## Setup

### Plex Configuration

Before using the utility, configure your Plex server details:

1. Open the `config.ini` file.
2. Enter your Plex server URL and authentication token in the respective fields:

```ini
server_baseurl = Your_Plex_Server_URL
server_token = Your_Plex_Auth_Token
```

## Usage

To use the Plex Poster Organizer, follow these steps:

Run the script:

```console
python tpdb.py
```

### Download Poster

To download a poster from a URL:

```console
python tpdb.py --download <URL>
```

### Organize Posters

To organize new posters:

```console
python tpdb.py --action new
```

### Sync Posters

To sync existing posters:

```console
python tpdb.py --action sync
```
