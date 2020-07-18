import pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6beta():
    pymake.build_apps("mf6beta")


if __name__ == "__main__":
    make_mf6beta()
