# StealerLogs-py

Official python library for the [stealerlogs.com](https://stealerlogs.com) API

- [StealerLogs-py](#stealerlogs-py)
  - [Installation](#installation)
  - [Quick start](#quick-start)
  - [Getting your api key](#getting-your-api-key)
  - [Other examples](#other-examples)

## Installation

```sh-session
uv add git+https://github.com/stealerlogs-com/stealerlogs-py
```

## Quick start

Example usage

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.search("example@example.com", type="email")
        print(response.hits)

if __name__ == "__main__":
    main()
```

## Getting your api key

1. Visit https://stealerlogs.com/account
2. Sign in or create an account
3. Copy your API key

## Other examples

<details>
<summary>Regex search</summary>

```python
from stealerlogs import Client, SearchType

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.search(
            r"admin\@gmail\.com",
            type=SearchType.EMAIL,
            regex=True,
        )
        print(response.hits)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Hide results with no files</summary>

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.search(
            "example@example.com",
            type="email",
            files=True,
        )
        print(response.hits)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Log credentials</summary>

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.credentials("LOG_ID", page=1)
        print(response.count, response.has_next)
        print(response.items)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Cookies</summary>

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.cookies("LOG_ID", page=1)
        print(response.domains)
        print(response.items)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Filter cookies by domain</summary>

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        response = sl.cookies(
            "LOG_ID",
            page=1,
            domains=[".youtube.com", ".google.com"],
            hide_expired=True,
        )
        print(response.count, response.has_next)
        print(response.items)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Files and file content</summary>

```python
from stealerlogs import Client

def main() -> None:
    with Client("MY_API_KEY") as sl:
        files = sl.files("LOG_ID", page=1)
        print(files.items)

        content = sl.content("LOG_ID", "Autofill/Chrome.txt")
        print(content.path, content.size)
        print(content.content)

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary>Async client</summary>

```python
import asyncio

from stealerlogs import AsyncClient

async def main() -> None:
    async with AsyncClient("MY_API_KEY") as sl:
        response = await sl.search("example@example.com", type="email")
        print(response.hits)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>
