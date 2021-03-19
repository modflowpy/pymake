import pymake


def make_mflgr():
    pymake.build_apps("mflgr", verbose=True)


if __name__ == "__main__":
    make_mflgr()
