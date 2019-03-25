import pymake


# Download and compile the CRT distribution
def make_app():
    pymake.build_apps(['gsflow'])


if __name__ == "__main__":
    make_app()
