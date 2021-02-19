import pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6():
    pymake.build_apps(("mf6",), verbose=True)

    return


if __name__ == "__main__":
    make_mf6()
