from pymake import Pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6():
    pm = Pymake()
    pm.download_target("mf6")
    pm.build("mf6")
    pm.build("zbud6")
    pm.download_cleanup()

    return




if __name__ == "__main__":
    make_mf6()
