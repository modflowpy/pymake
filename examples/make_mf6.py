from pymake import build_apps


# Download and compile the MODFLOW 6 distribution
def make_mf6():
    build_apps(("mf6",))

    return


if __name__ == "__main__":
    make_mf6()
