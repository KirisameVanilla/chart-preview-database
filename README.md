# Chart-Preview-Database

> All data belongs to [taiko.wiki](https://taiko.wiki)

## API

- `/api/previews` -> Get the previews.json  
    Call: `/api/previews`

    Return:

    ``` json
    {
        "1": {
            "1": [
                "https://cdn.ourtaiko.org/api/preview/1/1.jpg"
                ],
            "2": [
                "https://cdn.ourtaiko.org/api/preview/1/2.jpg"
                ],
            "3": [
                "https://cdn.ourtaiko.org/api/preview/1/3.jpg"
                ],
            "4": [
                "https://cdn.ourtaiko.org/api/preview/1/4.jpg"
                ],
            "5": []
        },
        ...
    }
    ```

- `/api/preview/id` -> Get a specific song's previews json  
    Call: `/api/preview/1`

    Return:

    ``` json
    {
        "1": [
            "https://cdn.ourtaiko.org/api/preview/1/1.jpg"
            ],
        "2": [
            "https://cdn.ourtaiko.org/api/preview/1/2.jpg"
            ],
        "3": [
            "https://cdn.ourtaiko.org/api/preview/1/3.jpg"
            ],
        "4": [
            "https://cdn.ourtaiko.org/api/preview/1/4.jpg"
            ],
        "5": []
    }
    ```

- `/api/preview/id/filename` -> Get the pic file
