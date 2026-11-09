import sys


def launch():
    if "--prologue" in sys.argv:
        from prologue import main
    else:
        from main import main

    main()


if __name__ == "__main__":
    launch()