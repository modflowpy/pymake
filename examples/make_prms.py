import pymake


# Download and compile the prms distribution
def make_app():
    pymake.build_apps(["prms"], verbose=True, meson=True)


if __name__ == "__main__":
    make_app()
