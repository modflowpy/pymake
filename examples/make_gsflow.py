import pymake


# Download and compile the GSFLOW distribution
def make_app():
    pymake.build_apps(["gsflow"], verbose=True)


if __name__ == "__main__":
    make_app()
