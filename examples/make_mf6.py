from pymake import Pymake


# Download and compile the MODFLOW 6 distribution
def make_mf6():
    # pymake.build_apps(['mf6', 'zbud6'])
    pm = Pymake()
    parser = pm.get_parser()
    parser.appdir = 'build'
    pm.build(['mf6', 'zbud6'])




if __name__ == "__main__":
    make_mf6()
