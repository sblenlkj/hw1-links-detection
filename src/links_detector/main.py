import uvicorn


def main() -> None:
    uvicorn.run(
        "links_detector.api:app",
        host="0.0.0.0",
        port=8978,
    )


if __name__ == "__main__":
    main()
