from .config import get_config


def main():
    config = get_config()
    print(config.message)


if __name__ == "__main__":
    main()
